"""DuckDB SQL Catalog Layer with PIT Querying & Manifest Hashing (ADR-002)."""

import hashlib
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd


class Catalog:
    """SQL query engine querying Parquet partitions directly via DuckDB zero-copy."""

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.con = duckdb.connect(database=":memory:")

    def query(self, sql: str, params: list[object] | None = None) -> pd.DataFrame:
        """Execute arbitrary SQL query against files via DuckDB."""
        if params:
            return self.con.execute(sql, params).df()
        return self.con.execute(sql).df()

    def query_daily_bars(
        self,
        symbols: str | list[str],
        start_date: str | date | datetime,
        end_date: str | date | datetime,
        exchange: str | None = None,
        as_of: str | date | datetime | None = None,
        use_normalized: bool = False,
    ) -> pd.DataFrame:
        """Query daily bars with optional Point-in-Time as_of timestamp filter (P2)."""
        if isinstance(symbols, str):
            symbols = [symbols]
        syms = [s.upper() for s in symbols]

        subfolder = "normalized" if use_normalized else "raw"
        folder_path = self.data_root / subfolder
        if not folder_path.exists():
            return pd.DataFrame()

        # Build glob pattern for parquet files
        pattern = str(folder_path / "**" / "*.parquet").replace("\\", "/")
        symbols_str = ", ".join(f"'{s}'" for s in syms)
        s_date = str(pd.to_datetime(start_date).date())
        e_date = str(pd.to_datetime(end_date).date())

        query_str = f"""
            SELECT *
            FROM read_parquet('{pattern}')
            WHERE symbol IN ({symbols_str})
              AND date >= '{s_date}'
              AND date <= '{e_date}'
        """
        if as_of is not None:
            as_of_str = pd.to_datetime(as_of).strftime("%Y-%m-%d %H:%M:%S")
            query_str += f" AND available_at <= '{as_of_str}'"

        query_str += " ORDER BY symbol, date"
        try:
            df = self.con.execute(query_str).df()
            if not df.empty and "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            return df
        except Exception:
            return pd.DataFrame()

    def compute_snapshot_hash(self, subpath: str | None = None) -> str:
        """Compute SHA-256 Run Manifest hash across Parquet files for 100% reproducibility."""
        target_dir = self.data_root if subpath is None else self.data_root / subpath
        if not target_dir.exists():
            return hashlib.sha256(b"empty").hexdigest()

        parquet_files = sorted(target_dir.glob("**/*.parquet"))
        if not parquet_files:
            return hashlib.sha256(b"no_files").hexdigest()

        hasher = hashlib.sha256()
        for p in parquet_files:
            # Hash relative path
            hasher.update(str(p.relative_to(self.data_root)).encode("utf-8"))
            # Hash content in chunks
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)

        return hasher.hexdigest()
