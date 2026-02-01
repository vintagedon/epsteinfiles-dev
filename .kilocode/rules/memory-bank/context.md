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
- **M04 complete: Layer 0 Validation**
  - Task 4.1: JSON Schema definitions for both datasets
  - Task 4.2: Quality audit with comprehensive findings
  - Task 4.3: Schema patches applied, L1 transformation plan documented
  - **Validation: 100% pass rate on both datasets**

### Current Phase

**Milestone 04 COMPLETE.** Ready for M05: Layer 1 Scalars.

### Active Work

Next session should begin M05.

## M04 Deliverables Summary

| Artifact | Path |
|----------|------|
| Flight logs schema | `data/layer-0-canonical/schema/flight-logs.schema.json` |
| Black book schema | `data/layer-0-canonical/schema/black-book.schema.json` |
| Schema validation script | `pipelines/validation/validate_l0_schemas.py` |
| Quality audit script | `pipelines/validation/quality_audit_l0.py` |
| Quality audit report | `research/quality-analysis/l0-quality-audit.md` |
| Audit metrics JSON | `research/quality-analysis/l0-audit-metrics.json` |
| **L1 transformation plan** | `docs/l1-transformation-plan.md` |

## Next Steps

### Immediate (M05: Layer 1 Scalars)

Per `docs/l1-transformation-plan.md`:

1. **Task 5.1: Entity extraction pipeline**
   - Install `probablepeople` for name parsing
   - Create `l1.identity_mentions` table
   - Parse all names from both datasets
   
2. **Task 5.2: Date and location normalization**
   - Flight dates to ISO 8601
   - Airport code lookup table
   - Country standardization to ISO 3166-1

3. **Task 5.3: Contact normalization**
   - Phone normalization with `phonenumbers` library
   - Multi-person entry decomposition
   - Entity type classification

### Near-Term (M05-M06)

- PostgreSQL table creation from schemas
- Import L0 CSVs to database
- Entity resolution candidate generation (Soundex + pgvector)

### Future / Backlog

- M06: Layer 2 vector embeddings (pgvector + sentence-transformers)
- M07: Layer 3 graph relationships (recursive CTEs per GDR)
- M08: Web interface at epsteinfiles.dev with K-anonymity views

## Active Decisions

### Approved Decisions (from M04)

| Decision | Details |
|----------|---------|
| Phone normalization | E.164 via `phonenumbers`, UK default for zero-prefix |
| Multi-person decomposition | Split on ` & `, link via `household_id` |
| Identity confidence | 5-tier scoring (1.0/0.7/0.3/0.1/0.0) |
| Victim protection | `suppress_from_public` flag, K-anonymity views |
| Country codes | ISO 3166-1 alpha-2, preserve raw values |
| Name parsing | `probablepeople` library (CRF-based) |

### Pending Decisions

- **Entity resolution thresholds:** What similarity score triggers auto-match vs manual review?
- **Vector embedding model:** `all-MiniLM-L6-v2` vs larger model? Trade-off: speed vs accuracy.

## Blockers and Dependencies

### Current Blockers

- None

### External Dependencies

- PostgreSQL instance for L1+ processing (cluster resource)

### Python Dependencies (M05)

```
probablepeople>=0.5.5
phonenumbers>=8.13.0
python-Levenshtein>=0.21.0
```

## Layer 0 Final Status

| Dataset | Records | Schema Valid | Quality Issues Documented |
|---------|---------|--------------|---------------------------|
| Flight Logs | 5,001 | ✅ 100% | Yes — see audit report |
| Black Book | 2,324 | ✅ 100% | Yes — see audit report |

## Key Quality Findings (Reference)

**Flight Logs:**
- 17.7% unidentified passengers (initials, "Female (1)", "?")
- 270 FOIA records with different conventions
- 6 unique aircraft, N908JE dominant (74%)

**Black Book:**
- 293 multi-person entries (12.6%)
- 226 likely organizations (9.7%)
- 6+ phone formats, 958 multi-number fields
- 28 country variations

All findings documented in `research/quality-analysis/l0-quality-audit.md` with remediation proposals in `docs/l1-transformation-plan.md`.

## Notes for Next Session

M05 should begin with PostgreSQL setup. Check cluster availability. The L1 transformation plan has implementation priority rankings — start with high-priority items (identity confidence, date normalization, name parsing).
