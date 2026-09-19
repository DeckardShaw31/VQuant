"""VQuant: Vietnam Quantitative Trading & Backtesting Framework."""

from vquant.__version__ import __version__
from vquant.backtest.engine import VNBacktest, BacktestResult, Trade
from vquant.factors.market_breadth import calculate_ma_breadth
from vquant.strategies.base import BaseStrategy, Signal
from vquant.strategies.trend import MinerviniVCPStrategy, TurtleBreakoutVN
from vquant.datasets.sample import load_sample_data

__all__ = [
    "__version__",
    "VNBacktest",
    "BacktestResult",
    "Trade",
    "calculate_ma_breadth",
    "BaseStrategy",
    "Signal",
    "MinerviniVCPStrategy",
    "TurtleBreakoutVN",
    "load_sample_data",
]
