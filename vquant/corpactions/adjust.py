"""Price and Total Return Adjustment Factor Calculation."""

from datetime import date

import numpy as np
import pandas as pd

from vquant.corpactions.parser import ActionType, CorporateActionEvent


class PriceAdjuster:
    """Calculates backward-adjusted Price-Return (PR) and Total-Return (TR) series."""

    @staticmethod
    def compute_daily_adjustment_factors(
        df_bars: pd.DataFrame,
        events: list[CorporateActionEvent],
        exchange: str = "HOSE",
    ) -> pd.DataFrame:
        """Compute backward cumulative adjustment factors for Price Return and Total Return.

        - Price Return Factor (adj_factor_pr): Accounts for stock dividends, bonuses, splits.
        - Total Return Factor (adj_factor_tr): Re-invests cash dividends on ex-date.
        """
        if df_bars.empty:
            return df_bars

        df = df_bars.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        n = len(df)
        mult_pr = np.ones(n, dtype=np.float64)
        mult_tr = np.ones(n, dtype=np.float64)

        # Map events by ex_date
        events_by_date: dict[date, list[CorporateActionEvent]] = {}
        for ev in events:
            events_by_date.setdefault(ev.ex_date, []).append(ev)

        # Find bar indexes for ex-dates
        date_to_idx = {d: i for i, d in enumerate(df["date"])}

        for ex_d, ev_list in events_by_date.items():
            if ex_d not in date_to_idx:
                continue
            idx = date_to_idx[ex_d]
            if idx == 0:
                continue

            # Prior day close price
            p_close_prev = float(df.loc[idx - 1, "close"])

            # Factors
            c_cash = sum(
                e.cash_amount for e in ev_list if e.action_type == ActionType.CASH_DIVIDEND
            )
            r_bonus = sum(e.ratio for e in ev_list if e.action_type == ActionType.STOCK_DIVIDEND)

            rights_events = [e for e in ev_list if e.action_type == ActionType.RIGHTS_ISSUE]
            rights_num = sum(e.issue_price * e.ratio for e in rights_events)
            r_issue = sum(e.ratio for e in rights_events)

            # Split
            split_ratio = 1.0
            for s in ev_list:
                if s.action_type == ActionType.STOCK_SPLIT and s.ratio > 0:
                    split_ratio *= s.ratio

            # 1. Price-Return ratio: (P_close - C + P_issue * r_issue) / ((1 + r) * split) / P_close
            p_pred_total = (p_close_prev - c_cash + rights_num) / (
                (1.0 + r_bonus + r_issue) * split_ratio
            )
            factor_pr_step = p_pred_total / p_close_prev if p_close_prev > 0 else 1.0

            # 2. Total-Return ratio
            factor_tr_step = p_pred_total / p_close_prev if p_close_prev > 0 else 1.0

            # Apply backward multiplication to all bars strictly before ex_date
            mult_pr[:idx] *= factor_pr_step
            mult_tr[:idx] *= factor_tr_step

        df["adj_factor_pr"] = mult_pr
        df["adj_factor_tr"] = mult_tr
        df["adj_close_pr"] = df["close"] * df["adj_factor_pr"]
        df["adj_close_tr"] = df["close"] * df["adj_factor_tr"]

        return df
