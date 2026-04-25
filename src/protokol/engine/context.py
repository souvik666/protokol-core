from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class ExecutionContext:
    """
    Runtime context for execution.

    Future use:
    - tracing IDs
    - request metadata
    - async execution state
    - user/session info
    """

    run_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}