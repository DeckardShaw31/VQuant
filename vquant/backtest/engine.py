"""Vietnam-specific Backtesting Engine supporting T+2.5 settlement and local tax laws."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd


@dataclass
class Trade:
    date: str
    symbol: str
    action: str  # 'BUY' or 'SELL'
    price: float
    shares: int
    gross_value: float
    commission: float
    tax: float
    net_value: float


class BacktestResult:
    """Encapsulates the output of a backtest run."""

    def __init__(
        self,
        equity_curve: pd.Series,
        trades: List[Trade],
        initial_capital: float,
        stats: Dict[str, float],
    ):
        self.equity_curve = equity_curve
        self.trades = trades
        self.initial_capital = initial_capital
        self.stats = stats

    def summary(self) -> str:
        """Formatted textual summary of the backtest performance."""
        lines = [
            "==================================================",
            "          VQUANT BACKTEST PERFORMANCE SUMMARY     ",
            "==================================================",
            f"Initial Capital:        {self.initial_capital:,.0f} VND",
            f"Final Capital:          {self.stats.get('final_capital', 0):,.0f} VND",
            f"Total Return:           {self.stats.get('total_return_pct', 0):.2f}%",
            f"Annualized Return:      {self.stats.get('annualized_return_pct', 0):.2f}%",
            f"Max Drawdown:           {self.stats.get('max_drawdown_pct', 0):.2f}%",
            f"Sharpe Ratio:           {self.stats.get('sharpe_ratio', 0):.2f}",
            f"Total Trades:           {int(self.stats.get('total_trades', 0))}",
            f"Win Rate:               {self.stats.get('win_rate_pct', 0):.2f}%",
            "--------------------------------------------------",
            f"Total Commission Paid:  {self.stats.get('total_commission', 0):,.0f} VND",
            f"Total Sell Tax (0.1%):  {self.stats.get('total_tax', 0):,.0f} VND",
            "==================================================",
        ]
        return "\n".join(lines)


class VNBacktest:
    """Backtesting engine tailored for the Vietnamese equity market.

    Key Features:
    - Enforces T+2.5 settlement delay: shares purchased at day T are locked until day T+2.
    - Accurately deducts Personal Income Tax (0.1%) on gross selling turnover.
    - Deducts brokerage commissions on both buy and sell sides.
    - Respects lot size 100 shares.
    """

    def __init__(
        self,
        initial_capital: float = 100_000_000.0,
        settlement_days: int = 2,
        tax_rate: float = 0.001,  # 0.1% sell tax in VN
        commission_rate: float = 0.0015,  # 0.15% per side
        lot_size: int = 100,
    ):
        self.initial_capital = float(initial_capital)
        self.settlement_days = int(settlement_days)
        self.tax_rate = float(tax_rate)
        self.commission_rate = float(commission_rate)
        self.lot_size = int(lot_size)

    def run_strategy(
        self,
        df: pd.DataFrame,
        strategy: Any,
        symbol: str = "VN_EQUITY",
    ) -> BacktestResult:
        """Run backtest directly from a VQuant Strategy object.

        Args:
            df: DataFrame containing OHLCV price bars.
            strategy: A BaseStrategy instance implementing `generate_signals(df)`.
            symbol: Stock symbol name.

        Returns:
            BacktestResult object.
        """
        signals = strategy.generate_signals(df)
        return self.run(df, signals=signals, symbol=symbol)

    def run(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        symbol: str = "VN_EQUITY",
    ) -> BacktestResult:
        """Run backtest simulation over price DataFrame with trading signals.

        Args:
            df: DataFrame containing at least 'date' (or DatetimeIndex) and 'close'.
            signals: Series containing 1 (Buy), -1 (Sell), or 0 (Hold).
            symbol: Stock symbol name.

        Returns:
            BacktestResult object containing equity curve and performance statistics.
        """
        df = df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        else:
            df["date"] = df.index

        close_prices = df["close"].values
        dates = df["date"].astype(str).values
        n = len(df)

        cash = self.initial_capital
        available_shares = 0
        # Tracks pending shares: list of tuples (settle_bar_index, shares_bought, buy_price)
        pending_batches: List[Dict[str, float]] = []
        trades: List[Trade] = []
        equity_series = np.zeros(n)

        total_tax_paid = 0.0
        total_commission_paid = 0.0

        for i in range(n):
            price = close_prices[i]
            sig = signals.iloc[i] if i < len(signals) else 0

            # 1. Unlock shares that have settled (T+2.5 logic)
            remaining_batches = []
            for batch in pending_batches:
                if i >= batch["settle_bar"]:
                    available_shares += batch["shares"]
                else:
                    remaining_batches.append(batch)
            pending_batches = remaining_batches

            # 2. Process sell signal (-1)
            if sig == -1 and available_shares > 0:
                shares_to_sell = available_shares
                gross_val = shares_to_sell * price
                comm = gross_val * self.commission_rate
                tax = gross_val * self.tax_rate
                net_val = gross_val - comm - tax

                cash += net_val
                available_shares = 0
                total_commission_paid += comm
                total_tax_paid += tax

                trades.append(
                    Trade(
                        date=dates[i],
                        symbol=symbol,
                        action="SELL",
                        price=price,
                        shares=shares_to_sell,
                        gross_value=gross_val,
                        commission=comm,
                        tax=tax,
                        net_value=net_val,
                    )
                )

            # 3. Process buy signal (1)
            elif sig == 1 and cash > (price * self.lot_size * (1 + self.commission_rate)):
                max_affordable = int(cash / (price * (1 + self.commission_rate)))
                shares_to_buy = (max_affordable // self.lot_size) * self.lot_size

                if shares_to_buy > 0:
                    gross_val = shares_to_buy * price
                    comm = gross_val * self.commission_rate
                    total_cost = gross_val + comm

                    cash -= total_cost
                    total_commission_paid += comm

                    pending_batches.append(
                        {
                            "settle_bar": i + self.settlement_days,
                            "shares": shares_to_buy,
                            "buy_price": price,
                        }
                    )

                    trades.append(
                        Trade(
                            date=dates[i],
                            symbol=symbol,
                            action="BUY",
                            price=price,
                            shares=shares_to_buy,
                            gross_value=gross_val,
                            commission=comm,
                            tax=0.0,
                            net_value=-total_cost,
                        )
                    )

            # 4. Calculate total portfolio equity at this bar
            total_held_shares = available_shares + sum(b["shares"] for b in pending_batches)
            portfolio_value = cash + (total_held_shares * price)
            equity_series[i] = portfolio_value

        # Calculate performance statistics
        equity_series_pd = pd.Series(equity_series, index=df["date"])
        final_capital = equity_series[-1]
        total_return_pct = ((final_capital - self.initial_capital) / self.initial_capital) * 100.0

        # Drawdown calculation
        roll_max = equity_series_pd.cummax()
        drawdowns = (equity_series_pd - roll_max) / roll_max
        max_drawdown_pct = abs(drawdowns.min()) * 100.0 if len(drawdowns) > 0 else 0.0

        # Annualized return & Sharpe (assuming 252 trading days)
        days = max(len(df), 1)
        annualized_return_pct = (((final_capital / self.initial_capital) ** (252.0 / days)) - 1) * 100.0

        daily_returns = equity_series_pd.pct_change().dropna()
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        # Win rate
        sell_trades = [t for t in trades if t.action == "SELL"]
        buy_trades = [t for t in trades if t.action == "BUY"]
        wins = 0
        for s, b in zip(sell_trades, buy_trades):
            if s.price > b.price:
                wins += 1
        win_rate_pct = (wins / len(sell_trades) * 100.0) if len(sell_trades) > 0 else 0.0

        stats = {
            "final_capital": final_capital,
            "total_return_pct": total_return_pct,
            "annualized_return_pct": annualized_return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": len(trades),
            "win_rate_pct": win_rate_pct,
            "total_commission": total_commission_paid,
            "total_tax": total_tax_paid,
        }

        return BacktestResult(
            equity_curve=equity_series_pd,
            trades=trades,
            initial_capital=self.initial_capital,
            stats=stats,
        )
