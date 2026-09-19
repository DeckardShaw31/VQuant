"""Data Provider Protocol, Capability Flags, Rate Limiter & Cache."""

import hashlib
import random
import time
from datetime import date, datetime
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable

import pandas as pd


class Capability(Enum):
    """Data capabilities supported by providers."""

    PRICES_DAILY = auto()
    CORPORATE_ACTIONS = auto()
    FUNDAMENTALS = auto()
    UNIVERSE = auto()
    FLOWS = auto()
    INTRADAY = auto()


class RateLimiter:
    """Token Bucket Rate Limiter with Exponential Backoff and Jitter."""

    def __init__(self, max_calls_per_sec: float = 5.0, max_retries: int = 3):
        self.max_calls_per_sec = max_calls_per_sec
        self.min_interval = 1.0 / max_calls_per_sec if max_calls_per_sec > 0 else 0.0
        self.last_call_time = 0.0
        self.max_retries = max_retries

    def acquire(self) -> None:
        """Wait if necessary to conform to rate limit."""
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_time = time.monotonic()

    def execute_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute callable with exponential backoff and jitter upon failure."""
        attempt = 0
        last_exception = None
        while attempt < self.max_retries:
            try:
                self.acquire()
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                last_exception = e
                if attempt >= self.max_retries:
                    break
                # Exponential backoff with full jitter
                base_delay = 0.5 * (2 ** (attempt - 1))
                jitter = random.uniform(0, base_delay)
                time.sleep(base_delay + jitter)
        raise RuntimeError(
            f"Failed {func.__name__} after {self.max_retries} retries: {last_exception}"
        ) from last_exception


class IncrementalCache:
    """Key-value in-memory or filesystem cache keyed by query parameters and schema hash."""

    def __init__(self, schema_version: str = "v1.0"):
        self.schema_version = schema_version
        self._store: dict[str, Any] = {}

    def _make_key(self, symbol: str, start: str, end: str, dataset: str) -> str:
        payload = f"{symbol.upper()}:{start}:{end}:{dataset}:{self.schema_version}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, symbol: str, start: str, end: str, dataset: str) -> pd.DataFrame | None:
        key = self._make_key(symbol, start, end, dataset)
        return self._store.get(key)

    def set(self, symbol: str, start: str, end: str, dataset: str, df: pd.DataFrame) -> None:
        key = self._make_key(symbol, start, end, dataset)
        self._store[key] = df.copy()

    def clear(self) -> None:
        self._store.clear()


@runtime_checkable
class DataProvider(Protocol):
    """Protocol defining the standard interface for market data providers (P4)."""

    name: str

    @property
    def capabilities(self) -> list[Capability]:
        """Return list of supported capabilities."""
        ...

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: str | date | datetime,
        end_date: str | date | datetime,
    ) -> pd.DataFrame:
        """Fetch raw unadjusted daily OHLCV bars.

        Returns DataFrame conforming to DAILY_BARS_SCHEMA columns:
        ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'value',
         'foreign_buy_val', 'foreign_sell_val', 'foreign_net_val', 'prop_buy_val',
         'prop_sell_val', 'available_at']
        """
        ...

    def fetch_corporate_actions(
        self,
        symbol: str,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> pd.DataFrame:
        """Fetch corporate actions (dividends, splits, bonuses, rights issues).

        Returns DataFrame conforming to CORPORATE_ACTIONS_SCHEMA columns:
        ['symbol', 'ex_date', 'record_date', 'action_type', 'cash_amount',
         'ratio', 'issue_price', 'ref_price_announced', 'source', 'available_at']
        """
        ...

    def health_check(self) -> bool:
        """Check whether provider connection and authentication are healthy."""
        ...
