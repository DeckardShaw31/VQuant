# ADR-003: Bitemporal Fundamentals and the available_at Discipline

## Status
Accepted

## Context
Financial statements are released weeks or months after the fiscal quarter ends. Using `period_end` as the query timestamp introduces catastrophic lookahead bias.

## Decision
Every fundamental observation stores two timestamps: `period_end` (fiscal period) and `available_at` (actual disclosure timestamp or conservative statutory deadline). Restatements append new rows with new `available_at` values.

## Consequences
- Queries take `as_of` date and only return values where `available_at <= as_of`.
- Completely eliminates lookahead bias in fundamental factor research.
