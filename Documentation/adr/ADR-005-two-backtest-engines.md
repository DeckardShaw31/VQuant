# ADR-005: Dual Backtest Engines (Vectorized and Event-Driven)

## Status
Accepted

## Context
Researchers need ultra-fast parameter sweeps (vectorized), but live execution requires realistic order handling, queues, and intraday fills (event-driven).

## Decision
VQuant provides both:
1. A fast vectorized engine for multi-year sweeps.
2. A high-fidelity event-driven engine for realistic execution.
Both share the same market rules layer, and a CI consistency test guarantees cumulative equity divergence stays under 5 basis points.

## Consequences
- Researchers get speed without sacrificing execution realism.
