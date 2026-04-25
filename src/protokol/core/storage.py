from typing import Optional
from abc import ABC, abstractmethod
import os
from .types import RunPlan

class AbstractStorage(ABC):
    """
    Base interface for persisting the state machine memory (RunPlan).
    Implement this interface for databases like Postgres, Redis, or Mongo.
    """
    
    @abstractmethod
    def save(self, session_id: str, plan: RunPlan) -> None:
        pass

    @abstractmethod
    def load(self, session_id: str) -> Optional[RunPlan]:
        pass

class FileStorage(AbstractStorage):
    """A simple file-based persistence adapter for local development and testing."""
    
    def __init__(self, directory: str = ".sessions"):
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def _get_path(self, session_id: str) -> str:
        return os.path.join(self.directory, f"{session_id}.json")

    def save(self, session_id: str, plan: RunPlan) -> None:
        data = plan.to_json()
        with open(self._get_path(session_id), "w") as f:
            f.write(data)

    def load(self, session_id: str) -> Optional[RunPlan]:
        path = self._get_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            data = f.read()
            return RunPlan.from_json(data)
