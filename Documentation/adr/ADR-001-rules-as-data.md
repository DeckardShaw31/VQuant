# ADR-001: Market Rules as Effective-Dated Data, Not Code

## Status
Accepted

## Context
Vietnamese exchange regulations evolve over time (e.g. tick sizes changed in 2016, KRX system cutover on 5 May 2025, settlement cycle reforms). Hardcoding conditional branches in Python code leads to stale logic, hidden bugs, and unmaintainable technical debt.

## Decision
All market rules (sessions, tick tables, lot sizes, price bands, settlement regimes, feature flags) MUST be stored as declarative YAML files under `vquant/market/regimes/<exchange>/` with explicit `effective_from` and `effective_to` dates and citations to the underlying exchange notice or decree.

## Consequences
- Engine logic is pure and stateless.
- Backtests can simulate past regimes faithfully without changing code.
- New exchange rules can be added simply by dropping a new YAML file into the repository.
