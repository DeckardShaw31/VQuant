"""Trading Strategies package for VQuant."""

from vquant.strategies.base import BaseStrategy, Signal
from vquant.strategies.trend import MinerviniVCPStrategy, TurtleBreakoutVN
from vquant.strategies.flow import (
    ForeignFlowStrategy,
    BreadthThrustStrategy,
    AllTimeHighBreakoutStrategy,
)

__all__ = [
    "BaseStrategy",
    "Signal",
    "MinerviniVCPStrategy",
    "TurtleBreakoutVN",
    "ForeignFlowStrategy",
    "BreadthThrustStrategy",
    "AllTimeHighBreakoutStrategy",
]
