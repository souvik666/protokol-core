from abc import ABC, abstractmethod
from typing import Any, Optional, Union, List
from .types import RunPlan, StepContext

class AbstractStep(ABC):
    """
    A single node in the state machine graph.
    Steps do NOT execute API calls. They define what is needed, process the result, and decide the next node.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for this step within a flow."""
        pass

    @abstractmethod
    def get_context(self, plan: RunPlan) -> StepContext:
        """
        Yields the requirements (prompt, tools) for this step.
        The external engine will execute the LLM based on this context.
        """
        pass

    @abstractmethod
    def process(self, plan: RunPlan, user_result: Any) -> dict:
        """
        Processes the result returned by the user's execution loop (e.g., the LLM response).
        Updates the plan.state as needed.
        Returns a dictionary representing the output of this step.
        """
        pass

    @abstractmethod
    def next(self, plan: RunPlan, output: dict) -> Union[str, List[str], None]:
        """
        Determines the next step(s) in the flow based on the current state and step output.
        Returns:
            - str: ID of the next step.
            - List[str]: IDs of multiple steps to execute in parallel.
            - None: Terminates the flow.
        """
        return None