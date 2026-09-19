"""Normalized & Corporate-Action-Adjusted Data Storage Layer."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from vquant.data.schema.schemas import NORMALIZED_BARS_SCHEMA


class NormalizedDataStore:
    """Store managing cleansed and corporate-action-adjusted daily bars."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, exchange: str, symbol: str) -> Path:
        return self.base_dir / exchange.upper() / f"{symbol.upper()}.parquet"

    def write_normalized_bars(self, df: pd.DataFrame, exchange: str = "HOSE") -> Path:
        """Write normalized bars with adjustment factors to Parquet."""
        if df.empty:
            raise ValueError("Cannot write empty DataFrame to normalized store.")

        symbol = str(df["symbol"].iloc[0]).upper()
        p = self._get_path(exchange, symbol)
        p.parent.mkdir(parents=True, exist_ok=True)

        table = pa.Table.from_pandas(df, schema=NORMALIZED_BARS_SCHEMA, preserve_index=False)
        pq.write_table(table, p, compression="zstd")
        return p

    def read_normalized_bars(
        self,
        symbol: str,
        exchange: str = "HOSE",
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> pd.DataFrame:
        """Read normalized bars for a symbol, optionally filtered by date range."""
        p = self._get_path(exchange, symbol)
        if not p.exists():
            return pd.DataFrame()

        df = pd.read_parquet(p)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        if start_date is not None:
            s_d = pd.to_datetime(start_date).date()
            df = df[df["date"] >= s_d]
        if end_date is not None:
            e_d = pd.to_datetime(end_date).date()
            df = df[df["date"] <= e_d]

        return df.sort_values("date").reset_index(drop=True)
