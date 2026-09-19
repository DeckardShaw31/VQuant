"""Tests for Corporate Action Quarantine Protocol (P6: Zero Silent Data Repair)."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from vquant.corpactions import (
    ActionType,
    CorporateActionEvent,
    CorporateActionReconciler,
    QuarantineManager,
)


def test_quarantine_triggers_on_discrepancy():
    """Verify event is quarantined when discrepancy > 1 tick size in strict mode."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        quarantine_file = Path(tmp_dir) / "quarantine.parquet"
        q_mgr = QuarantineManager(quarantine_file=quarantine_file)
        reconciler = CorporateActionReconciler(quarantine_manager=q_mgr)

        events = [
            CorporateActionEvent(
                symbol="TEST",
                ex_date=date(2023, 5, 10),
                record_date=date(2023, 5, 11),
                action_type=ActionType.CASH_DIVIDEND,
                cash_amount=1000.0,
            )
        ]
        # Prev close = 50,000 -> Pred = 49,000. Actual = 45,000 (diff 4,000 >> tick 50)
        with pytest.raises(ValueError, match="Reconciliation failure"):
            reconciler.reconcile_event(
                symbol="TEST",
                ex_date=date(2023, 5, 10),
                p_close_prev=50000.0,
                p_ref_actual=45000.0,
                events=events,
                exchange="HOSE",
                strict=True,
            )

        # Verify recorded in quarantine
        assert q_mgr.count() == 1
        df_q = q_mgr.get_quarantined_items()
        assert df_q["symbol"].iloc[0] == "TEST"
        assert df_q["p_ref_calc"].iloc[0] == 49000.0
        assert df_q["p_ref_actual"].iloc[0] == 45000.0
