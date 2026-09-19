"""Tests for Vietnam Trading Calendar."""

from datetime import date

from vquant.market.calendar import get_calendar


def test_calendar_trading_day():
    cal = get_calendar()
    # Weekend test
    assert not cal.is_trading_day("2024-01-06")  # Saturday
    assert not cal.is_trading_day("2024-01-07")  # Sunday

    # Normal trading day
    assert cal.is_trading_day("2024-01-08")  # Monday

    # New year holiday
    assert not cal.is_trading_day("2024-01-01")


def test_settlement_date():
    cal = get_calendar()
    # Buy on Monday 2024-01-08 -> T+2 PM is Wednesday 2024-01-10
    settle = cal.settlement_date("2024-01-08", cycle="T+2 PM")
    assert settle == date(2024, 1, 10)

    # Buy on Thursday 2024-01-11 -> T+2 PM is Monday 2024-01-15 (skipping weekend)
    settle_thu = cal.settlement_date("2024-01-11", cycle="T+2 PM")
    assert settle_thu == date(2024, 1, 15)
