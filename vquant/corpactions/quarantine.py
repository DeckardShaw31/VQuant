"""Corporate Action Quarantine Protocol (Principle P6: Zero Silent Data Repair)."""

from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from vquant.data.schema.schemas import QUARANTINE_SCHEMA


@dataclass(frozen=True)
class QuarantinedItem:
    """Item that failed reference price reconciliation and is isolated."""

    symbol: str
    ex_date: date
    action_type: str
    p_close_prev: float
    p_ref_calc: float
    p_ref_actual: float
    tick_diff: float
    reason: str
    quarantined_at: datetime = datetime.now()


class QuarantineManager:
    """Manages quarantined events in dedicated Parquet storage."""

    def __init__(self, quarantine_file: str | Path):
        self.quarantine_file = Path(quarantine_file)
        self.quarantine_file.parent.mkdir(parents=True, exist_ok=True)

    def record_violation(self, item: QuarantinedItem) -> None:
        """Append a quarantined item to storage (fail loud, P6)."""
        df_new = pd.DataFrame([asdict(item)])
        df_new["ex_date"] = pd.to_datetime(df_new["ex_date"]).dt.date
        df_new["quarantined_at"] = pd.to_datetime(df_new["quarantined_at"])

        if self.quarantine_file.exists():
            df_old = pd.read_parquet(self.quarantine_file)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            # Deduplicate by symbol, ex_date, action_type
            df_combined = df_combined.drop_duplicates(subset=["symbol", "ex_date", "action_type"])
        else:
            df_combined = df_new

        table = pa.Table.from_pandas(df_combined, schema=QUARANTINE_SCHEMA, preserve_index=False)
        pq.write_table(table, self.quarantine_file, compression="zstd")

    def get_quarantined_items(self, symbol: str | None = None) -> pd.DataFrame:
        """Return all or symbol-specific quarantined items."""
        if not self.quarantine_file.exists():
            return pd.DataFrame(columns=[f.name for f in QUARANTINE_SCHEMA])
        df = pd.read_parquet(self.quarantine_file)
        if symbol is not None:
            df = df[df["symbol"] == symbol.upper()]
        return df.reset_index(drop=True)

    def count(self) -> int:
        """Return total number of quarantined items."""
        return len(self.get_quarantined_items())
