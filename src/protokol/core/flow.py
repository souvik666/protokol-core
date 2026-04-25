from abc import ABC
from typing import Any, Dict, Type
from .step import AbstractStep
from .types import RunPlan, StepContext
from abc import abstractmethod

class AbstractFlow(AbstractStep, ABC):
    """
    A collection of Steps that form a directed graph.
    Flows inherit from AbstractStep, meaning an entire Flow can be nested as a single step inside another Flow.
    """

    @property
    @abstractmethod
    def steps(self) -> Dict[str, Type[AbstractStep]]:
        """Dictionary mapping step IDs to their corresponding Step classes."""
        pass

    def __init__(self):
        # Instantiate all steps when the flow is created
        self._instances = {
            step_id: step_class()
            for step_id, step_class in self.steps.items()
        }

    def get_step(self, step_id: str) -> AbstractStep:
        """Retrieves an instantiated step by its ID."""
        if step_id not in self._instances:
            raise ValueError(f"Step '{step_id}' not found in flow.")
        return self._instances[step_id]

    def all_steps(self) -> Dict[str, AbstractStep]:
        """Returns all instantiated steps."""
        return self._instances.copy()

    @property
    def start_step_id(self) -> str:
        """Returns the ID of the first step in the flow (used when nesting flows)."""
        return list(self.steps.keys())[0]

    # --- AbstractStep Interface (for Nested Flows) ---
    def get_context(self, plan: RunPlan) -> StepContext:
        """Flows themselves do not have context; the engine descends into their steps."""
        raise NotImplementedError("Engine handles sub-flows directly.")

    def process(self, plan: RunPlan, user_result: Any) -> dict:
        """Flows manipulate global state via their child steps."""
        return {}

    def next(self, plan: RunPlan, output: dict) -> str | None:
        """When a flow finishes, it should return control to the parent flow (or terminate)."""
        return None