"""Smart Money Flow & Market Breadth Strategies tailored for the Vietnamese Stock Market."""

import numpy as np
import pandas as pd
from vquant.strategies.base import BaseStrategy, Signal
from vquant.factors.smart_money import calculate_foreign_streak, calculate_cumulative_foreign_flow


class ForeignFlowStrategy(BaseStrategy):
    """Strategy that rides institutional foreign investor net buying momentum.

    Entry Rule:
    - Foreign streak >= min_streak (foreign investors net buyers for consecutive days)
    - Cumulative foreign net flow over N days > 0
    - Close > SMA(Close, trend_ma) to ensure technical alignment

    Exit Rule:
    - Foreign investors net sell for exit_streak consecutive days
    - OR Close drops below SMA(Close, trend_ma)
    - OR Fixed stop loss is triggered
    """

    def __init__(
        self,
        min_streak: int = 3,
        exit_streak: int = 2,
        cum_window: int = 5,
        trend_ma: int = 20,
        stop_loss_pct: float = 0.07,
        name: str = "ForeignFlowMomentum",
    ):
        super().__init__(name=name)
        self.min_streak = min_streak
        self.exit_streak = exit_streak
        self.cum_window = cum_window
        self.trend_ma = trend_ma
        self.stop_loss_pct = stop_loss_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()
        if "foreign_net_val" not in df.columns:
            if "foreign_buy_val" in df.columns and "foreign_sell_val" in df.columns:
                df["foreign_net_val"] = df["foreign_buy_val"] - df["foreign_sell_val"]
            else:
                raise ValueError("DataFrame must contain 'foreign_net_val' (or 'foreign_buy_val' and 'foreign_sell_val').")

        close = df["close"]
        foreign_net = df["foreign_net_val"]

        # Calculate factors
        streak = calculate_foreign_streak(foreign_net)
        cum_flow = calculate_cumulative_foreign_flow(foreign_net, window=self.cum_window)
        ma_trend = close.rolling(window=self.trend_ma, min_periods=1).mean()

        # Streak of consecutive net selling days
        is_selling = (foreign_net < 0).astype(int)
        sell_streaks = np.zeros(len(df), dtype=int)
        cur_sell_streak = 0
        for i in range(len(df)):
            if is_selling.iloc[i] == 1:
                cur_sell_streak += 1
            else:
                cur_sell_streak = 0
            sell_streaks[i] = cur_sell_streak
        sell_streak_series = pd.Series(sell_streaks, index=df.index)

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        in_position = False
        entry_price = 0.0

        for i in range(len(df)):
            c = close.iloc[i]
            strk = streak.iloc[i]
            c_flow = cum_flow.iloc[i]
            trend = ma_trend.iloc[i]
            s_strk = sell_streak_series.iloc[i]

            if not in_position:
                # Buy trigger
                if strk >= self.min_streak and c_flow > 0 and c > trend:
                    signals.iloc[i] = Signal.BUY
                    in_position = True
                    entry_price = c
            else:
                # Stop loss check
                stop_hit = c <= entry_price * (1.0 - self.stop_loss_pct)
                # Sell trigger
                if s_strk >= self.exit_streak or c < trend or stop_hit:
                    signals.iloc[i] = Signal.SELL
                    in_position = False
                    entry_price = 0.0

        return signals


class BreadthThrustStrategy(BaseStrategy):
    """Market Breadth Thrust Strategy.

    Entry Rule:
    - Market breadth (% of stocks > MA20) surges from <= oversold_level (e.g. 15%)
      to >= thrust_level (e.g. 60%) within max_thrust_bars (e.g. 10 trading sessions).
    - Indicates an explosive bottom and high probability market uptrend.

    Exit Rule:
    - Market breadth falls below exit_level (e.g. 40%) or Close drops below 20 SMA.
    """

    def __init__(
        self,
        oversold_level: float = 15.0,
        thrust_level: float = 60.0,
        max_thrust_bars: int = 10,
        exit_level: float = 40.0,
        stop_loss_pct: float = 0.07,
        name: str = "BreadthThrustVN",
    ):
        super().__init__(name=name)
        self.oversold_level = oversold_level
        self.thrust_level = thrust_level
        self.max_thrust_bars = max_thrust_bars
        self.exit_level = exit_level
        self.stop_loss_pct = stop_loss_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()
        if "breadth" not in df.columns:
            raise ValueError("DataFrame must contain 'breadth' column (percentage 0.0 - 100.0).")

        breadth = df["breadth"]
        close = df["close"]
        ma20 = close.rolling(window=20, min_periods=1).mean()

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        in_position = False
        entry_price = 0.0
        last_oversold_idx = -999

        for i in range(len(df)):
            b = breadth.iloc[i]
            c = close.iloc[i]

            if b <= self.oversold_level:
                last_oversold_idx = i

            if not in_position:
                # Thrust occurred if recent oversold was within max_thrust_bars
                if b >= self.thrust_level and (i - last_oversold_idx) <= self.max_thrust_bars:
                    signals.iloc[i] = Signal.BUY
                    in_position = True
                    entry_price = c
            else:
                stop_hit = c <= entry_price * (1.0 - self.stop_loss_pct)
                if b < self.exit_level or c < ma20.iloc[i] or stop_hit:
                    signals.iloc[i] = Signal.SELL
                    in_position = False
                    entry_price = 0.0

        return signals


class AllTimeHighBreakoutStrategy(BaseStrategy):
    """Strategy that buys stocks breaking out to 52-week or All-Time Highs with volume surge.

    Stocks trading at all-time highs have zero overhead supply (bagholders wishing to break even),
    often creating strong trend momentum in the Vietnamese market.

    Entry Rule:
    - Close > previous 252-day High
    - Volume >= volume_mult * 20-day Volume SMA
    - Close > 50 SMA

    Exit Rule:
    - Trailing stop hit (trailing_stop_pct) or Close < 50 SMA.
    """

    def __init__(
        self,
        lookback_window: int = 252,
        volume_mult: float = 1.5,
        trend_ma: int = 50,
        trailing_stop_pct: float = 0.08,
        name: str = "AllTimeHighBreakout",
    ):
        super().__init__(name=name)
        self.lookback_window = lookback_window
        self.volume_mult = volume_mult
        self.trend_ma = trend_ma
        self.trailing_stop_pct = trailing_stop_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()
        high = df["high"]
        close = df["close"]
        vol = df["volume"]

        # 52-week high of previous bars
        prior_high = high.shift(1).rolling(window=self.lookback_window, min_periods=20).max()
        vol_sma = vol.rolling(window=20, min_periods=1).mean()
        ma_trend = close.rolling(window=self.trend_ma, min_periods=1).mean()

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        in_position = False
        peak_price = 0.0

        for i in range(len(df)):
            c = close.iloc[i]
            v = vol.iloc[i]
            ph = prior_high.iloc[i]
            vs = vol_sma.iloc[i]
            trend = ma_trend.iloc[i]

            if not in_position:
                if pd.notna(ph) and c > ph and v >= self.volume_mult * vs and c > trend:
                    signals.iloc[i] = Signal.BUY
                    in_position = True
                    peak_price = c
            else:
                if c > peak_price:
                    peak_price = c

                trailing_stop = peak_price * (1.0 - self.trailing_stop_pct)
                if c <= trailing_stop or c < trend:
                    signals.iloc[i] = Signal.SELL
                    in_position = False
                    peak_price = 0.0

        return signals
