# ROADMAP

> **Status:** Draft 0.1 · 2026-09-19
> **Package name:** `vnq` is a placeholder.
> **Companion document:** [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Table of contents

1. [Assumptions and planning rules](#1-assumptions-and-planning-rules)
2. [Release train at a glance](#2-release-train-at-a-glance)
3. [Phase details](#3-phase-details)
4. [Gates](#4-gates)
5. [Cross-cutting tracks](#5-cross-cutting-tracks)
6. [Adoption plan](#6-adoption-plan)
7. [Metrics](#7-metrics)
8. [Risk register](#8-risk-register)
9. [Scope-cut order](#9-scope-cut-order)
10. [First 14 days](#10-first-14-days)
11. [Post-1.0 backlog](#11-post-10-backlog)
12. [References](#12-references)

---

## 1. Assumptions and planning rules

**Capacity assumption:** one maintainer at about 20 h/week (52 weeks ≈ 1,040 h). Timelines scale linearly with capacity: at 10 h/week, double every duration. Co-maintainers (target: by v0.5) shorten the Phase 4/5 critical paths, because those phases are parallelisable.

**Planning rules**

1. **Correctness before breadth.** No phase starts until the previous phase's exit criteria pass.
2. **Ship early.** Publish v0.1 (data and rules) around week 8. Early users find the corporate-action edge cases you will not.
3. **Numeric exit criteria only.** "Works" is not an exit criterion. Each phase has measurable, automated checks.
4. **Rules as data from day one** (ARCHITECTURE P1). No date-conditional code paths.
5. **No live trading before the gates in Phase 6.**
6. **Definition of Done (every feature):** tests (unit, plus property/golden where relevant), type hints, docstring, docs entry (EN, and VI for user-facing pages), changelog line, example or notebook, and rule/source references where a market rule is involved.

**Effort budget**

| Phase | Weeks | Hours (20 h/wk) |
|---|---|---|
| 0 Foundations | 1–2 | 40 |
| 1 Data core | 3–8 | 120 |
| 2 Backtest core | 9–14 | 120 |
| 3 Research toolkit | 15–20 | 120 |
| 4 Portfolio and risk | 21–28 | 160 |
| 5 PIT fundamentals and flows | 29–36 | 160 |
| 6 Execution and hardening | 37–48 | 240 |
| 7 v1.0 | 49–52 | 80 |
| **Total** | **52** | **1,040** |

---

## 2. Release train at a glance

| Version | Target week | Theme | Public? |
|---|---|---|---|
| 0.1 | 8 | Data, rules, corporate actions, validation | Yes (PyPI pre-release) |
| 0.2 | 14 | Backtest engines, fills, costs, ledger | Yes |
| 0.3 | 20 | Research toolkit and integrity tooling. **Minimum viable well-known library** | Yes |
| 0.4 | 28 | Portfolio, lot-aware allocator, risk, VN30F | Yes |
| 0.5 | 36 | PIT fundamentals, sector templates, flows, macro | Yes |
| 0.9 | 48 | Paper trading, broker adapters (beta), CLI, monitoring, full bilingual docs | Yes |
| 1.0 | 52 | API freeze for `stable` tier, benchmark suite | Yes |

---

## 3. Phase details

### Phase 0: Foundations (weeks 1–2, 40 h)

**Goal:** a repository that enforces the architecture's principles before any feature code exists.

**Deliverables**

- [ ] Name check (PyPI, GitHub, trademark). Decide final package name (OQ-7).
- [ ] Apache-2.0 license, CONTRIBUTING, code of conduct, issue templates, security policy.
- [ ] `pyproject.toml` (uv or hatch), ruff, mypy strict, import-linter contracts, pre-commit (including secret scanning).
- [ ] CI: lint, type, tests (Python 3.10–3.13 × Linux/macOS/Windows), docs build.
- [ ] Rules-as-data schema and regime loader. Encode current HOSE, HNX, and UPCoM regimes plus the KRX cutover regime (5 May 2025), each citing its source notice.
- [ ] Trading calendar 2015–2027 (holidays, make-up days) as data, with a contributor process for updates.
- [ ] ADR-001 to ADR-005 drafted. Repo skeleton matching ARCHITECTURE §10.

**Exit criteria**

- `market.regime(date, exchange)` returns exactly one regime for every date 2015-01-01 to 2026-12-31 (property test: no gaps, no overlaps).
- Calendar has zero mismatches against a hand-checked sample of at least 50 trading and non-trading days.
- CI green on the full matrix; import-linter blocks a deliberately illegal import in a test.

**Dependencies:** none. **Main risk:** rule details recalled incorrectly, mitigated by the **[verify]** tags and by requiring a source citation per regime file.

---

### Phase 1: Data core → v0.1 (weeks 3–8, 120 h)

**Goal:** trustworthy, adjusted, point-in-time daily prices for at least VN30 (then VN100).

**Deliverables**

- [ ] `Provider` protocol with capability flags, rate limiter, retry/backoff, incremental cache.
- [ ] `vnstock` adapter plus a second source (SSI, DNSE, or CSV-only, per OQ-1) and a BYO-Parquet/CSV adapter.
- [ ] Raw/normalized/quarantine storage with Parquet and DuckDB catalog; snapshot hashing.
- [ ] Corporate-action parser, adjuster (price-return and total-return series), reconciler, and quarantine table.
- [ ] Validation checks V001–V011 (ARCHITECTURE §5.5).
- [ ] PIT universe: listings, delistings, exchange transfers, VN30 constituent history, trading-status history.
- [ ] CLI: `vnq fetch`, `vnq validate`. Quickstart docs (EN and VI). `known-issues.md`.
- [ ] Seed from working code you already trust: port the vnstock wrapper with incremental caching, triple-barrier labeling, purged/embargoed walk-forward, and overfitwatch-style DSR/PBO checks with tests rather than rewriting them. (Labeling and validation ports are staged into Phase 3.)

**Exit criteria**

| Metric | Threshold |
|---|---|
| VN30 ex-dates over 10 years that reconcile to exchange reference price within 1 tick | ≥ 99%, with 100% of residuals catalogued in `known-issues.md` with a cause |
| V001 violations after adjustment (excluding quarantined events) | 0 |
| Cross-source adjusted-price difference under 1 bp | ≥ 99.9% of VN30 bars since 2015 |
| Cold fetch, 30 symbols × 10 years | < 5 min |
| Warm incremental fetch | < 20 s |
| PIT universe: VN30 membership on any test date matches published constituents | 100% on a 12-date sample |

**Release:** v0.1 to PyPI as a pre-release, with a launch post in English and Vietnamese.

**Dependencies:** Phase 0. **Main risks:** vendor breakage (canary CI, BYO path), reconciliation misses (quarantine, do not patch).

---

### Phase 2: Backtest core → v0.2 (weeks 9–14, 120 h)

**Goal:** a backtest whose fills, costs, and settlement follow Vietnamese rules by default.

**Deliverables**

- [ ] Vectorized engine: tradability masks, lot rounding, settlement ledger.
- [ ] Event-driven engine: ATO, ATC, LO, MP, partial fills, participation cap.
- [ ] Fill model (limit-lock rules, tick/2 floor, square-root impact) and cost model (fee tiers, sale tax, dividend withholding, custody, margin interest presets).
- [ ] Ledger with settlement states (ARCHITECTURE §7.4) and the six invariants.
- [ ] Tear sheet and cost attribution. Run manifest.
- [ ] Resolve OQ-2, OQ-3, OQ-4 as ADRs.
- [ ] Three canonical strategies (buy-and-hold VN30, monthly momentum top-quintile, mean-reversion with stop) as reference implementations.

**Exit criteria**

| Metric | Threshold |
|---|---|
| Vectorized vs event-driven cumulative equity divergence, 3 canonical strategies | < 5 bps |
| Ledger invariants under Hypothesis | 1,000,000 random cases, 0 failures |
| Vectorized backtest, 100 stocks × 10 years | < 1 s |
| Event-driven, same universe | < 10 s pure Python (< 1 s with Numba once optimised) |
| Golden backtest regression | Stable within tolerance across two CI runs on a pinned data snapshot |

**Dependencies:** Phase 1. **Main risks:** engine divergence (consistency test as merge gate), fill-model over-precision (defaults documented and overridable).

---

### Phase 3: Research toolkit → v0.3 (weeks 15–20, 120 h)

**Goal:** make honest research easy and dishonest research loud. **v0.3 is the minimum viable well-known library** (see §9).

**Deliverables**

- [ ] Feature registry with declared lookback/lag/availability and the mandatory shift-invariance test. Technical, volatility, and microstructure families first.
- [ ] Labeling: fixed-horizon, triple-barrier (band-aware), meta-labeling, `t0/t1` overlap tracking.
- [ ] Models: scikit-learn and LightGBM wrappers, HMM, GARCH.
- [ ] Validation: purged + embargoed K-fold, CPCV, Deflated Sharpe, PBO, White's Reality Check/SPA, MinBTL, trial-count logging.
- [ ] Integrity section wired into every report.
- [ ] Reference notebooks: (1) "Why your Vietnamese backtest is too good" (tick, lot, cost, band effects quantified), (2) meta-labeling pipeline, (3) multiple-testing demo.

**Exit criteria**

| Metric | Threshold |
|---|---|
| DSR / PBO / MinBTL vs published reference implementations | Match to 1e-6 |
| Shift-invariance test | Passes for 100% of registered features |
| Purge/embargo correctness | Test proves training rows within the embargo window are dropped and test-window coverage is unchanged per fold |
| Notebook execution in CI | 100% pass |

**Release:** v0.3 with a public "VN-Bench" preview (see §6).

**Dependencies:** Phase 2. **Main risk:** subtle leakage in labels (overlap tracking plus property tests).

---

### Phase 4: Portfolio and risk → v0.4 (weeks 21–28, 160 h)

**Goal:** portfolios that are feasible at real Vietnamese account sizes.

**Deliverables**

- [ ] Allocators: equal-weight, volatility-target, risk parity, mean-variance with shrinkage, HRP, Kelly-fraction sizing.
- [ ] **Lot-aware allocator** (greedy baseline, MILP option) with residual-cash and ADV-cap constraints.
- [ ] Risk: EWMA/shrinkage covariance, factor exposures, ADV-based liquidity risk, limit-lock risk, drawdown limits.
- [ ] Optional margin module (lists, ratios, maintenance, forced liquidation, interest).
- [ ] VN30F support: multiplier, margin, roll, hedge overlay.

**Exit criteria**

| Metric | Threshold |
|---|---|
| Lot-aware allocator vs naive rounding at 100M VND, 20 positions | Lower tracking error to target weights on every date in a 5-year test |
| Residual cash | ≤ 1 lot of the cheapest held name, or documented infeasibility |
| Futures P&L | Matches hand-computed multiplier and roll examples to 1 VND |
| Margin liquidation logic | Passes scenario tests derived from written broker terms |

**Dependencies:** Phase 2. Parallelisable with Phase 5 once a co-maintainer joins.

---

### Phase 5: PIT fundamentals and flows → v0.5 (weeks 29–36, 160 h)

**Goal:** fundamentals and market-structure signals without lookahead.

**Deliverables**

- [ ] Bitemporal fundamentals store, `available_at` rule, restatement handling, YTD de-cumulation, TTM.
- [ ] Canonical taxonomy with bank, securities, real-estate, and general templates.
- [ ] Flows: foreign net buy/sell and room, proprietary flows, ETF flows, margin debt, VN30F basis.
- [ ] Macro series with `available_at`: policy and interbank rates, USD/VND, credit growth, CPI, PMI, disbursement.
- [ ] Fundamental and flow feature families in the registry.

**Exit criteria**

| Metric | Threshold |
|---|---|
| Fundamentals shift test (no value visible before `available_at`) | 0 violations across the full universe |
| YTD de-cumulation | Standalone quarters sum to the reported annual figure within rounding for ≥ 99% of company-years |
| Template validation | Bank and non-bank templates populated for ≥ 95% of VN100 |
| Restatement test | Restated values appear only after their own `available_at` |

**Dependencies:** Phase 1 (storage), Phase 3 (registry).

---

### Phase 6: Execution and hardening → v0.9 (weeks 37–48, 240 h)

**Goal:** paper trading and beta broker connectivity, plus the polish needed to be adoptable.

**Deliverables**

- [ ] OMS abstraction (state machine, idempotent IDs, cancel/replace), paper broker sharing the event-engine fill model.
- [ ] Broker adapters (SSI, DNSE) in `beta`, with pre-trade risk checks, kill switch, reconciliation, append-only audit log.
- [ ] CLI (`vnq backtest`, `vnq report`, paper-trading commands), monitoring hooks, scheduling recipes.
- [ ] Full bilingual documentation, market-rules reference pages, cookbook.
- [ ] **Legal review** of automated-order and market-manipulation rules (Law on Securities 2019 and implementing decrees), before any live adapter is marked usable.
- [ ] Performance pass (Numba inner loops, parallel sweeps).

**Exit criteria**

| Metric | Threshold |
|---|---|
| 30-day paper run reconciled to broker records | 0 unexplained breaks |
| Pre-trade checks | 100% of invalid orders (off-tick, off-lot, out-of-band, duplicate) rejected in scenario tests |
| Sweep of 10,000 configs | Near-linear scaling to available cores |
| Docs | Every public `stable`/`beta` symbol documented; VI coverage of quickstart, market rules, and top 10 tutorials |

**Dependencies:** Phases 2–5.

---

### Phase 7: v1.0 (weeks 49–52, 80 h)

**Goal:** stable API and public proof of quality.

**Deliverables**

- [ ] API freeze for the `stable` tier. Deprecation policy in force.
- [ ] Benchmark suite ("VN-Bench") with reproducible published results.
- [ ] Security audit of dependencies, trusted PyPI publishing, signed releases.
- [ ] Migration guide from vnstock-based scripts.
- [ ] Release announcement (EN/VI), maintainers and governance document.

**Exit criteria**

| Metric | Threshold |
|---|---|
| External users completing the tutorial unaided | 3 |
| Open `stable`-tier bugs older than 30 days | 0 |
| Reproducing VN-Bench from a clean checkout | Identical to published numbers within stated tolerance |

---

## 4. Gates

Each gate is a go / adjust / stop decision.

| Gate | When | Question | Evidence |
|---|---|---|---|
| G1 | Week 8 | Is the data correct enough to publish? | Phase 1 exit table |
| G2 | Week 14 | Are backtests trustworthy? | Engine divergence, invariants, golden regression |
| G3 | Week 20 | Does the integrity tooling match reference math? | Phase 3 exit table. Recalibrate the adoption targets below |
| G4 | Week 36 | Is there enough external pull to justify continuing at this scope? | Adoption metrics vs targets |
| G5 | Week 44 | Are we legally and operationally ready for live components? | Legal review, paper-run status |

**Adoption targets (heuristics, recalibrate at G3).** These are planning targets, not predictions.

| By week | Target |
|---|---|
| 20 | ≥ 5 external issues or PRs; ≥ 200 total PyPI downloads per week |
| 36 | ≥ 3 external contributors; at least one third-party adapter or rules contribution |
| 52 | ≥ 3 external users completing the tutorial; one university club or course using the library |

If G4 is missed, prefer narrowing scope (see §9) over extending the timeline.

---

## 5. Cross-cutting tracks

| Track | Continuous activities |
|---|---|
| Testing | Golden fixtures grow with every corporate-action bug. Nightly canary against live providers |
| Docs | Bilingual from v0.1. "Known data problems" and "Market rules" pages updated on every rule change |
| Rules maintenance | Monitor exchange and SSC notices. Each change ships as a new dated regime file with source link |
| Community | Weekly issue triage, contributor on-ramps ("good first issue": holiday tables, corporate-action fixtures, sector templates) |
| Legal | Data-provider terms per adapter. Disclaimers. Pre-live review (Phase 6) |
| Data acquisition | Maintain the BYO-data path so users with licensed data are never blocked by our adapters |

---

## 6. Adoption plan

Features do not make a library well known. Trust, documentation, and distribution do.

1. **Own a correctness claim.** Publish "Market rules" and "Known data problems" from v0.1. Vietnamese quants search for exactly this.
2. **VN-Bench.** Standard strategies (momentum, value, low-volatility, meta-labeled) on VN100 with one shared cost model, published with all results, including those that fail after costs. Honest negative results build credibility. Preview at v0.3, full suite at v1.0.
3. **Time-limited hooks.**
   - FTSE Russell reaffirmed Vietnam's reclassification to secondary emerging market status, effective 21 September 2026, and Circular 08/2026 opened a route for foreign investors to trade through global brokers. An **index-inclusion event-study notebook** is a strong early content piece.
   - Vietnam's earlier introduction of a non-prefunding model for foreign institutions, and the planned CCP, are further natural event-study anchors.
   - Government commentary has cited FTSE Advanced EM and MSCI EM status as longer-term aims (target year 2030), which keeps foreign-flow and index-rebalancing tooling relevant.
4. **Bilingual content.** Vietnamese tutorials, short video walkthroughs, university quant clubs, and Facebook and Zalo communities. A real advantage over English-only libraries.
5. **Integrate, do not fight.** vnstock adapter and migration guide. Export adapters for backtrader, vectorbt, and Qlib.
6. **Contributor on-ramps.** Labelled good-first-issues, a data-quality report template, and a public contributor list.
7. **Publication cadence.** One substantive technical post per release (for example "What the 10,000 VND tick step does to your costs"), each reproducible from the repo.

---

## 7. Metrics

| Metric | Why it matters | Source |
|---|---|---|
| Weekly PyPI downloads | Reach (noisy, mirrors inflate) | pypistats |
| Reconciliation rate (ex-dates within 1 tick) | Core correctness | CI report |
| Open quarantined events | Data quality debt | Quarantine table |
| External contributors and merged external PRs | Ecosystem health | GitHub |
| Median time-to-first-response on issues | Maintainer reliability | GitHub |
| Number of maintained adapters and rule regimes | Coverage | Repo |
| Citations in theses, papers, courses | Credibility | Manual tracking |
| CI flake rate | Engineering health | CI |

GitHub stars are tracked but not used for decisions.

---

## 8. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Trigger to escalate |
|---|---|---|---|---|---|
| R1 | Data source ToS change or breakage | High | High | Adapter isolation, contract tests, nightly canary, BYO-data path, no redistribution | Canary fails 2 nights in a row |
| R2 | Wrong corporate-action adjustments | Medium | High | Reconcile to exchange reference, quarantine, public known-issues page | Reconciliation rate < 98% |
| R3 | Rule change (settlement, short selling, CCP) | High | Medium | Effective-dated regimes and feature toggles | Any SSC/exchange notice |
| R4 | Scope creep | High | High | Phase exit criteria, scope-cut order (§9) | Phase overruns by > 25% |
| R5 | Maintainer bandwidth | High | High | Plugin architecture, narrow `stable` surface, co-maintainers by v0.5 | Two consecutive missed weeks |
| R6 | Credibility loss from inflated backtests | Medium | High | Integrity section on every report, trial-count logging, MinBTL warnings | Any user-reported unrealistic result |
| R7 | Legal exposure (advice, automation, manipulation rules) | Low–Medium | High | Disclaimers, legal review before live execution | Before Phase 6 broker work |
| R8 | Name or trademark collision | Low | Medium | Check at Phase 0 | Any objection |
| R9 | Rule recalled incorrectly | Medium | Medium | **[verify]** tag, source citation per regime file | Any regime file lacking a source |
| R10 | Adoption below targets | Medium | Medium | G3/G4 gates, narrow scope, deepen content and partnerships | G4 miss |

---

## 9. Scope-cut order

If time or adoption falls short, cut in this order, latest items first:

1. Broker adapters and live components (Phase 6 execution).
2. Alternative data (Phase 5 flows and macro beyond foreign flow).
3. Advanced allocators (HRP, MILP) beyond the greedy lot-aware allocator.
4. Margin module.
5. Futures overlay.
6. Event-driven intraday support (daily only).

**Minimum viable well-known library = v0.3:** trustworthy data, realistic backtests, and integrity tooling, with bilingual docs and VN-Bench preview. Everything after v0.3 is an extension of a product that already has a claim.

---

## 10. First 14 days

About 40 hours at 20 h/week (roughly 3 h/day).

| Day | Task | Hours |
|---|---|---|
| 1 | Name check, repo creation, license, CONTRIBUTING, code of conduct | 3 |
| 2 | `pyproject.toml`, ruff, mypy, pre-commit with secret scanning | 3 |
| 3 | CI matrix (3.10–3.13 × 3 OS), docs skeleton (mkdocs-material, EN/VI) | 3 |
| 4 | Import-linter contracts and repo skeleton per ARCHITECTURE §10 | 3 |
| 5 | Rules-as-data schema and regime loader with tests | 3 |
| 6 | Encode HOSE regimes (pre-KRX and 2025-05-05 KRX) with source citations | 3 |
| 7 | Encode HNX and UPCoM regimes. Property test: no gaps or overlaps | 3 |
| 8 | Trading calendar 2015–2027 as data | 3 |
| 9 | Calendar verification against a 50-day hand-checked sample | 3 |
| 10 | Corporate-action reconciliation spec: formulas, rounding question (OQ-2) | 3 |
| 11 | Hand-collect 15 real ex-dates (cash, stock) as golden fixtures | 3 |
| 12 | Hand-collect 15–35 more ex-dates (rights, combined, splits) | 3 |
| 13 | Hypothesis tests for tick, lot, and band invariants | 3 |
| 14 | ADR-001 to ADR-005, README, v0.0.1 tag. Phase 0 exit-criteria review | 4 |

**Total:** 43 h, slightly above the 40 h Phase 0 budget. Day 14 review absorbs slippage, and any overrun is charged to the Phase 1 buffer.

---

## 11. Post-1.0 backlog

- Historical intraday and tick data pipeline (OQ-5), microstructure research tools.
- Covered warrants, ETFs, and options once liquid.
- Government bond and interest-rate analytics.
- Optional Polars front-end (OQ-6).
- Factor library with Vietnamese factor returns (published and reproducible).
- Corporate-event studies toolkit (index inclusion, rights issues, foreign-room events).
- Web dashboard for run manifests and integrity reports.
- Governance transition: maintainers group, RFC process.

---

## 12. References

- KRX go-live (5 May 2025): https://vietnamnews.vn/economy/1717047/krx-system-officially-goes-live.html
- KRX-enabled features and CCP context: https://theinvestor.vn/vietnams-new-stock-trading-system-krx-to-go-live-on-may-5-d15128.html
- FTSE Russell confirmation and Circular 08/2026: https://news.tuoitre.vn/ftse-russell-confirms-vietnam-stock-market-upgrade-103260408190951389.htm
- Non-prefunding model, failed-trade handling: https://news.tuoitre.vn/vietnam-stock-market-upgraded-to-secondary-emerging-status-103251008112750752.htm
- Reform roadmap including CCP timeline (full CCP operation targeted for Q1 2027): https://vietnam-briefing.com/news/vietnam-reclassified-to-emerging-market-status-by-ftse-russell.html
- Longer-term EM aspirations (commentary): https://professionalparaplanner.co.uk/?p=21213
- Rule texts to confirm before encoding: Law on Securities 2019 and implementing decree, disclosure circular, settlement circular, current HOSE/HNX trading regulations.
