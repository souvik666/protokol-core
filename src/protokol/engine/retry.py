from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Type


class RetryStrategy(ABC):
    """
    Defines retry behavior.
    """

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        pass


class ExceptionRetryStrategy(RetryStrategy):
    """Retry only for specific exception classes up to max_retries."""

    def __init__(self, *, max_retries: int = 2, retry_for: Iterable[Type[BaseException]] | None = None):
        self.max_retries = max_retries
        self.retry_for = tuple(retry_for or (Exception,))

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return isinstance(error, self.retry_for) and attempt < self.max_retries


class SimpleRetryStrategy(RetryStrategy):
    """
    Basic retry: retry until max_retries.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def should_retry(self, attempt: int, error: Exception) -> bool:
        return attempt < self.max_retries


class NoRetryStrategy(RetryStrategy):
    def should_retry(self, attempt: int, error: Exception) -> bool:
        return False
