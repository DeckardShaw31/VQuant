"""Adapter for Vnstock Ecosystem (vnstock / vnstock_data)."""

import warnings
from datetime import date, datetime

import pandas as pd

from vquant.data.providers.base import Capability


class VNStockAdapter:
    """Adapter bridging Vnstock ecosystem to VQuant DataProvider protocol."""

    def __init__(self, api_key: str | None = None):
        self.name = "VNStockAdapter"
        self.api_key = api_key
        self._is_available = self._check_availability()

    def _check_availability(self) -> bool:
        import importlib.util

        return importlib.util.find_spec("vnstock") is not None

    @property
    def capabilities(self) -> list[Capability]:
        return [Capability.PRICES_DAILY, Capability.CORPORATE_ACTIONS]

    def health_check(self) -> bool:
        return self._is_available

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: str | date | datetime,
        end_date: str | date | datetime,
    ) -> pd.DataFrame:
        if not self._is_available:
            raise ImportError(
                "vnstock not installed. Install via pip or use FileAdapter / SampleAdapter."
            )
        try:
            from vnstock import Vnstock

            stock = Vnstock().stock(symbol=symbol.upper(), source="VCI")
            df = stock.quote.history(
                start=str(start_date)[:10],
                end=str(end_date)[:10],
                interval="1D",
            )
            if df.empty:
                return pd.DataFrame()
            df = df.rename(
                columns={"time": "date", "match_volume": "volume", "match_value": "value"}
            )
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["symbol"] = symbol.upper()
            for col in [
                "foreign_buy_val",
                "foreign_sell_val",
                "foreign_net_val",
                "prop_buy_val",
                "prop_sell_val",
            ]:
                if col not in df.columns:
                    df[col] = 0.0
            df["available_at"] = pd.to_datetime(df["date"]).map(
                lambda d: datetime.combine(d, datetime.min.time()).replace(hour=15, minute=30)
            )
            return df.sort_values("date").reset_index(drop=True)
        except Exception as e:
            warnings.warn(f"Failed to fetch from vnstock: {e}. Returning empty DataFrame.")
            return pd.DataFrame()

    def fetch_corporate_actions(
        self,
        symbol: str,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            columns=[
                "symbol",
                "ex_date",
                "record_date",
                "action_type",
                "cash_amount",
                "ratio",
                "issue_price",
                "ref_price_announced",
                "source",
                "available_at",
            ]
        )
