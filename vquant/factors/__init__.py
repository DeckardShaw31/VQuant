"""Factors module for VQuant."""

from vquant.factors.market_breadth import calculate_ma_breadth
from vquant.factors.smart_money import (
    calculate_cumulative_foreign_flow,
    calculate_foreign_streak,
    calculate_foreign_turnover_ratio,
)

__all__ = [
    "calculate_ma_breadth",
    "calculate_cumulative_foreign_flow",
    "calculate_foreign_streak",
    "calculate_foreign_turnover_ratio",
]
