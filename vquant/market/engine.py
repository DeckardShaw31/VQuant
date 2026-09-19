"""Market Rules Engine: Loads versioned YAML regimes and resolves trading rules."""

import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

REGIMES_DIR = Path(__file__).parent / "regimes"


@dataclass
class TickRule:
    price_gte: float
    tick: float


@dataclass
class MarketRegime:
    regime: str
    exchange: str
    effective_from: str
    effective_to: str | None
    sources: list[str]
    sessions: dict[str, Any]
    tick_table: list[TickRule]
    lot_size: int
    odd_lot_board: bool
    price_band_pct: float
    first_day_band_pct: float
    settlement: dict[str, str]
    features: dict[str, bool]

    def get_tick(self, price: float) -> float:
        """Resolve tick size for a given price according to regime rules."""
        # Find the highest price_gte threshold that is <= price
        matching_tick = self.tick_table[0].tick
        for rule in sorted(self.tick_table, key=lambda r: r.price_gte):
            if price >= rule.price_gte:
                matching_tick = rule.tick
            else:
                break
        return matching_tick

    def round_to_tick(self, price: float, mode: str = "nearest") -> float:
        """Round price to valid tick grid."""
        tick = self.get_tick(price)
        if mode == "nearest":
            return round(round(price / tick) * tick, 2)
        elif mode == "down":
            return round(math.floor(price / tick) * tick, 2)
        elif mode == "up":
            return round(math.ceil(price / tick) * tick, 2)
        else:
            raise ValueError(f"Unknown rounding mode: {mode}")

    def price_limits(self, ref_price: float, is_first_day: bool = False) -> tuple[float, float]:
        """Compute Ceiling and Floor price given reference price.

        Rules:
        Ceiling = Reference * (1 + band_pct), rounded DOWN to nearest tick.
        Floor = Reference * (1 - band_pct), rounded UP to nearest tick.
        """
        band = self.first_day_band_pct if is_first_day else self.price_band_pct
        raw_ceil = ref_price * (1.0 + band)
        raw_floor = ref_price * (1.0 - band)

        ceiling = self.round_to_tick(raw_ceil, mode="down")
        floor = self.round_to_tick(raw_floor, mode="up")

        # Floor must be at least one tick
        tick = self.get_tick(ref_price)
        floor = max(floor, tick)
        return ceiling, floor


_REGIME_CACHE: dict[str, list[MarketRegime]] = {}


def load_all_regimes(exchange: str) -> list[MarketRegime]:
    """Load all regimes for an exchange sorted by effective_from date."""
    ex = exchange.lower()
    if ex in _REGIME_CACHE:
        return _REGIME_CACHE[ex]

    ex_dir = REGIMES_DIR / ex
    if not ex_dir.exists():
        raise ValueError(f"No regime directory found for exchange '{exchange}' at {ex_dir}")

    regimes: list[MarketRegime] = []
    for p in ex_dir.glob("*.yaml"):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        tick_rules = [
            TickRule(price_gte=float(r["price_gte"]), tick=float(r["tick"]))
            for r in data["tick_table"]
        ]
        reg = MarketRegime(
            regime=data["regime"],
            exchange=data["exchange"],
            effective_from=data["effective_from"],
            effective_to=data.get("effective_to"),
            sources=data.get("sources", []),
            sessions=data.get("sessions", {}),
            tick_table=tick_rules,
            lot_size=int(data["lot_size"]),
            odd_lot_board=bool(data.get("odd_lot_board", True)),
            price_band_pct=float(data["price_band_pct"]),
            first_day_band_pct=float(data["first_day_band_pct"]),
            settlement=data.get("settlement", {}),
            features=data.get("features", {}),
        )
        regimes.append(reg)

    regimes.sort(key=lambda r: r.effective_from)
    _REGIME_CACHE[ex] = regimes
    return regimes


def get_regime(dt: str | date | datetime, exchange: str = "HOSE") -> MarketRegime:
    """Resolve the active MarketRegime for a specific date and exchange."""
    if isinstance(dt, (date, datetime)):
        dt_str = dt.strftime("%Y-%m-%d")
    else:
        dt_str = str(dt)[:10]

    regimes = load_all_regimes(exchange)
    for reg in reversed(regimes):
        if dt_str >= reg.effective_from:
            if reg.effective_to is None or dt_str <= reg.effective_to:
                return reg

    # Fallback to earliest if before all
    return regimes[0]


def get_tick_size(
    price: float,
    exchange: str = "HOSE",
    dt: str | date | datetime = "2024-01-01",
) -> float:
    """Get tick size for given price, exchange, and date."""
    return get_regime(dt, exchange).get_tick(price)


def round_to_tick(
    price: float,
    exchange: str = "HOSE",
    dt: str | date | datetime = "2024-01-01",
    direction: str = "nearest",
) -> float:
    """Round price to valid exchange tick."""
    return get_regime(dt, exchange).round_to_tick(price, mode=direction)


def get_price_limits(
    ref_price: float,
    exchange: str = "HOSE",
    dt: str | date | datetime = "2024-01-01",
    is_first_day: bool = False,
) -> tuple[float, float, float]:
    """Return (floor_price, ceiling_price, ref_price)."""
    reg = get_regime(dt, exchange)
    ceil, floor = reg.price_limits(ref_price, is_first_day=is_first_day)
    return floor, ceil, ref_price
