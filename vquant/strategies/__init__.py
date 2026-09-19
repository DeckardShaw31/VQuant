"""Trading Strategies package for VQuant."""

from vquant.strategies.base import BaseStrategy, Signal
from vquant.strategies.flow import (
    AllTimeHighBreakoutStrategy,
    BreadthThrustStrategy,
    ForeignFlowStrategy,
)
from vquant.strategies.trend import MinerviniVCPStrategy, TurtleBreakoutVN

__all__ = [
    "BaseStrategy",
    "Signal",
    "MinerviniVCPStrategy",
    "TurtleBreakoutVN",
    "ForeignFlowStrategy",
    "BreadthThrustStrategy",
    "AllTimeHighBreakoutStrategy",
]
