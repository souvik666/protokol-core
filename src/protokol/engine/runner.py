import logging
from typing import Optional, Callable, Any, Union, Dict, List
from protokol.core.types import RunPlan, StepContext
from protokol.core.flow import AbstractFlow
from protokol.core.step import AbstractStep

logger = logging.getLogger(__name__)

class Engine:
    """
    The Protokol Execution Engine.
    This class is completely synchronous and stateless. It evaluates the current RunPlan, 
    yields Contexts to the user, and advances the state machine based on user results.
    """
    def __init__(
        self,
        on_step_start: Optional[Callable[[str, RunPlan], None]] = None,
        on_step_complete: Optional[Callable[[str, RunPlan, Any], None]] = None,
        on_flow_error: Optional[Callable[[str, RunPlan, Exception], None]] = None,
    ):
        # Observability hooks for integrating Datadog, Prometheus, etc.
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_flow_error = on_flow_error

    def _resolve_flow(self, root_flow: AbstractFlow, plan: RunPlan) -> AbstractFlow:
        """Resolve the currently active flow by walking down the nested flow call stack."""
        current_flow = root_flow
        for frame in plan.call_stack:
            parent_id = frame["parent_step"]
            current_flow = current_flow.get_step(parent_id)
        return current_flow

    def get_context(self, flow: AbstractFlow, plan: RunPlan) -> Union[StepContext, Dict[str, StepContext]]:
        """Yields the StepContext(s) for the current step in the RunPlan."""
        if not plan.current_step:
            raise ValueError("RunPlan.current_step is not set.")
            
        active_flow = self._resolve_flow(flow, plan)
            
        # Handle Parallel Execution Contexts
        if isinstance(plan.current_step, list):
            contexts = {}
            for s_id in plan.current_step:
                if self.on_step_start: 
                    self.on_step_start(s_id, plan)
                contexts[s_id] = active_flow.get_step(s_id).get_context(plan)
            return contexts
            
        if self.on_step_start:
            self.on_step_start(plan.current_step, plan)
            
        step = active_flow.get_step(plan.current_step)
        
        # Handle Nested Flow: Push the parent step to the stack and descend into the sub-flow
        if isinstance(step, AbstractFlow):
            plan.call_stack.append({"parent_step": plan.current_step})
            plan.current_step = step.start_step_id
            return self.get_context(flow, plan)
            
        return step.get_context(plan)

    def advance(self, flow: AbstractFlow, plan: RunPlan, user_result: Any):
        """Processes the LLM result returned by the user and advances the state machine pointers."""
        try:
            active_flow = self._resolve_flow(flow, plan)
            
            # --- Parallel Step Advancement ---
            if isinstance(plan.current_step, list):
                if not isinstance(user_result, dict):
                    raise ValueError("For parallel execution, user_result must be a dict.")
                    
                next_steps = []
                for s_id in plan.current_step:
                    step = active_flow.get_step(s_id)
                    
                    try:
                        output = step.process(plan, user_result.get(s_id))
                    except Exception as e:
                        # Built-in Retry Logic: If processing fails, increment attempt and skip advancing.
                        step_state = plan.get_step_state(s_id)
                        step_state.attempt += 1
                        step_state.last_error = str(e)
                        if step_state.attempt <= step_state.max_retries:
                            logger.warning(f"Step {s_id} failed, retrying: {e}")
                            next_steps.append(s_id) # Keep step in the next parallel batch
                            continue
                        else:
                            raise e

                    if self.on_step_complete:
                        self.on_step_complete(s_id, plan, output)
                        
                    # Write to immutable audit log
                    plan.trace.append({
                        "step": s_id,
                        "attempt": plan.get_step_state(s_id).attempt,
                        "result": user_result.get(s_id),
                    })

                    # Calculate next step(s)
                    ns = step.next(plan, output)
                    if ns:
                        if isinstance(ns, list): next_steps.extend(ns)
                        else: next_steps.append(ns)
                        
                self._handle_next_steps(flow, plan, next_steps)

            # --- Standard Step Advancement ---
            else:
                current_step_id = plan.current_step
                step = active_flow.get_step(current_step_id)
                
                try:
                    output = step.process(plan, user_result)
                except Exception as e:
                    # Built-in Retry Logic
                    step_state = plan.get_step_state(current_step_id)
                    step_state.attempt += 1
                    step_state.last_error = str(e)
                    if step_state.attempt <= step_state.max_retries:
                        logger.warning(f"Step {current_step_id} failed, retrying: {e}")
                        return # Abort advancement, exact same context will be yielded on next loop
                    else:
                        raise e
                        
                if self.on_step_complete:
                    self.on_step_complete(current_step_id, plan, output)
                    
                ns = step.next(plan, output)
                
                # Write to immutable audit log
                plan.trace.append({
                    "step": current_step_id,
                    "attempt": plan.get_step_state(current_step_id).attempt,
                    "result": user_result,
                    "next": ns
                })

                self._handle_next_steps(flow, plan, ns)

        except Exception as e:
            if self.on_flow_error:
                curr = str(plan.current_step)
                self.on_flow_error(curr, plan, e)
            plan.failed = True
            plan.error = str(e)
            plan.is_terminal = True
            
    def _handle_next_steps(self, root_flow: AbstractFlow, plan: RunPlan, ns: Union[str, List[str], None]):
        """Helper to mutate the plan's current_step pointer and handle nested flow stack pops."""
        if not ns:
            # The current flow has ended. Check if we are inside a nested sub-flow.
            if plan.call_stack:
                # Pop the stack and return control to the parent flow
                parent_info = plan.call_stack.pop()
                parent_step_id = parent_info["parent_step"]
                
                # Re-resolve the active flow to the parent's level
                parent_flow = self._resolve_flow(root_flow, plan)
                parent_step = parent_flow.get_step(parent_step_id)
                
                # Evaluate the parent step's next() method to continue routing
                ns_after_pop = parent_step.next(plan, {})
                self._handle_next_steps(root_flow, plan, ns_after_pop)
            else:
                # Stack is empty, the root flow is complete
                plan.is_terminal = True
        elif isinstance(ns, list):
            # Parallel execution
            plan.current_step = list(set(ns))
        else:
            plan.current_step = ns
