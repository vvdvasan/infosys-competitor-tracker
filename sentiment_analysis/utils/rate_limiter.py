"""Rate limiter for API calls."""

import time
from datetime import datetime, timedelta
from collections import deque
import threading

class RateLimiter:
    """Thread-safe rate limiter for API requests."""

    def __init__(self, max_requests_per_minute: int = 30, max_tokens_per_minute: int = 6000):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_minute: Maximum requests allowed per minute
            max_tokens_per_minute: Maximum tokens allowed per minute
        """
        self.max_rpm = max_requests_per_minute
        self.max_tpm = max_tokens_per_minute

        # Track requests and tokens with timestamps
        self.request_times = deque()
        self.token_counts = deque()
        self.lock = threading.Lock()

    def _clean_old_entries(self):
        """Remove entries older than 1 minute."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=1)

        # Clean request times
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

        # Clean token counts
        while self.token_counts and self.token_counts[0][0] < cutoff_time:
            self.token_counts.popleft()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self.lock:
            self._clean_old_entries()

            # Check request limit
            while len(self.request_times) >= self.max_rpm:
                # Calculate wait time
                oldest_request = self.request_times[0]
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - datetime.now()).total_seconds()

                if wait_seconds > 0:
                    print(f"Rate limit reached. Waiting {wait_seconds:.1f} seconds...")
                    time.sleep(wait_seconds + 0.1)

                self._clean_old_entries()

    def add_request(self, tokens_used: int = 0):
        """Record a new request."""
        with self.lock:
            current_time = datetime.now()
            self.request_times.append(current_time)

            if tokens_used > 0:
                self.token_counts.append((current_time, tokens_used))

    def get_current_usage(self) -> dict:
        """Get current usage statistics."""
        with self.lock:
            self._clean_old_entries()

            total_tokens = sum(count for _, count in self.token_counts)

            return {
                "requests_used": len(self.request_times),
                "requests_remaining": max(0, self.max_rpm - len(self.request_times)),
                "tokens_used": total_tokens,
                "tokens_remaining": max(0, self.max_tpm - total_tokens)
            }
