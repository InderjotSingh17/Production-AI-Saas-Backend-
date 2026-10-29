import threading 
import time 
from collections.abc import Callable 
from typing import TypeVar

T=TypeVar("T")
class CircuitOpenError(Exception):
    """Raised when the circuit breaker blocks a request."""

class CircuitBreaker:
    def __init__(

        self,
        failure_threshold: int=5,
        recovery_timeout: float=30.0,
    ):
        self.failure_threshold=failure_threshold
        self.recovery_timeout=recovery_timeout
        self.state="CLOSED"
        self.failure_count=0
        self.opened_at=0.0
        self.lock=threading.Lock()
    def call(
        self,
        operation: Callable[[],T],
        is_failure: Callable[[Exception],bool],
    ) -> T:
        with self.lock:
            if self.state == "OPEN":
                elapsed = time.monotonic() - self.opened_at

                if elapsed < self.recovery_timeout:
                    raise CircuitOpenError(
                        "AI provider circuit is open. Try again shortly."
                    )

                self.state = "HALF_OPEN"

            elif self.state == "HALF_OPEN":
                raise CircuitOpenError(
                    "AI provider recovery is being tested. Try again shortly."
                )

        try:
            result = operation()

        except Exception as exc:
            if is_failure(exc):
                with self.lock:
                    self.failure_count += 1

                    if (
                        self.state == "HALF_OPEN"
                        or self.failure_count >= self.failure_threshold
                    ):
                        self.state = "OPEN"
                        self.opened_at = time.monotonic()

            else:
                with self.lock:
                    if self.state == "HALF_OPEN":
                        self.state = "CLOSED"

                    self.failure_count = 0

            raise

        with self.lock:
            self.state = "CLOSED"
            self.failure_count = 0

        return result


gemini_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
)