"""Tests for Vietnam Regulatory Corporate Action Reconciler and Adjustments."""

from datetime import date

import pandas as pd
import pytest

from vquant.corpactions import (
    ActionType,
    CorporateActionEvent,
    CorporateActionReconciler,
    PriceAdjuster,
)


def test_cash_dividend_reconciliation_hose():
    """Verify theoretical reference price for Cash Dividend on HOSE.

    Formula: P_ref = P_close - C
    Example: Prior close = 78,400 VND, Cash dividend = 2,000 VND -> P_ref = 76,400 VND.
    """
    reconciler = CorporateActionReconciler()
    events = [
        CorporateActionEvent(
            symbol="VNM",
            ex_date=date(2023, 6, 15),
            record_date=date(2023, 6, 16),
            action_type=ActionType.CASH_DIVIDEND,
            cash_amount=2000.0,
        )
    ]
    p_ref = reconciler.calculate_theoretical_ref_price(
        p_close_prev=78400.0,
        events=events,
        exchange="HOSE",
        ex_date=date(2023, 6, 15),
    )
    assert p_ref == 76400.0

    valid, pred, diff = reconciler.reconcile_event(
        symbol="VNM",
        ex_date="2023-06-15",
        p_close_prev=78400.0,
        p_ref_actual=76400.0,
        events=events,
        exchange="HOSE",
    )
    assert valid is True
    assert diff == 0.0


def test_bonus_and_rights_issue_reconciliation():
    """Verify theoretical reference price with combined stock dividend and rights issue.

    P_close = 30,000, 10% bonus (r=0.1), Rights issue 20% at 15,000 (r=0.2, P=15000).
    Numerator = 30000 + 15000 * 0.2 = 33000
    Denominator = 1 + 0.1 + 0.2 = 1.3
    P_ref_raw = 33000 / 1.3 = 25384.615...
    Tick size in (10k-50k) is 50 VND -> Rounded to nearest tick: 25,400 VND.
    """
    reconciler = CorporateActionReconciler()
    events = [
        CorporateActionEvent(
            symbol="HPG",
            ex_date=date(2023, 7, 20),
            record_date=date(2023, 7, 21),
            action_type=ActionType.STOCK_DIVIDEND,
            ratio=0.1,
        ),
        CorporateActionEvent(
            symbol="HPG",
            ex_date=date(2023, 7, 20),
            record_date=date(2023, 7, 21),
            action_type=ActionType.RIGHTS_ISSUE,
            ratio=0.2,
            issue_price=15000.0,
        ),
    ]
    p_ref = reconciler.calculate_theoretical_ref_price(
        p_close_prev=30000.0,
        events=events,
        exchange="HOSE",
        ex_date=date(2023, 7, 20),
    )
    assert p_ref == 25400.0


def test_price_adjuster_backward():
    """Verify PriceAdjuster correctly adjusts historical bars prior to ex-date."""
    df_bars = pd.DataFrame(
        {
            "date": [date(2023, 6, 13), date(2023, 6, 14), date(2023, 6, 15), date(2023, 6, 16)],
            "close": [78000.0, 80000.0, 76000.0, 77000.0],
        }
    )
    events = [
        CorporateActionEvent(
            symbol="VNM",
            ex_date=date(2023, 6, 15),
            record_date=date(2023, 6, 16),
            action_type=ActionType.STOCK_DIVIDEND,
            ratio=0.1,  # 10% stock dividend -> Factor = 1 / 1.1 = 0.90909...
        )
    ]
    df_adj = PriceAdjuster.compute_daily_adjustment_factors(df_bars, events)
    assert "adj_close_pr" in df_adj.columns
    assert "adj_factor_pr" in df_adj.columns

    # Bars on or after ex_date have factor 1.0
    assert df_adj.loc[2, "adj_factor_pr"] == 1.0
    assert df_adj.loc[3, "adj_factor_pr"] == 1.0

    # Bars before ex_date are discounted by factor
    expected_factor = (80000.0 / 1.1) / 80000.0
    assert pytest.approx(df_adj.loc[0, "adj_factor_pr"], 1e-5) == expected_factor
    assert pytest.approx(df_adj.loc[1, "adj_factor_pr"], 1e-5) == expected_factor
