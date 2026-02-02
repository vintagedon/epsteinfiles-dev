# M05: Layer 1 Scalars

**Status:** ✅ Complete  
**Sessions:** 1  
**Date Range:** 2026-02-01  
**Branch:** main (direct commits during active development phase)

---

## Summary

Milestone 05 established the Layer 1 scalar infrastructure: PostgreSQL database, normalized tables, and unified identity mentions for entity resolution. All L1 transforms from the M04 transformation plan were implemented. Validation confirms 100% L0→L1 completeness with strong cross-dataset signal (22 exact name matches, 134 Soundex blocks).

---

## Work Completed

| Task | Description | Deliverables |
|------|-------------|--------------|
| 5.1 | Database setup + L0 import | Database created, schemas, CSV import |
| 5.2 | Flight logs L1 transforms | FL-1 through FL-4, victim protection |
| 5.3 | Black book L1 transforms | BB-1 through BB-4, phone normalization |
| 5.4 | Unified identity mentions | Name parsing with probablepeople, Soundex |
| 5.5 | Validation + DDL scripts | Validation suite, reproducible DDL |

---

## Deliverables

### Database Infrastructure

| Component | Details |
|-----------|---------|
| Database | `epsteinfiles_ard` on pgsql01 (10.25.20.8) |
| Schemas | `core`, `l1`, `l2`, `l3`, `ingest` |
| Extensions | `fuzzystrmatch`, `vector` |

### Pipeline Scripts

| File | Description |
|------|-------------|
| `pipelines/ingestion/import_l0_to_postgres.py` | L0 CSV import with batch processing |
| `pipelines/processing/transform_flight_logs_l1.py` | FL-1 through FL-4 transforms |
| `pipelines/processing/transform_black_book_l1.py` | BB-1 through BB-4 transforms |
| `pipelines/processing/build_identity_mentions.py` | Unified name parsing + Soundex |
| `pipelines/validation/validate_l1.py` | Comprehensive L1 quality checks |
| `pipelines/ddl/create_epsteinfiles_db.sql` | Reproducible database DDL |

### Configuration & Metrics

| File | Description |
|------|-------------|
| `.env` | Project environment (gitignored) |
| `research/quality-analysis/l1-metrics.json` | Machine-readable validation metrics |

---

## Database Schema (L1)

### Tables Created

| Table | Records | Purpose |
|-------|---------|---------|
| `l1.flight_events` | 1,491 | Deduplicated flights (by date/tail/route) |
| `l1.flight_passengers` | 5,001 | One per L0 record, with confidence + victim flags |
| `l1.contacts` | 2,324 | One per L0 black book, with entity type |
| `l1.contact_persons` | 2,610 | Decomposed multi-person entries |
| `l1.phone_numbers` | 5,585 | Normalized to E.164 where possible |
| `l1.identity_mentions` | 6,783 | Unified for entity resolution |

### Views Created

| View | Purpose |
|------|---------|
| `l1.flight_passengers_public` | Excludes suppressed records (victim protection) |

---

## Transformation Results

### Flight Logs (FL-1 through FL-4)

| Transform | Metric | Result |
|-----------|--------|--------|
| FL-1: Identity confidence | Distribution | 1.0: 4,118 / 0.7: 128 / 0.3: 189 / 0.1: 128 / 0.0: 438 |
| FL-2: Victim protection | Suppressed | 566 (11.3%) |
| FL-3: Date normalization | ISO 8601 | All dates converted |
| FL-4: Name parsing | To identity_mentions | 4,435 records (conf ≥ 0.3) |

### Black Book (BB-1 through BB-4)

| Transform | Metric | Result |
|-----------|--------|--------|
| BB-1: Multi-person decomposition | Records created | 2,610 (from 2,324 L0) |
| BB-2: Phone normalization | E.164 valid | 2,633 / 5,585 (47.1%) |
| BB-3: Country standardization | ISO mapped | 1,525 (100% of non-null) |
| BB-4: Entity classification | Distribution | individual: 1,777 / household: 289 / org: 226 / unknown: 32 |

### Identity Mentions

| Metric | Value |
|--------|-------|
| Total mentions | 6,783 |
| From flight_passengers | 4,435 |
| From contact_persons | 2,348 |
| With Soundex codes | 6,526 |
| Unique Soundex blocks | 885 |
| Avg mentions per block | 7.4 |

---

## Cross-Dataset Signal

| Metric | Value | Significance |
|--------|-------|--------------|
| Exact name matches | 22 | Direct entity links possible |
| Overlapping Soundex | 134 | Resolution candidate blocks |
| Parse confidence ≥ 0.9 | 5,576 (82%) | High-quality parsing |

---

## Technical Decisions

### Data Quality Finding

**`Unique ID` column in flight logs is not unique.** Four values have collisions (12 total rows affected). Different passengers share identical composite IDs due to source data issues. Solution: Use `ID` as primary key instead.

| Duplicate Unique ID | Rows | Example |
|--------------------|------|---------|
| 37137-B-727-31-N908JE-TIST-HPN-11-Pass 1 | 6 | 6 different passengers |
| 36244-G-1159B-N908JE-TEB-PBI-1215-Pass 6 | 2 | Jordan Dubin + Nanny (1) |
| 37307-B-727-31-N908JE-JFK-MRY-66-Pass 7 | 2 | David Rockwell + Richard ? |
| 37934-B-727-31H-N908JE-ZUUU-ZBAA-231-Pass 10 | 2 | Joe Novich + Secret Service (4) |

### Phone Validation Rate

47.1% E.164 validation is lower than ideal but expected given:
- Source data has 6+ format variations
- Many numbers lack country context
- Historical numbers may no longer be valid

The `raw_value` is always preserved for reference.

---

## Validation Performed

```bash
# L0 Import
python pipelines/ingestion/import_l0_to_postgres.py --create-db
# Result: 5,001 flight logs + 2,324 black book imported

# Flight Logs Transform
python pipelines/processing/transform_flight_logs_l1.py
# Result: 1,491 flights, 5,001 passengers, 566 suppressed

# Black Book Transform
python pipelines/processing/transform_black_book_l1.py
# Result: 2,324 contacts, 2,610 persons, 5,585 phones

# Identity Mentions
python pipelines/processing/build_identity_mentions.py
# Result: 6,783 mentions, 885 Soundex blocks

# Full Validation
python pipelines/validation/validate_l1.py
# Result: All checks pass, metrics exported
```

---

## Files Created

### Pipelines
- `pipelines/ingestion/import_l0_to_postgres.py`
- `pipelines/processing/transform_flight_logs_l1.py`
- `pipelines/processing/transform_black_book_l1.py`
- `pipelines/processing/build_identity_mentions.py`
- `pipelines/validation/validate_l1.py`
- `pipelines/ddl/create_epsteinfiles_db.sql`

### Configuration
- `.env` (gitignored)

### Research
- `research/quality-analysis/l1-metrics.json`

### Documentation
- `work-logs/05-layer-1-scalars/README.md`
- `scratch/m05-tracking.md` (gitignored)

### Modified
- `.kilocode/rules/memory-bank/context.md`

---

## Dependencies Added

```
probablepeople>=0.5.5
phonenumbers>=8.13.0
python-Levenshtein>=0.21.0
psycopg[binary]>=3.0
python-dotenv>=1.0.0
```

---

## Next Steps (M06)

1. **Embedding model setup** — Install sentence-transformers, select model
2. **Generate name embeddings** — Embed 6,783 identity mentions
3. **Entity resolution candidates** — Combine Soundex + vector similarity
4. **Threshold tuning** — Evaluate precision/recall on known entities

---

## References

- [L1 Transformation Plan](../../docs/l1-transformation-plan.md)
- [L1 Validation Metrics](../../research/quality-analysis/l1-metrics.json)
- [DDL Script](../../pipelines/ddl/create_epsteinfiles_db.sql)
- [Memory Bank Context](../../.kilocode/rules/memory-bank/context.md)
