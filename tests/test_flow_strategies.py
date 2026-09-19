"""Unit tests for Smart Money Flow factors and flow strategies."""

import pytest
import pandas as pd
from vquant import (
    VNBacktest,
    ForeignFlowStrategy,
    BreadthThrustStrategy,
    AllTimeHighBreakoutStrategy,
    load_sample_flow_data,
    calculate_cumulative_foreign_flow,
    calculate_foreign_streak,
    calculate_foreign_turnover_ratio,
)


def test_smart_money_factors():
    series = pd.Series([10.0, 15.0, -5.0, 20.0, 30.0, 25.0])
    streak = calculate_foreign_streak(series)
    assert streak.tolist() == [1, 2, 0, 1, 2, 3]

    cum = calculate_cumulative_foreign_flow(series, window=3)
    assert len(cum) == len(series)
    assert cum.iloc[1] == 25.0

    total_val = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0, 100.0])
    ratio = calculate_foreign_turnover_ratio(series, total_val)
    assert ratio.iloc[0] == 0.10


def test_foreign_flow_strategy():
    df = load_sample_flow_data(periods=200)
    assert "foreign_net_val" in df.columns
    strategy = ForeignFlowStrategy(min_streak=2, exit_streak=2)
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})

    bt = VNBacktest()
    result = bt.run_strategy(df, strategy, symbol="FOREIGN_TEST")
    assert result.initial_capital > 0
    assert "total_return_pct" in result.stats


def test_breadth_thrust_strategy():
    df = load_sample_flow_data(periods=200)
    assert "breadth" in df.columns
    strategy = BreadthThrustStrategy(oversold_level=20.0, thrust_level=55.0)
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_all_time_high_breakout():
    df = load_sample_flow_data(periods=200)
    strategy = AllTimeHighBreakoutStrategy(lookback_window=50)
    signals = strategy.generate_signals(df)
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})

    bt = VNBacktest()
    result = bt.run_strategy(df, strategy, symbol="ATH_TEST")
    assert result.initial_capital > 0
