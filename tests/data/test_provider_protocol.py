"""Tests for DataProvider Protocol, RateLimiter, IncrementalCache, and Adapters."""

import tempfile
from pathlib import Path

import pandas as pd

from vquant.data.providers import (
    Capability,
    DataProvider,
    FileAdapter,
    IncrementalCache,
    RateLimiter,
    SampleAdapter,
)


def test_provider_protocol_conformance():
    """Verify SampleAdapter satisfies DataProvider runtime protocol."""
    adapter = SampleAdapter()
    assert isinstance(adapter, DataProvider)
    assert Capability.PRICES_DAILY in adapter.capabilities
    assert adapter.health_check() is True

    df = adapter.fetch_daily_bars(
        symbol="VNM",
        start_date="2023-01-01",
        end_date="2023-03-31",
    )
    assert not df.empty
    assert "open" in df.columns
    assert "close" in df.columns
    assert "available_at" in df.columns
    assert df["symbol"].iloc[0] == "VNM"


def test_rate_limiter_and_retry():
    """Verify RateLimiter backoff mechanism and execution."""
    limiter = RateLimiter(max_calls_per_sec=20.0, max_retries=2)
    counter = 0

    def flaky_func():
        nonlocal counter
        counter += 1
        if counter < 2:
            raise ConnectionError("Network jitter")
        return "success"

    result = limiter.execute_with_retry(flaky_func)
    assert result == "success"
    assert counter == 2


def test_incremental_cache():
    """Verify cache store and retrieval keyed by query and schema version."""
    cache = IncrementalCache(schema_version="v1.0")
    df = pd.DataFrame({"close": [10.0, 11.0]})

    cache.set("HPG", "2023-01-01", "2023-01-02", "daily_bars", df)
    cached = cache.get("HPG", "2023-01-01", "2023-01-02", "daily_bars")
    assert cached is not None
    assert len(cached) == 2

    # Miss on different date
    assert cache.get("HPG", "2023-01-01", "2023-01-05", "daily_bars") is None


def test_file_adapter():
    """Verify FileAdapter reading CSV correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        df_csv = pd.DataFrame(
            {
                "date": ["2023-01-03", "2023-01-04"],
                "open": [50000.0, 51000.0],
                "high": [52000.0, 52000.0],
                "low": [49500.0, 50500.0],
                "close": [51000.0, 51500.0],
                "volume": [100000, 150000],
            }
        )
        df_csv.to_csv(tmp_path / "VCB.csv", index=False)

        adapter = FileAdapter(data_dir=tmp_path)
        assert isinstance(adapter, DataProvider)
        assert adapter.health_check() is True

        res = adapter.fetch_daily_bars("VCB", "2023-01-01", "2023-01-05")
        assert len(res) == 2
        assert res["symbol"].iloc[0] == "VCB"
        assert "available_at" in res.columns
