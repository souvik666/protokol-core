from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json

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
    trace: list[Dict[str, Any]] = field(default_factory=list)

    def get_step_state(self, step_id: str) -> StepState:
        """Retrieves or initializes the retry state for a specific step."""
        if step_id not in self.step_states:
            self.step_states[step_id] = StepState()
        return self.step_states[step_id]

    def to_json(self) -> str:
        """Serializes the RunPlan for database persistence."""
        from dataclasses import asdict
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'RunPlan':
        """Hydrates a RunPlan from a JSON string."""
        raw = json.loads(data)
        if "step_states" in raw:
            raw["step_states"] = {k: StepState(**v) for k, v in raw["step_states"].items()}
        return cls(**raw)
