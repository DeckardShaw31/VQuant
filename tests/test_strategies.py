"""Unit tests for VQuant strategies and backtesting engine."""

import pandas as pd

from vquant import (
    MinerviniVCPStrategy,
    TurtleBreakoutVN,
    VNBacktest,
    calculate_ma_breadth,
    load_sample_data,
)


def test_load_sample_data():
    df = load_sample_data(periods=100)
    assert len(df) == 100
    for col in ["date", "open", "high", "low", "close", "volume"]:
        assert col in df.columns
    assert (df["high"] >= df["low"]).all()


def test_minervini_vcp_strategy():
    df = load_sample_data(periods=200)
    strategy = MinerviniVCPStrategy()
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_turtle_breakout_strategy():
    df = load_sample_data(periods=150)
    strategy = TurtleBreakoutVN(entry_window=10, exit_window=5)
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_backtest_with_strategy():
    df = load_sample_data(periods=200)
    strategy = TurtleBreakoutVN(entry_window=10, exit_window=5)
    bt = VNBacktest(initial_capital=50_000_000, settlement_days=2)
    result = bt.run_strategy(df, strategy, symbol="VN30_TEST")

    assert result.initial_capital == 50_000_000
    assert "total_return_pct" in result.stats
    assert "max_drawdown_pct" in result.stats
    assert "total_tax" in result.stats
    assert len(result.equity_curve) == len(df)

    # Check that summary text generates cleanly
    summary_text = result.summary()
    assert "VQUANT BACKTEST PERFORMANCE SUMMARY" in summary_text


def test_market_breadth():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    data = {
        "HPG": [20 + i for i in range(30)],
        "VHM": [40 + i * 0.5 for i in range(30)],
        "VCB": [80 - i * 0.2 for i in range(30)],
    }
    df_prices = pd.DataFrame(data, index=dates)
    breadth = calculate_ma_breadth(df_prices, window=10)
    assert len(breadth) == 30
    assert (breadth.dropna() >= 0.0).all() and (breadth.dropna() <= 100.0).all()
