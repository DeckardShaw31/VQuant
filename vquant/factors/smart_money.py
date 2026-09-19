"""Smart Money & Institutional Flow Factors for the Vietnamese Market."""

import numpy as np
import pandas as pd


def calculate_cumulative_foreign_flow(foreign_net_val: pd.Series, window: int = 5) -> pd.Series:
    """Calculate the rolling cumulative net buying value of foreign investors.

    Args:
        foreign_net_val: Series containing daily net foreign buying value (Buy Value - Sell Value).
        window: Number of rolling trading days (default 5).

    Returns:
        pd.Series of cumulative net foreign value over the window.
    """
    return foreign_net_val.rolling(window=window, min_periods=1).sum()


def calculate_foreign_streak(foreign_net_val: pd.Series) -> pd.Series:
    """Calculate consecutive streak of days foreign investors were net buyers (> 0).

    Returns:
        pd.Series where positive integer represents consecutive net buying days,
        and 0 represents net selling or neutral days.
    """
    is_buying = (foreign_net_val > 0).astype(int)
    streaks = np.zeros(len(foreign_net_val), dtype=int)
    current_streak = 0

    for i in range(len(foreign_net_val)):
        if is_buying.iloc[i] == 1:
            current_streak += 1
        else:
            current_streak = 0
        streaks[i] = current_streak

    return pd.Series(streaks, index=foreign_net_val.index, name="foreign_streak")


def calculate_foreign_turnover_ratio(
    foreign_net_val: pd.Series, total_value: pd.Series
) -> pd.Series:
    """Calculate the ratio of net foreign buying to total turnover.

    Args:
        foreign_net_val: Net foreign buying value.
        total_value: Total trading value of the stock.

    Returns:
        pd.Series representing foreign net participation ratio (0.0 to 1.0).
    """
    safe_total = total_value.replace(0, np.nan)
    ratio = foreign_net_val / safe_total
    return ratio.fillna(0.0)
