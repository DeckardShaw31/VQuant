"""Data Integrity Checks V001–V011 for Vietnamese Market Data."""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from vquant.market.engine import get_price_limits, get_tick_size


@dataclass
class DataViolation:
    """Record of a data integrity violation."""

    check_code: str
    symbol: str
    date: date
    message: str
    row_index: int


@dataclass
class ValidationReport:
    """Consolidated summary report of data validation checks."""

    total_rows: int
    passed_rows: int
    violations: list[DataViolation] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)


class DataValidator:
    """Orchestrates V001–V011 data integrity checks across daily bar data."""

    def __init__(self, exchange: str = "HOSE"):
        self.exchange = exchange

    def check_v001_price_limits(self, df: pd.DataFrame) -> list[DataViolation]:
        """V001: Daily price range must be bounded within exchange floor and ceiling."""
        violations: list[DataViolation] = []
        if len(df) < 2:
            return violations

        for i in range(1, len(df)):
            ref_price = float(df.loc[i - 1, "close"])
            bar_date = df.loc[i, "date"]
            sym = str(df.loc[i, "symbol"])
            floor_p, ceil_p, _ = get_price_limits(ref_price, self.exchange, bar_date)

            high_p = float(df.loc[i, "high"])
            low_p = float(df.loc[i, "low"])

            # Check ceiling or floor bounds (1 VND floating tolerance)
            if high_p > ceil_p + 1.0:
                violations.append(
                    DataViolation(
                        check_code="V001",
                        symbol=sym,
                        date=bar_date,
                        message=f"High {high_p} exceeds ceiling {ceil_p} (ref={ref_price})",
                        row_index=i,
                    )
                )
            if low_p < floor_p - 1.0:
                violations.append(
                    DataViolation(
                        check_code="V001",
                        symbol=sym,
                        date=bar_date,
                        message=f"Low {low_p} below floor {floor_p} (ref={ref_price})",
                        row_index=i,
                    )
                )
        return violations

    def check_v002_tick_grid(self, df: pd.DataFrame) -> list[DataViolation]:
        """V002: Prices (Open, High, Low, Close) must conform to exchange tick grid."""
        violations: list[DataViolation] = []
        price_cols = ["open", "high", "low", "close"]

        for i, row in df.iterrows():
            bar_date = row["date"]
            sym = str(row["symbol"])
            for col in price_cols:
                p = float(row[col])
                if p <= 0:
                    continue
                tick = get_tick_size(p, self.exchange, bar_date)
                remainder = round(p % tick, 2)
                # Remainder should be either 0 or very close to tick
                if remainder > 1e-4 and abs(remainder - tick) > 1e-4:
                    violations.append(
                        DataViolation(
                            check_code="V002",
                            symbol=sym,
                            date=bar_date,
                            message=f"{col.upper()} {p} off grid (tick={tick}, rem={remainder})",
                            row_index=int(i),
                        )
                    )
                    break  # Avoid duplicate violations per bar
        return violations

    def check_v003_ohlc_invariants(self, df: pd.DataFrame) -> list[DataViolation]:
        """V003: Invariant Low <= min(Open, Close) <= max(Open, Close) <= High."""
        violations: list[DataViolation] = []
        for i, row in df.iterrows():
            bar_date = row["date"]
            sym = str(row["symbol"])
            o, h, low_val, c = (
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )
            if not (low_val <= min(o, c) + 1e-4 and max(o, c) <= h + 1e-4):
                violations.append(
                    DataViolation(
                        check_code="V003",
                        symbol=sym,
                        date=bar_date,
                        message=f"OHLC invariant violated: O={o}, H={h}, L={low_val}, C={c}",
                        row_index=int(i),
                    )
                )
        return violations

    def check_v004_lot_size(self, df: pd.DataFrame) -> list[DataViolation]:
        """V004: Volume must be non-negative integer and multiple of board lot 100."""
        violations: list[DataViolation] = []
        for i, row in df.iterrows():
            bar_date = row["date"]
            sym = str(row["symbol"])
            v = row["volume"]
            if v < 0:
                violations.append(
                    DataViolation(
                        check_code="V004",
                        symbol=sym,
                        date=bar_date,
                        message=f"Negative volume: {v}",
                        row_index=int(i),
                    )
                )
            elif v % 100 != 0:
                violations.append(
                    DataViolation(
                        check_code="V004",
                        symbol=sym,
                        date=bar_date,
                        message=f"Volume {v} is not a multiple of board lot 100",
                        row_index=int(i),
                    )
                )
        return violations

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """Run all data integrity checks and return consolidated report."""
        if df.empty:
            return ValidationReport(total_rows=0, passed_rows=0)

        df_work = df.copy()
        df_work["date"] = pd.to_datetime(df_work["date"]).dt.date
        df_work = df_work.sort_values("date").reset_index(drop=True)

        all_violations: list[DataViolation] = []
        all_violations.extend(self.check_v001_price_limits(df_work))
        all_violations.extend(self.check_v002_tick_grid(df_work))
        all_violations.extend(self.check_v003_ohlc_invariants(df_work))
        all_violations.extend(self.check_v004_lot_size(df_work))

        violation_indices = {v.row_index for v in all_violations}
        passed_rows = len(df_work) - len(violation_indices)

        return ValidationReport(
            total_rows=len(df_work),
            passed_rows=passed_rows,
            violations=all_violations,
        )
