"""VQuant: Vietnam Quantitative Trading & Backtesting Framework."""

from vquant.__version__ import __version__
from vquant.backtest.engine import VNBacktest, BacktestResult, Trade
from vquant.factors.market_breadth import calculate_ma_breadth
from vquant.factors.smart_money import (
    calculate_cumulative_foreign_flow,
    calculate_foreign_streak,
    calculate_foreign_turnover_ratio,
)
from vquant.strategies.base import BaseStrategy, Signal
from vquant.strategies.trend import MinerviniVCPStrategy, TurtleBreakoutVN
from vquant.strategies.flow import (
    ForeignFlowStrategy,
    BreadthThrustStrategy,
    AllTimeHighBreakoutStrategy,
)
from vquant.datasets.sample import load_sample_data, load_sample_flow_data

__all__ = [
    "__version__",
    "VNBacktest",
    "BacktestResult",
    "Trade",
    "calculate_ma_breadth",
    "calculate_cumulative_foreign_flow",
    "calculate_foreign_streak",
    "calculate_foreign_turnover_ratio",
    "BaseStrategy",
    "Signal",
    "MinerviniVCPStrategy",
    "TurtleBreakoutVN",
    "ForeignFlowStrategy",
    "BreadthThrustStrategy",
    "AllTimeHighBreakoutStrategy",
    "load_sample_data",
    "load_sample_flow_data",
]
