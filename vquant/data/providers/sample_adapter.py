"""Sample Data Provider Adapter for Offline Simulation and Testing."""

from datetime import date, datetime

import numpy as np
import pandas as pd

from vquant.data.providers.base import Capability


class SampleAdapter:
    """Adapter generating realistic synthetic data conforming to DataProvider protocol."""

    def __init__(self, random_seed: int = 42):
        self.name = "SampleAdapter"
        self.random_seed = random_seed

    @property
    def capabilities(self) -> list[Capability]:
        return [Capability.PRICES_DAILY, Capability.CORPORATE_ACTIONS, Capability.FLOWS]

    def health_check(self) -> bool:
        return True

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: str | date | datetime,
        end_date: str | date | datetime,
    ) -> pd.DataFrame:
        sym = symbol.upper()
        s_date = pd.to_datetime(start_date).date()
        e_date = pd.to_datetime(end_date).date()

        dates = pd.bdate_range(start=s_date, end=e_date)
        n = len(dates)
        if n == 0:
            return pd.DataFrame(
                columns=[
                    "symbol",
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "value",
                    "foreign_buy_val",
                    "foreign_sell_val",
                    "foreign_net_val",
                    "prop_buy_val",
                    "prop_sell_val",
                    "available_at",
                ]
            )

        rng = np.random.default_rng(self.random_seed + sum(ord(c) for c in sym))
        dt = 1.0 / 252.0
        mu = 0.12
        sigma = 0.25
        returns = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), size=n)

        # Baseline price in VND (e.g. 50,000)
        base_price = 50000.0
        log_prices = np.log(base_price) + np.cumsum(returns)
        close_prices = np.exp(log_prices)

        # Round to 50 VND tick grid
        close_prices = np.round(close_prices / 50.0) * 50.0
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = base_price

        # High / Low within intraday drift
        intra_std = rng.uniform(0.005, 0.02, size=n)
        high_prices = np.maximum(open_prices, close_prices) * (1.0 + np.abs(intra_std))
        low_prices = np.minimum(open_prices, close_prices) * (1.0 - np.abs(intra_std))

        high_prices = np.round(high_prices / 50.0) * 50.0
        low_prices = np.round(low_prices / 50.0) * 50.0
        high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
        low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

        # Volume (multiples of 100)
        volume = rng.integers(1000, 50000, size=n) * 100
        value = close_prices * volume

        # Foreign flows
        f_buy = rng.uniform(0.05, 0.25, size=n) * value
        f_sell = rng.uniform(0.05, 0.25, size=n) * value
        f_net = f_buy - f_sell

        p_buy = rng.uniform(0.02, 0.10, size=n) * value
        p_sell = rng.uniform(0.02, 0.10, size=n) * value

        df = pd.DataFrame(
            {
                "symbol": sym,
                "date": dates.date,
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": volume,
                "value": value,
                "foreign_buy_val": f_buy,
                "foreign_sell_val": f_sell,
                "foreign_net_val": f_net,
                "prop_buy_val": p_buy,
                "prop_sell_val": p_sell,
            }
        )
        df["available_at"] = pd.to_datetime(df["date"]).map(
            lambda d: datetime.combine(d, datetime.min.time()).replace(hour=15, minute=30)
        )
        return df

    def fetch_corporate_actions(
        self,
        symbol: str,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> pd.DataFrame:
        sym = symbol.upper()
        data = [
            {
                "symbol": sym,
                "ex_date": date(2023, 6, 15),
                "record_date": date(2023, 6, 16),
                "action_type": "cash",
                "cash_amount": 2000.0,
                "ratio": 0.0,
                "issue_price": 0.0,
                "ref_price_announced": 48000.0,
                "source": "SampleExchangeNotice",
                "available_at": datetime(2023, 6, 1, 9, 0),
            }
        ]
        return pd.DataFrame(data)
