# ADR-004: Corporate-Action Reconciliation to Exchange Reference Price

## Status
Accepted

## Context
Corporate actions (cash dividends, stock dividends, bonus shares, rights issues) adjust stock prices. Calculation errors or vendor mistakes create fake price jumps.

## Decision
On ex-dates, the theoretical predicted reference price MUST be reconciled against the official reference price published by the exchange. If the difference exceeds 1 tick, the event is rejected and logged to the `quarantine` table.

## Consequences
- Silent data corruption is prevented.
- All edge cases are catalogued in `known-issues.md`.
