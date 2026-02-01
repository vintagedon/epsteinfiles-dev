# Epstein Files ARD Context

<!-- 
Purpose: Current state, next steps, active decisions - the most frequently updated file
Audience: AI agents needing to understand "where are we now?"
Update Frequency: After every significant work session
CRITICAL: Keep this current. Stale context is worse than no context.
-->

## Current State

**Last Updated:** 2026-02-01

### Recent Accomplishments

- M01 complete: Repository scaffolded, memory bank populated, scope bounded
- M02 complete: GitHub Project configured with milestones M03-M08, 18 tasks created
- M03 complete: Source evaluation, L0 import with provenance documentation
  - Flight logs: 5,001 records from Internet Archive PDF
  - Black book: 2,324 records from epsteinsblackbook.com
  - Reproducible extraction scripts with `--verify-only` flags
  - Full SHA-256 provenance chains documented

### Current Phase

We are currently in **Milestone 04: Layer 0 Validation** which involves schema definition, quality audit, and preparation for PostgreSQL import.

### Active Work

Next session should begin:

1. **Task 4.1:** Define formal JSON schemas for both datasets
2. **Task 4.2:** Run comprehensive quality audit
3. **Task 4.3:** Document data quality issues for L1 consideration

## Next Steps

### Immediate (Next Session)

1. Create JSON schema definitions in `data/layer-0-canonical/schema/`
2. Build validation scripts against schemas
3. Audit data quality (nulls, format consistency, edge cases)
4. Document findings for L1 processing decisions

### Near-Term (M04-M05)

- PostgreSQL table creation from schemas
- Import L0 CSVs to database
- M05: Layer 1 entity extraction and normalization

### Future / Backlog

- M06: Layer 2 vector embeddings
- M07: Layer 3 graph relationships
- M08: Web interface at epsteinfiles.dev
- Cross-reference with ARD methodology repo as case study

## Active Decisions

### Pending Decisions

- **Vector database choice:** pgvector (aligned with cluster) vs. dedicated vector DB. Leaning pgvector for simplicity.
- **Graph storage:** Neo4j vs. PostgreSQL with recursive CTEs. Defer until M07.
- **Entity resolution approach:** Rule-based vs. ML-based for L1 name matching. Evaluate in M05.

### Recent Decisions

- **2026-02-01 - Internet Archive for flight logs:** Pre-structured 22-column format with 82% passenger identification beat alternatives.
- **2026-02-01 - epsteinsblackbook.com for black book:** Row-level Wayback provenance links, already parsed fields.
- **2026-02-01 - Minimal L0 transformation:** Schema preserved for PostgreSQL materialization; transformations happen in SQL.
- **2026-02-01 - Deterministic UUIDs:** record_id derived from row content hash for reproducibility.

## Blockers and Dependencies

### Current Blockers

- None

### External Dependencies

- PostgreSQL instance for L1+ processing (cluster resource)

## Layer 0 Inventory

| Dataset | Records | File | SHA-256 |
|---------|---------|------|---------|
| Flight Logs | 5,001 | `flight-logs.csv` | `af9ed4eb...` |
| Black Book | 2,324 | `black-book.csv` | `2ab19186...` |

## Notes and Observations

### Data Quality Notes (for M04)

**Flight Logs:**
- 17.7% passengers marked "Unknown" (initials only)
- Coverage ends September 2002
- No crew manifest data

**Black Book:**
- 34% missing country field
- 17% email coverage (expected for era)
- Some entries are organizations, not individuals

### Context for Next Session

Begin M04 with schema definition. Reference `research/source-analysis/` for column definitions. L0 data is validated and ready for formal schema work.
