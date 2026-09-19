"""VQuant: Vietnam Quantitative Trading & Backtesting Framework."""

from vquant.__version__ import __version__
from vquant.backtest.engine import VNBacktest, BacktestResult, Trade
from vquant.factors.market_breadth import calculate_ma_breadth

__all__ = [
    "__version__",
    "VNBacktest",
    "BacktestResult",
    "Trade",
    "calculate_ma_breadth",
]
