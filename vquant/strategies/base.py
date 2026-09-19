"""Base Strategy Class and Signal Definitions for VQuant."""

from abc import ABC, abstractmethod
from enum import IntEnum

import pandas as pd


class Signal(IntEnum):
    """Trading signal constants."""

    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """Abstract base class for all VQuant trading strategies.

    Subclasses must implement the `generate_signals` method which returns
    a pandas Series of signals (-1: Sell, 0: Hold, 1: Buy).
    """

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Analyze OHLCV price DataFrame and return trading signals.

        Args:
            df: DataFrame containing at least ['open', 'high', 'low', 'close', 'volume'].

        Returns:
            pd.Series with the same index as df containing integer signals (1, -1, 0).
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
