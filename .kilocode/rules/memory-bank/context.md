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
- M04 complete: Layer 0 Validation (schemas, quality audit, transformation plan)
- **M05 complete: Layer 1 Scalars**
  - Task 5.1: Database setup on pgsql01, L0 import (5,001 + 2,324 rows)
  - Task 5.2: Flight logs transforms (FL-1 through FL-4)
  - Task 5.3: Black book transforms (BB-1 through BB-4)
  - Task 5.4: Unified identity mentions with probablepeople parsing
  - Task 5.5: Validation + DDL scripts
  - **Validation: All checks pass, metrics exported**

### Current Phase

**Milestone 05 COMPLETE.** Ready for M06: Layer 2 Vectors.

### Active Work

Next session should begin M06.

## M05 Deliverables Summary

| Artifact | Path |
|----------|------|
| Project .env | `.env` (gitignored) |
| L0 import script | `pipelines/ingestion/import_l0_to_postgres.py` |
| Flight logs L1 transform | `pipelines/processing/transform_flight_logs_l1.py` |
| Black book L1 transform | `pipelines/processing/transform_black_book_l1.py` |
| Identity mentions builder | `pipelines/processing/build_identity_mentions.py` |
| L1 validation script | `pipelines/validation/validate_l1.py` |
| Reproducible DDL | `pipelines/ddl/create_epsteinfiles_db.sql` |
| L1 metrics JSON | `research/quality-analysis/l1-metrics.json` |

## L1 Final Metrics

| Table | Records | Notes |
|-------|---------|-------|
| l1.flight_events | 1,491 | Unique flights |
| l1.flight_passengers | 5,001 | 566 suppressed (victim protection) |
| l1.contacts | 2,324 | 1,777 individual, 289 household, 226 org |
| l1.contact_persons | 2,610 | Multi-person decomposition |
| l1.phone_numbers | 5,585 | 47.1% valid E.164 |
| l1.identity_mentions | 6,783 | 885 Soundex blocks, ready for embedding |

### Cross-Dataset Signal

- **22 exact name matches** (case-insensitive) between flight logs and black book
- **134 Soundex codes** appear in both datasets
- Average 7.4 mentions per Soundex block (good for resolution)

## Next Steps

### Immediate (M06: Layer 2 Vectors)

1. **Task 6.1: Embedding model setup**
   - Install sentence-transformers
   - Select model: all-MiniLM-L6-v2 (384-dim) or larger
   - Test on sample names

2. **Task 6.2: Generate name embeddings**
   - Embed all 6,783 identity mentions
   - Store in `l1.identity_mentions.name_embedding`
   - Create IVFFlat index for similarity search

3. **Task 6.3: Entity resolution candidates**
   - Combine Soundex blocking with vector similarity
   - Generate candidate pairs within blocks
   - Score with cosine similarity + Jaro-Winkler

4. **Task 6.4: Validation**
   - Spot-check known entities (Epstein, Maxwell, etc.)
   - Evaluate precision/recall on sample
   - Tune similarity thresholds

### Near-Term (M06-M07)

- Finalize entity resolution thresholds
- Create resolved_entities table (M07)
- Build relationship graphs

### Future / Backlog

- M07: Layer 3 graph relationships (recursive CTEs per GDR)
- M08: Web interface at epsteinfiles.dev with K-anonymity views

## Active Decisions

### Approved Decisions

| Decision | Details |
|----------|---------|
| Database | `epsteinfiles_ard` on pgsql01 (10.25.20.8) |
| Schema structure | `core` (L0), `l1`, `l2`, `l3`, `ingest` |
| Phone normalization | E.164 via `phonenumbers`, UK default for zero-prefix |
| Multi-person decomposition | Split on ` & `, link via `household_id` |
| Identity confidence | 5-tier scoring (1.0/0.7/0.3/0.1/0.0) |
| Victim protection | `suppress_from_public` flag, 566 records suppressed |
| Country codes | ISO 3166-1 alpha-2 |
| Name parsing | `probablepeople` library (CRF-based) |
| Entity resolution blocking | Soundex on surname + first name |

### Pending Decisions

- **Embedding model:** `all-MiniLM-L6-v2` (384-dim, fast) vs larger model (768-dim, better accuracy)
- **Entity resolution thresholds:** What similarity score triggers auto-match vs manual review?
- **IVFFlat lists:** How many lists for the vector index? (depends on data size)

## Blockers and Dependencies

### Current Blockers

- None

### Python Dependencies (M06)

```
sentence-transformers>=2.2.0
torch>=2.0.0  # or CPU-only version
```

## Database Connection

```
Host: 10.25.20.8
Port: 5432
Database: epsteinfiles_ard
Schemas: core, l1, l2, l3, ingest
Extensions: fuzzystrmatch, vector
```

## Notes for Next Session

M06 should start with sentence-transformers setup. The 384-dim model is probably sufficient for name matching—names are short strings and we're combining with Soundex blocking. Consider running embeddings on GPU node if available.

Key validation: After embedding, test retrieval for known entities. "Jeffrey Epstein" should cluster with "Jeff Epstein", "J. Epstein", etc.
