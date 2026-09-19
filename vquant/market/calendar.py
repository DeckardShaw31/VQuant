"""Vietnam Trading Calendar (HOSE/HNX) supporting holidays and T+2.5 settlement."""

import bisect
from datetime import date, datetime
from pathlib import Path

import pandas as pd

CALENDAR_CSV = Path(__file__).parent / "data" / "calendar.csv"


class VNTradingCalendar:
    """Trading calendar for Vietnamese equity exchanges."""

    def __init__(self, csv_path: Path | None = None):
        path = csv_path or CALENDAR_CSV
        if path.exists():
            self._df = pd.read_csv(path)
        else:
            raise FileNotFoundError(f"Calendar CSV not found at {path}")

        self._df["date"] = pd.to_datetime(self._df["date"]).dt.date
        trading_rows = self._df[self._df["is_trading_day"] == 1]
        self._trading_days_set: set[date] = set(trading_rows["date"])
        self._trading_days_sorted: list[date] = sorted(list(self._trading_days_set))

    def is_trading_day(self, dt: str | date | datetime) -> bool:
        """Check if date is an active exchange trading day."""
        d = self._parse_date(dt)
        return d in self._trading_days_set

    def next_trading_day(self, dt: str | date | datetime, n: int = 1) -> date:
        """Get the n-th next trading day after date dt using binary search."""
        d = self._parse_date(dt)
        idx = bisect.bisect_right(self._trading_days_sorted, d)
        target_idx = idx + n - 1
        if target_idx < len(self._trading_days_sorted):
            return self._trading_days_sorted[target_idx]
        raise OverflowError(
            f"Requested trading day beyond calendar range (after {self._trading_days_sorted[-1]})"
        )

    def prev_trading_day(self, dt: str | date | datetime, n: int = 1) -> date:
        """Get the n-th previous trading day before date dt using binary search."""
        d = self._parse_date(dt)
        idx = bisect.bisect_left(self._trading_days_sorted, d)
        target_idx = idx - n
        if target_idx >= 0:
            return self._trading_days_sorted[target_idx]
        raise OverflowError(
            f"Requested trading day before calendar range (before {self._trading_days_sorted[0]})"
        )

    def trading_days_between(
        self, start_dt: str | date | datetime, end_dt: str | date | datetime
    ) -> list[date]:
        """Get all trading days between start and end (inclusive)."""
        s = self._parse_date(start_dt)
        e = self._parse_date(end_dt)
        start_idx = bisect.bisect_left(self._trading_days_sorted, s)
        end_idx = bisect.bisect_right(self._trading_days_sorted, e)
        return self._trading_days_sorted[start_idx:end_idx]

    def settlement_date(
        self, trade_date: str | date | datetime, cycle: str = "T+2 PM"
    ) -> date:
        """Calculate the exact date when bought shares become available for selling."""
        d = self._parse_date(trade_date)
        if cycle in ("T+2 PM", "T+1.5", "T+2"):
            return self.next_trading_day(d, n=2)
        elif cycle == "T+0":
            return d
        else:
            return self.next_trading_day(d, n=2)

    def _parse_date(self, dt: str | date | datetime) -> date:
        if isinstance(dt, datetime):
            return dt.date()
        if isinstance(dt, date):
            return dt
        return pd.to_datetime(dt).date()


_DEFAULT_CALENDAR: VNTradingCalendar | None = None


def get_calendar() -> VNTradingCalendar:
    global _DEFAULT_CALENDAR
    if _DEFAULT_CALENDAR is None:
        _DEFAULT_CALENDAR = VNTradingCalendar()
    return _DEFAULT_CALENDAR
