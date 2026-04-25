from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json


NextStep = Union[str, List[str], None]


@dataclass
class TraceEntry:
    """Structured audit log entry for every step transition."""

    step: str
    attempt: int
    result: Any
    next: NextStep = None
    parallel: bool = False

    def validate(self) -> None:
        if not isinstance(self.step, str) or not self.step:
            raise ValueError("TraceEntry.step must be a non-empty string")
        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise ValueError("TraceEntry.attempt must be a non-negative integer")
        if self.next is not None:
            if isinstance(self.next, list):
                if not all(isinstance(item, str) for item in self.next):
                    raise ValueError("TraceEntry.next list must contain only strings")
            elif not isinstance(self.next, str):
                raise ValueError("TraceEntry.next must be a string, list of strings, or None")
        if not isinstance(self.parallel, bool):
            raise ValueError("TraceEntry.parallel must be a boolean")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "step": self.step,
            "attempt": self.attempt,
            "result": self.result,
            "next": self.next,
            "parallel": self.parallel,
        }

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "TraceEntry":
        if not isinstance(raw, dict):
            raise ValueError("TraceEntry data must be a dict")
        next_value = raw.get("next")
        entry = cls(
            step=raw.get("step", ""),
            attempt=raw.get("attempt", 0),
            result=raw.get("result"),
            next=next_value,
            parallel=raw.get("parallel", False),
        )
        entry.validate()
        return entry

@dataclass
class StepContext:
    """
    Yielded by a Step to request execution from the user's domain.
    It contains the prompt, required tools, and any kwargs (e.g., temperature) the LLM needs.
    """
    prompt: str
    tools: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepState:
    """Tracks the execution attempts and errors for a single Step."""
    attempt: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None


@dataclass
class RunPlan:
    """
    The complete, serializable memory of the state machine.
    This object is passed between steps and can be persisted to a database to pause/resume workflows.
    """
    # Global state payload manipulated by the steps
    state: Dict[str, Any] = field(default_factory=dict)
    
    # Tracks retries for individual steps
    step_states: Dict[str, StepState] = field(default_factory=dict)

    # Flow control pointers
    current_step: Union[str, List[str], None] = None
    is_terminal: bool = False
    is_waiting: bool = False # Flag indicating the flow is paused waiting for human input
    failed: bool = False
    error: Optional[str] = None
    
    # Tracks nested flow context (so the engine knows where to return)
    call_stack: List[Dict[str, Any]] = field(default_factory=list)

    # Immutable audit log of every step executed
    trace: List[TraceEntry] = field(default_factory=list)

    def get_step_state(self, step_id: str) -> StepState:
        """Retrieves or initializes the retry state for a specific step."""
        if step_id not in self.step_states:
            self.step_states[step_id] = StepState()
        return self.step_states[step_id]

    def reset_step_state(self, step_id: str) -> None:
        """Resets attempt counters for a step after a successful run."""
        state = self.get_step_state(step_id)
        state.attempt = 0
        state.last_error = None

    def add_trace_entry(
        self,
        *,
        step: str,
        attempt: int,
        result: Any,
        next_step: NextStep,
        parallel: bool,
    ) -> None:
        entry = TraceEntry(step=step, attempt=attempt, result=result, next=next_step, parallel=parallel)
        self.trace.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "step_states": {k: {
                "attempt": v.attempt,
                "max_retries": v.max_retries,
                "last_error": v.last_error,
            } for k, v in self.step_states.items()},
            "current_step": self.current_step,
            "is_terminal": self.is_terminal,
            "is_waiting": self.is_waiting,
            "failed": self.failed,
            "error": self.error,
            "call_stack": self.call_stack,
            "trace": [entry.to_dict() for entry in self.trace],
        }

    def to_json(self) -> str:
        """Serializes the RunPlan for database persistence."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, data: str) -> 'RunPlan':
        """Hydrates a RunPlan from a JSON string."""
        raw = json.loads(data)
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> 'RunPlan':
        if not isinstance(raw, dict):
            raise ValueError("RunPlan data must be a dictionary")

        state = raw.get("state", {})
        if not isinstance(state, dict):
            raise ValueError("RunPlan.state must be a dictionary")

        step_states_raw = raw.get("step_states", {})
        if not isinstance(step_states_raw, dict):
            raise ValueError("RunPlan.step_states must be a dictionary")
        step_states = {k: StepState(**v) for k, v in step_states_raw.items() if isinstance(v, dict)}

        current_step = raw.get("current_step")
        if current_step is not None and not isinstance(current_step, (str, list)):
            raise ValueError("RunPlan.current_step must be a string, list of strings, or None")
        if isinstance(current_step, list):
            for item in current_step:
                if not isinstance(item, str):
                    raise ValueError("RunPlan.current_step list must contain only strings")

        call_stack = raw.get("call_stack", [])
        if not isinstance(call_stack, list):
            raise ValueError("RunPlan.call_stack must be a list")
        for frame in call_stack:
            if not isinstance(frame, dict):
                raise ValueError("RunPlan.call_stack entries must be dictionaries")

        trace_raw = raw.get("trace", [])
        if not isinstance(trace_raw, list):
            raise ValueError("RunPlan.trace must be a list")
        trace = [TraceEntry.from_raw(entry) for entry in trace_raw]

        return cls(
            state=state,
            step_states=step_states,
            current_step=current_step,
            is_terminal=bool(raw.get("is_terminal", False)),
            is_waiting=bool(raw.get("is_waiting", False)),
            failed=bool(raw.get("failed", False)),
            error=raw.get("error"),
            call_stack=call_stack,
            trace=trace,
        )
