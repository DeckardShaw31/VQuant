"""Tests for Parquet Storage Layer and DuckDB Catalog with Run Manifest Hashing."""

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from vquant.data.providers import SampleAdapter
from vquant.data.store import Catalog, RawDataStore


def test_raw_data_store_partitioning_and_reading():
    """Verify partitioned writing by year and reading back."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = RawDataStore(base_dir=tmp_dir)
        adapter = SampleAdapter(random_seed=42)
        df = adapter.fetch_daily_bars("FPT", "2023-01-01", "2023-04-30")

        written = store.write_daily_bars(df, provider="sample", exchange="HOSE")
        assert len(written) > 0
        assert all(p.exists() for p in written)

        # Read back
        df_read = store.read_daily_bars("FPT")
        assert len(df_read) == len(df)
        assert (df_read["close"].values == df["close"].values).all()


def test_duckdb_catalog_point_in_time_query():
    """Verify DuckDB queries Parquet with zero-copy and respects Point-in-Time as_of filter."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_store = RawDataStore(base_dir=tmp_path / "raw")
        adapter = SampleAdapter(random_seed=42)
        df = adapter.fetch_daily_bars("FPT", "2023-01-01", "2023-02-28")
        raw_store.write_daily_bars(df, provider="sample", exchange="HOSE")

        catalog = Catalog(data_root=tmp_path)

        # 1. Query without as_of
        res = catalog.query_daily_bars(
            symbols=["FPT"],
            start_date="2023-01-01",
            end_date="2023-01-31",
        )
        assert not res.empty

        # 2. Query with as_of set to mid-January
        as_of_time = datetime(2023, 1, 15, 12, 0, 0)
        res_pit = catalog.query_daily_bars(
            symbols=["FPT"],
            start_date="2023-01-01",
            end_date="2023-01-31",
            as_of=as_of_time,
        )
        # Dates should only include dates strictly available before as_of_time
        assert all(pd.to_datetime(d) <= pd.to_datetime("2023-01-15") for d in res_pit["date"])
        assert len(res_pit) < len(res)

        # 3. Test Run Manifest SHA-256 Hash
        hash1 = catalog.compute_snapshot_hash()
        hash2 = catalog.compute_snapshot_hash()
        assert hash1 == hash2
        assert len(hash1) == 64
