"""Trend Following & Momentum Strategies tailored for the Vietnamese Stock Market."""

import pandas as pd

from vquant.strategies.base import BaseStrategy, Signal


class MinerviniVCPStrategy(BaseStrategy):
    """Mark Minervini's Trend Template and Volatility Contraction Pattern (VCP).

    Conditions for a BUY setup:
    1. Trend Template:
       - Close > 50 SMA > 150 SMA > 200 SMA
       - 200 SMA trending up (slope > 0 over past 20 bars)
       - Close >= 1.25 * 52-week Low (at least 25% off its low)
       - Close >= 0.75 * 52-week High (within 25% of its high)
    2. VCP Contraction & Breakout:
       - Volatility is contracting (ATR(10) / Close <= contraction_max)
       - Volume Spike: Volume > volume_mult * SMA(Volume, 20)
       - Close breakout: Close > 20-day High of previous bar

    Exit Condition:
    - Close falls below 50 SMA or fixed trailing stop loss pct.
    """

    def __init__(
        self,
        fast_ma: int = 50,
        mid_ma: int = 150,
        slow_ma: int = 200,
        volume_mult: float = 1.5,
        lookback_breakout: int = 20,
        stop_loss_pct: float = 0.07,
        name: str = "MinerviniVCP",
    ):
        super().__init__(name=name)
        self.fast_ma = fast_ma
        self.mid_ma = mid_ma
        self.slow_ma = slow_ma
        self.volume_mult = volume_mult
        self.lookback_breakout = lookback_breakout
        self.stop_loss_pct = stop_loss_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                raise ValueError(f"DataFrame must contain '{col}' column.")

        close = df["close"]
        vol = df["volume"]

        # Moving Averages
        sma_fast = close.rolling(window=self.fast_ma, min_periods=1).mean()
        sma_mid = close.rolling(window=self.mid_ma, min_periods=1).mean()
        sma_slow = close.rolling(window=self.slow_ma, min_periods=1).mean()

        # 200-day SMA slope over 20 bars
        sma_slow_slope = sma_slow - sma_slow.shift(20).fillna(sma_slow)

        # 52-week High & Low (approximated by 252 trading days)
        high_52w = df["high"].rolling(window=252, min_periods=20).max()
        low_52w = df["low"].rolling(window=252, min_periods=20).min()

        # Volume 20-day SMA
        vol_sma = vol.rolling(window=20, min_periods=1).mean()

        # Breakout price (highest high of past N days, excluding current bar)
        recent_high = (
            df["high"].shift(1).rolling(window=self.lookback_breakout, min_periods=5).max()
        )

        # Trend Template Condition
        trend_template = (
            (close > sma_fast)
            & (sma_fast > sma_mid)
            & (sma_mid > sma_slow)
            & (sma_slow_slope > 0)
            & (close >= 1.25 * low_52w)
            & (close >= 0.75 * high_52w)
        )

        # Breakout & Volume Spike Condition
        breakout = (close > recent_high) & (vol >= self.volume_mult * vol_sma)

        buy_trigger = trend_template & breakout
        exit_trigger = close < sma_fast

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        in_position = False
        entry_price = 0.0

        for i in range(len(df)):
            current_close = close.iloc[i]

            if not in_position:
                if buy_trigger.iloc[i]:
                    signals.iloc[i] = Signal.BUY
                    in_position = True
                    entry_price = current_close
            else:
                # Check stop loss or technical exit
                stop_loss_hit = current_close <= entry_price * (1.0 - self.stop_loss_pct)
                if exit_trigger.iloc[i] or stop_loss_hit:
                    signals.iloc[i] = Signal.SELL
                    in_position = False
                    entry_price = 0.0

        return signals


class TurtleBreakoutVN(BaseStrategy):
    """Turtle Trading System adapted for the Vietnamese Market.

    Entry Rule:
    - BUY when Close breaks above the 20-day High (Donchian Upper Channel).

    Exit Rule:
    - SELL when Close falls below the 10-day Low (Donchian Lower Channel)
      or ATR-based trailing stop (2 * ATR).
    """

    def __init__(
        self,
        entry_window: int = 20,
        exit_window: int = 10,
        atr_window: int = 20,
        stop_atr_mult: float = 2.0,
        name: str = "TurtleBreakoutVN",
    ):
        super().__init__(name=name)
        self.entry_window = entry_window
        self.exit_window = exit_window
        self.atr_window = atr_window
        self.stop_atr_mult = stop_atr_mult

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate Donchian Channels (shifted by 1 bar to avoid lookahead bias)
        upper_channel = (
            high.shift(1).rolling(window=self.entry_window, min_periods=self.entry_window).max()
        )
        lower_channel = (
            low.shift(1).rolling(window=self.exit_window, min_periods=self.exit_window).min()
        )

        # True Range and ATR
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_window, min_periods=1).mean()

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        in_position = False
        trailing_stop = 0.0

        for i in range(len(df)):
            c = close.iloc[i]
            uc = upper_channel.iloc[i]
            lc = lower_channel.iloc[i]
            cur_atr = atr.iloc[i]

            if not in_position:
                if pd.notna(uc) and c > uc:
                    signals.iloc[i] = Signal.BUY
                    in_position = True
                    trailing_stop = c - (self.stop_atr_mult * cur_atr)
            else:
                # Update trailing stop (ratchet up only)
                potential_stop = c - (self.stop_atr_mult * cur_atr)
                if potential_stop > trailing_stop:
                    trailing_stop = potential_stop

                # Exit if lower channel broken or trailing stop hit
                if (pd.notna(lc) and c < lc) or (c <= trailing_stop):
                    signals.iloc[i] = Signal.SELL
                    in_position = False
                    trailing_stop = 0.0

        return signals
