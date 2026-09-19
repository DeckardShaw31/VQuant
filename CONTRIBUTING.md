# Contributing to VQuant

Thank you for your interest in contributing to **VQuant**!

Our primary design directive is: **A Vietnamese-equities backtest is realistic by default and cannot silently cheat.**

---

## 1. Development Principles
Before contributing, please review the 8 design principles in [ARCHITECTURE.md](Documentation/ARCHITECTURE.md):
- **P1: Market rules are versioned data, not code.** Do not hardcode market rules in Python `if/else` date branches. Add or edit a YAML file under `vquant/market/regimes/`.
- **P2: Point-in-time (PIT) everywhere.** Never use future information. Every record must carry `available_at`.
- **P3: Reproducible runs.** Runs must be auditable via Run Manifests.
- **P4: Provider-agnostic core.** Data sources are pluggable adapters under `vquant.data.providers.Provider` protocol.
- **P5: Pandas-facing, columnar inside.** Public methods return pandas; internal computations use PyArrow, Parquet, and DuckDB.
- **P6: Fail loud.** Never silently patch bad data; quarantine irreconcilable corporate actions.
- **P7: Explicit stability tiers.** Tag all symbols as `@tier("stable" | "beta" | "experimental")`.
- **P8: Honest by default.** Reports must include Deflated Sharpe Ratio (DSR), PBO, and cost breakdowns.

---

## 2. Definition of Done (DoD)
Every Pull Request must satisfy:
1. **Full Test Coverage**: Unit tests + property-based tests (`hypothesis`) or golden regression fixtures.
2. **Type Safety**: Passes `mypy --strict` with zero warnings.
3. **Layering Contracts**: Passes `lint-imports` without violating architecture boundaries.
4. **Market Rule Citations**: When encoding a rule, cite the official decree, circular, or exchange notice.
5. **Documentation**: Bilingual updates (English and Vietnamese for user-facing features).

---

## 3. Commit Convention
We follow Conventional Commits:
- `feat(scope): ...`
- `fix(scope): ...`
- `docs(scope): ...`
- `test(scope): ...`
- `refactor(scope): ...`
