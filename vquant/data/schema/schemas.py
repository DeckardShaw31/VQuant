"""Strict PyArrow Schemas for VQuant Datasets."""

import pyarrow as pa

# Daily OHLCV Bars Schema with Market Microstructure & Flow Attributes
DAILY_BARS_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.int64()),
        ("value", pa.float64()),
        ("foreign_buy_val", pa.float64()),
        ("foreign_sell_val", pa.float64()),
        ("foreign_net_val", pa.float64()),
        ("prop_buy_val", pa.float64()),
        ("prop_sell_val", pa.float64()),
        ("available_at", pa.timestamp("us")),
    ]
)

# Normalized Bars Schema with Split/Dividend Adjustments
NORMALIZED_BARS_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("date", pa.date32()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.int64()),
        ("value", pa.float64()),
        ("foreign_buy_val", pa.float64()),
        ("foreign_sell_val", pa.float64()),
        ("foreign_net_val", pa.float64()),
        ("prop_buy_val", pa.float64()),
        ("prop_sell_val", pa.float64()),
        ("adj_factor_pr", pa.float64()),
        ("adj_factor_tr", pa.float64()),
        ("adj_close_pr", pa.float64()),
        ("adj_close_tr", pa.float64()),
        ("available_at", pa.timestamp("us")),
    ]
)

# Corporate Actions Schema
CORPORATE_ACTIONS_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("ex_date", pa.date32()),
        ("record_date", pa.date32()),
        ("action_type", pa.string()),  # "cash", "bonus", "issue", "split"
        ("cash_amount", pa.float64()),  # VND per share (e.g. 2000.0)
        ("ratio", pa.float64()),  # e.g. 0.1 for 10% bonus
        ("issue_price", pa.float64()),  # VND for rights issue
        ("ref_price_announced", pa.float64()),  # Actual ref price from exchange
        ("source", pa.string()),
        ("available_at", pa.timestamp("us")),
    ]
)

# Corporate Action Quarantine Schema (P6: Zero Silent Data Repair)
QUARANTINE_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("ex_date", pa.date32()),
        ("action_type", pa.string()),
        ("p_close_prev", pa.float64()),
        ("p_ref_calc", pa.float64()),
        ("p_ref_actual", pa.float64()),
        ("tick_diff", pa.float64()),
        ("reason", pa.string()),
        ("quarantined_at", pa.timestamp("us")),
    ]
)
