# ADR-002: Immutable Parquet and DuckDB Catalog

## Status
Accepted

## Context
Large-scale quantitative research requires sub-second queries, reproducibility, and minimal memory overhead. Storing data in loose CSVs or raw pickle files causes schema drift and high I/O latency.

## Decision
- Raw ingested data is stored in partitioned, immutable Parquet files.
- Cleaned, corporate-action-adjusted data is stored in the normalized Parquet layer.
- Metadata and point-in-time catalogs are indexed via embedded DuckDB views.
- Every backtest records the SHA-256 hash of the data snapshot manifest.

## Consequences
- Reproducible research runs across machines.
- High-speed columnar analytics via Apache Arrow and DuckDB.
