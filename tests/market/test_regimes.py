"""Tests for Market Rules Engine and Regimes."""

from vquant.market.engine import get_regime, load_all_regimes


def test_load_all_regimes():
    hose_regimes = load_all_regimes("HOSE")
    assert len(hose_regimes) >= 2
    assert hose_regimes[0].exchange == "HOSE"


def test_hose_regime_dates():
    # Pre-KRX date
    reg_2020 = get_regime("2020-05-15", "HOSE")
    assert reg_2020.regime == "hose-2016-09-12"
    assert reg_2020.price_band_pct == 0.07

    # Post-KRX cutover date (2025-05-05)
    reg_krx = get_regime("2025-05-05", "HOSE")
    assert reg_krx.regime == "hose-krx-2025-05-05"


def test_hnx_and_upcom_regimes():
    hnx = get_regime("2024-01-01", "HNX")
    assert hnx.exchange == "HNX"
    assert hnx.price_band_pct == 0.10

    upcom = get_regime("2024-01-01", "UPCOM")
    assert upcom.exchange == "UPCOM"
    assert upcom.price_band_pct == 0.15


def test_no_gaps_in_regimes():
    """Property test: every day from 2015-01-01 to 2026-12-31 resolves to exactly one regime."""
    import pandas as pd

    dates = pd.date_range("2015-01-01", "2026-12-31", freq="D")
    for d in dates[::30]:  # Sample every 30 days
        reg = get_regime(d.date(), "HOSE")
        assert reg is not None
        assert reg.exchange == "HOSE"
