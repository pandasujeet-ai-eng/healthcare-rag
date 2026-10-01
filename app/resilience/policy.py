from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 4.0


DEFAULT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    initial_delay_seconds=0.5,
    backoff_multiplier=2.0,
    max_delay_seconds=4.0,
)