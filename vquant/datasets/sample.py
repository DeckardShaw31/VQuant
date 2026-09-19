"""Embedded sample datasets for VQuant testing and quickstart."""

import numpy as np
import pandas as pd


def load_sample_data(symbol: str = "VN30_SAMPLE", periods: int = 300, random_seed: int = 42) -> pd.DataFrame:
    """Generate realistic OHLCV sample data simulating a Vietnamese stock.

    Args:
        symbol: Symbol identifier (default 'VN30_SAMPLE').
        periods: Number of business trading days to simulate (default 300).
        random_seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume'].
    """
    np.random.seed(random_seed)
    dates = pd.date_range(end="2024-12-31", periods=periods, freq="B")

    # Generate geometric Brownian motion with mild upward drift
    dt = 1.0 / 252.0
    mu = 0.15  # 15% annual drift
    sigma = 0.28  # 28% annual volatility
    returns = np.random.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), size=periods)

    initial_price = 28.5  # Typical VN stock price (28,500 VND in thousands)
    price_series = initial_price * np.exp(np.cumsum(returns))

    # Generate realistic Open, High, Low, Close
    intraday_noise = np.random.uniform(0.005, 0.025, size=periods)
    high = price_series * (1.0 + intraday_noise)
    low = price_series * (1.0 - intraday_noise)
    open_p = low + np.random.uniform(0.2, 0.8, size=periods) * (high - low)
    close = price_series

    # Volume with occasional spikes
    base_volume = np.random.lognormal(mean=14.0, sigma=0.5, size=periods)
    volume_spikes = (np.random.uniform(0, 1, size=periods) > 0.90) * np.random.uniform(1.5, 3.0, size=periods)
    volume = (base_volume * np.where(volume_spikes > 0, volume_spikes, 1.0)).astype(int)

    df = pd.DataFrame(
        {
            "date": dates,
            "open": np.round(open_p, 2),
            "high": np.round(high, 2),
            "low": np.round(low, 2),
            "close": np.round(close, 2),
            "volume": volume,
        }
    )
    return df
