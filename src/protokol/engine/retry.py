from __future__ import annotations

from abc import ABC, abstractmethod


class RetryStrategy(ABC):
    """
    Defines retry behavior.
    """

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        pass


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
