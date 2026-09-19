"""Property tests for market invariants."""

from vquant.market.engine import get_regime


def test_tick_rules_hose():
    reg = get_regime("2024-01-01", "HOSE")
    # Price < 10,000 -> tick 10
    assert reg.get_tick(8500) == 10.0
    # Price 10,000 - 49,950 -> tick 50
    assert reg.get_tick(10000) == 50.0
    assert reg.get_tick(28500) == 50.0
    # Price >= 50,000 -> tick 100
    assert reg.get_tick(50000) == 100.0
    assert reg.get_tick(95000) == 100.0


def test_price_limits_hose():
    reg = get_regime("2024-01-01", "HOSE")
    ref = 28500.0  # e.g. HPG
    ceil, floor = reg.price_limits(ref)
    assert ceil > ref
    assert floor < ref
    # Band is 7%
    assert ceil <= round(ref * 1.07, 2)
    assert floor >= round(ref * 0.93, 2)
    # Both must align to tick
    assert ceil % reg.get_tick(ceil) == 0.0
    assert floor % reg.get_tick(floor) == 0.0
