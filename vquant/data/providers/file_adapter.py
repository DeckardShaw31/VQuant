"""File-based Bring-Your-Own-Data (BYOD) Provider Adapter."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from vquant.data.providers.base import Capability


class FileAdapter:
    """Adapter reading market data from user-supplied CSV or Parquet files."""

    def __init__(self, data_dir: str | Path):
        self.name = "FileAdapter"
        self.data_dir = Path(data_dir)

    @property
    def capabilities(self) -> list[Capability]:
        return [Capability.PRICES_DAILY, Capability.CORPORATE_ACTIONS]

    def health_check(self) -> bool:
        return self.data_dir.exists() and self.data_dir.is_dir()

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: str | date | datetime,
        end_date: str | date | datetime,
    ) -> pd.DataFrame:
        sym = symbol.upper()
        # Look for parquet or csv
        p_parquet = self.data_dir / f"{sym}.parquet"
        p_csv = self.data_dir / f"{sym}.csv"

        if p_parquet.exists():
            df = pd.read_parquet(p_parquet)
        elif p_csv.exists():
            df = pd.read_csv(p_csv)
        else:
            raise FileNotFoundError(f"No data file found for {sym} in {self.data_dir}")

        df["date"] = pd.to_datetime(df["date"]).dt.date
        s_date = pd.to_datetime(start_date).date()
        e_date = pd.to_datetime(end_date).date()

        filtered = df[(df["date"] >= s_date) & (df["date"] <= e_date)].copy()
        filtered["symbol"] = sym

        # Guarantee expected schema columns
        for col in [
            "foreign_buy_val",
            "foreign_sell_val",
            "foreign_net_val",
            "prop_buy_val",
            "prop_sell_val",
        ]:
            if col not in filtered.columns:
                filtered[col] = 0.0
        if "value" not in filtered.columns:
            filtered["value"] = filtered["close"] * filtered["volume"]
        if "available_at" not in filtered.columns:
            # End of trading day 15:30:00 ICT as available_at
            filtered["available_at"] = pd.to_datetime(filtered["date"]).map(
                lambda d: datetime.combine(d, datetime.min.time()).replace(hour=15, minute=30)
            )

        return filtered.sort_values("date").reset_index(drop=True)

    def fetch_corporate_actions(
        self,
        symbol: str,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
    ) -> pd.DataFrame:
        sym = symbol.upper()
        p_ca = self.data_dir / f"{sym}_corpactions.csv"
        if not p_ca.exists():
            # Return empty frame with schema columns
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
        df = pd.read_csv(p_ca)
        df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.date
        df["record_date"] = pd.to_datetime(df["record_date"]).dt.date
        df["symbol"] = sym
        return df.reset_index(drop=True)
