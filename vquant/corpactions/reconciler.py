"""Corporate Action Reconciler with Vietnam Exchange Reference Price Formula."""

from datetime import date, datetime

import pandas as pd

from vquant.corpactions.parser import ActionType, CorporateActionEvent
from vquant.corpactions.quarantine import QuarantinedItem, QuarantineManager
from vquant.market.engine import get_tick_size, round_to_tick


class CorporateActionReconciler:
    """Reconciles predicted theoretical ref prices against exchange ref prices.

    Vietnam Regulatory Formula for Ex-Date Theoretical Reference Price:
        P_ref = (P_close - C + P_issue * r_issue) / (1 + r_bonus + r_issue)
    where:
        - P_close: Close price on the day prior to ex-date
        - C: Cash dividend amount per share (VND)
        - P_issue: Rights issue purchase price (VND)
        - r_issue: Rights issue ratio
        - r_bonus: Stock bonus / stock dividend ratio
    """

    def __init__(self, quarantine_manager: QuarantineManager | None = None):
        self.quarantine_manager = quarantine_manager

    def calculate_theoretical_ref_price(
        self,
        p_close_prev: float,
        events: list[CorporateActionEvent],
        exchange: str,
        ex_date: str | date | datetime,
    ) -> float:
        """Calculate predicted reference price rounded to the nearest exchange tick."""
        c_cash = sum(e.cash_amount for e in events if e.action_type == ActionType.CASH_DIVIDEND)
        r_bonus = sum(e.ratio for e in events if e.action_type == ActionType.STOCK_DIVIDEND)

        rights_events = [e for e in events if e.action_type == ActionType.RIGHTS_ISSUE]
        rights_numerator = sum(e.issue_price * e.ratio for e in rights_events)
        r_issue = sum(e.ratio for e in rights_events)

        numerator = p_close_prev - c_cash + rights_numerator
        denominator = 1.0 + r_bonus + r_issue

        if denominator <= 0:
            raise ValueError(
                f"Invalid denominator ({denominator}) in corporate action calculation."
            )

        raw_ref = numerator / denominator

        # Handle stock split if present
        split_events = [e for e in events if e.action_type == ActionType.STOCK_SPLIT]
        if split_events:
            for s in split_events:
                if s.ratio > 0:
                    raw_ref = raw_ref / s.ratio

        # Round to nearest valid exchange tick size
        return round_to_tick(raw_ref, exchange=exchange, dt=ex_date, direction="nearest")

    def reconcile_event(
        self,
        symbol: str,
        ex_date: str | date | datetime,
        p_close_prev: float,
        p_ref_actual: float,
        events: list[CorporateActionEvent],
        exchange: str = "HOSE",
        strict: bool = True,
    ) -> tuple[bool, float, float]:
        """Reconcile theoretical ref price with exchange announced ref price.

        Returns: (is_valid, p_ref_predicted, tick_diff)
        If difference exceeds 1 tick:
            - If quarantine_manager exists: Records item to quarantine.
            - If strict=True: Raises ValueError (fail loud, P6).
        """
        p_pred = self.calculate_theoretical_ref_price(p_close_prev, events, exchange, ex_date)
        tick = get_tick_size(p_pred, exchange, ex_date)
        diff = abs(p_pred - p_ref_actual)

        # Allow at most 1 tick size tolerance for exchange rounding peculiarities
        is_valid = diff <= (tick + 1e-6)

        if not is_valid:
            reason = (
                f"Reconciliation failure for {symbol} on {ex_date}: "
                f"Predicted {p_pred:.1f} vs Actual {p_ref_actual:.1f} "
                f"(diff={diff:.1f} > tick={tick:.1f})"
            )
            if self.quarantine_manager is not None:
                item = QuarantinedItem(
                    symbol=symbol.upper(),
                    ex_date=pd.to_datetime(ex_date).date(),
                    action_type=",".join(e.action_type.value for e in events),
                    p_close_prev=p_close_prev,
                    p_ref_calc=p_pred,
                    p_ref_actual=p_ref_actual,
                    tick_diff=diff / tick if tick > 0 else 0.0,
                    reason=reason,
                    quarantined_at=datetime.now(),
                )
                self.quarantine_manager.record_violation(item)

            if strict:
                raise ValueError(reason)

        return is_valid, p_pred, diff
