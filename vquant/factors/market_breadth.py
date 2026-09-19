"""Alpha Factors and Market Breadth calculations for the Vietnamese Market."""

import pandas as pd


def calculate_ma_breadth(df_prices: pd.DataFrame, window: int = 20) -> pd.Series:
    """Calculate the percentage of stocks trading above their moving average (Market Breadth).

    Args:
        df_prices: DataFrame where columns are stock symbols and rows are trading dates.
        window: Moving average period (e.g. 20, 50, 200).

    Returns:
        Series of market breadth percentage (0.0 to 100.0) for each date.
    """
    ma = df_prices.rolling(window=window).mean()
    above_ma = df_prices > ma
    breadth_pct = (above_ma.sum(axis=1) / df_prices.count(axis=1)) * 100.0
    return breadth_pct
