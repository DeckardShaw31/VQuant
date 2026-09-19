"""Corporate Action Parser and Event Normalization."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

import pandas as pd


class ActionType(str, Enum):
    """Types of corporate action events on the Vietnamese stock market."""

    CASH_DIVIDEND = "cash"
    STOCK_DIVIDEND = "bonus"
    RIGHTS_ISSUE = "issue"
    STOCK_SPLIT = "split"


@dataclass(frozen=True)
class CorporateActionEvent:
    """Normalized corporate action event."""

    symbol: str
    ex_date: date
    record_date: date
    action_type: ActionType
    cash_amount: float = 0.0  # VND per share (for cash dividend)
    ratio: float = 0.0  # Bonus/dividend ratio (e.g. 0.1 for 10%)
    issue_price: float = 0.0  # Purchase price for rights issue (VND)
    ref_price_announced: float | None = None
    source: str = "exchange"
    available_at: datetime | None = None

    @classmethod
    def from_row(cls, row: pd.Series | dict[str, Any]) -> "CorporateActionEvent":
        act_type_str = str(row["action_type"]).lower()
        if "cash" in act_type_str:
            act = ActionType.CASH_DIVIDEND
        elif "bonus" in act_type_str or "stock" in act_type_str:
            act = ActionType.STOCK_DIVIDEND
        elif "issue" in act_type_str or "right" in act_type_str:
            act = ActionType.RIGHTS_ISSUE
        elif "split" in act_type_str:
            act = ActionType.STOCK_SPLIT
        else:
            raise ValueError(f"Unknown corporate action type: {act_type_str}")

        ex_d = pd.to_datetime(row["ex_date"]).date()
        rec_d = pd.to_datetime(row.get("record_date", row["ex_date"])).date()

        return cls(
            symbol=str(row["symbol"]).upper(),
            ex_date=ex_d,
            record_date=rec_d,
            action_type=act,
            cash_amount=float(row.get("cash_amount", 0.0) or 0.0),
            ratio=float(row.get("ratio", 0.0) or 0.0),
            issue_price=float(row.get("issue_price", 0.0) or 0.0),
            ref_price_announced=(
                float(row["ref_price_announced"])
                if pd.notna(row.get("ref_price_announced"))
                else None
            ),
            source=str(row.get("source", "exchange")),
            available_at=pd.to_datetime(row.get("available_at"))
            if pd.notna(row.get("available_at"))
            else None,
        )


def parse_events(df: pd.DataFrame) -> list[CorporateActionEvent]:
    """Parse DataFrame into list of CorporateActionEvent instances."""
    if df.empty:
        return []
    return [CorporateActionEvent.from_row(row) for _, row in df.iterrows()]
