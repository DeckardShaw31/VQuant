"""Tests for Data Integrity Checks V001–V004."""

from datetime import date

import pandas as pd

from vquant.data.validate import DataValidator


def test_validator_clean_data():
    """Verify clean dataset passes all checks with zero violations."""
    validator = DataValidator(exchange="HOSE")
    df = pd.DataFrame(
        {
            "symbol": ["VCB", "VCB", "VCB"],
            "date": [date(2023, 1, 3), date(2023, 1, 4), date(2023, 1, 5)],
            "open": [80000.0, 81000.0, 81500.0],
            "high": [82000.0, 82000.0, 83000.0],
            "low": [79500.0, 80500.0, 81000.0],
            "close": [81000.0, 81500.0, 82000.0],
            "volume": [200000, 150000, 300000],
        }
    )
    report = validator.validate(df)
    assert report.is_clean is True
    assert report.violation_count == 0
    assert report.passed_rows == 3


def test_validator_catches_violations():
    """Verify validator catches V001 (limits), V002 (tick), V003 (OHLC), V004 (lot)."""
    validator = DataValidator(exchange="HOSE")
    df = pd.DataFrame(
        {
            "symbol": ["VCB", "VCB"],
            "date": [date(2023, 1, 3), date(2023, 1, 4)],
            # Bar 1 has:
            # - V001: Close 95,000 is +18.75% over 80,000 (> 7% HOSE ceiling 85,600)
            # - V002: Open 80,033 not on 50 VND tick grid
            # - V003: Low 96,000 > Close 95,000
            # - V004: Volume 10005 is not multiple of 100
            "open": [80000.0, 80033.0],
            "high": [80000.0, 97000.0],
            "low": [80000.0, 96000.0],
            "close": [80000.0, 95000.0],
            "volume": [100000, 10005],
        }
    )
    report = validator.validate(df)
    assert report.is_clean is False
    codes = {v.check_code for v in report.violations}
    assert "V001" in codes
    assert "V002" in codes
    assert "V003" in codes
    assert "V004" in codes
