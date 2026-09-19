"""Immutable Raw Data Storage using Partitioned Parquet (ADR-002)."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from vquant.data.schema.schemas import DAILY_BARS_SCHEMA


class RawDataStore:
    """Store managing immutable raw market data partitioned by provider, year, and exchange."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_partition_path(
        self,
        provider: str,
        dataset: str,
        year: int,
        exchange: str,
        symbol: str,
    ) -> Path:
        return (
            self.base_dir
            / provider.lower()
            / dataset.lower()
            / str(year)
            / exchange.upper()
            / f"{symbol.upper()}.parquet"
        )

    def write_daily_bars(
        self,
        df: pd.DataFrame,
        provider: str,
        exchange: str = "HOSE",
        dataset: str = "daily_bars",
    ) -> list[Path]:
        """Write raw daily bars into partitioned immutable Parquet files."""
        if df.empty:
            return []

        df_work = df.copy()
        df_work["date"] = pd.to_datetime(df_work["date"]).dt.date
        df_work["year"] = pd.to_datetime(df_work["date"]).dt.year

        written_paths: list[Path] = []
        for (symbol, year), group in df_work.groupby(["symbol", "year"]):
            p = self._get_partition_path(
                provider=provider,
                dataset=dataset,
                year=int(year),
                exchange=exchange,
                symbol=str(symbol),
            )
            p.parent.mkdir(parents=True, exist_ok=True)

            # Drop temporary partition column
            clean_group = group.drop(columns=["year"]).sort_values("date").reset_index(drop=True)

            # Ensure all schema columns present
            table = pa.Table.from_pandas(
                clean_group, schema=DAILY_BARS_SCHEMA, preserve_index=False
            )
            pq.write_table(table, p, compression="zstd")
            written_paths.append(p)

        return written_paths

    def read_daily_bars(
        self,
        symbol: str,
        provider: str | None = None,
        exchange: str | None = None,
        year: int | None = None,
    ) -> pd.DataFrame:
        """Read daily bars matching symbol across partitions."""
        sym = symbol.upper()
        pattern = f"**/{sym}.parquet" if year is None else f"**/{year}/**/{sym}.parquet"
        matched_files = list(self.base_dir.glob(pattern))
        if not matched_files:
            return pd.DataFrame()

        dfs = [pd.read_parquet(f) for f in matched_files]
        combined = pd.concat(dfs, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"]).dt.date
        return combined.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
