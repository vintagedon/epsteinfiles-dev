<!--
---
title: "Layer 0 Schemas"
description: "JSON Schema definitions for L0 canonical datasets"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: schema
  - layer: L0
---
-->

# Layer 0 Schemas

JSON Schema (draft-07) definitions for validating L0 canonical datasets.

---

## 1. Contents

```
schema/
├── flight-logs.schema.json    # 22-column flight log records
├── black-book.schema.json     # 17-column contact entries
└── README.md                  # This file
```

---

## 2. Schema Files

| Schema | Dataset | Columns | Records |
|--------|---------|---------|---------|
| [flight-logs.schema.json](flight-logs.schema.json) | Flight Logs | 22 | 5,001 |
| [black-book.schema.json](black-book.schema.json) | Black Book | 17 | 2,324 |

---

## 3. Validation

Run schema validation with:

```bash
# Validate all datasets
python pipelines/validation/validate_l0_schemas.py

# Validate specific dataset
python pipelines/validation/validate_l0_schemas.py --dataset flight
python pipelines/validation/validate_l0_schemas.py --dataset book

# Validate sample (faster)
python pipelines/validation/validate_l0_schemas.py --sample 100

# Output as JSON
python pipelines/validation/validate_l0_schemas.py --json
```

Requires: `pip install jsonschema`

---

## 4. Schema Design Principles

### Strictness Level: Moderate

- **Types enforced**: integers, strings, nullability
- **Formats validated**: UUID, URI (for provenance links)
- **Enums applied**: categorical fields (Known: Yes/No)
- **Patterns applied**: date format, tail numbers, passenger numbering
- **NOT enforced**: phone number formats, email formats (too messy from OCR)

### L1 Evolution

These L0 schemas preserve source structure. L1 processing will decompose records per GDR architecture:

| L0 Table | L1 Tables |
|----------|-----------|
| flight-logs | `flight_events` + `flight_passengers` + `identity_mentions` |
| black-book | `identity_mentions` + `contact_info` |

See `research/gdr-artifacts/epstein-schema-architecture.md` for full L1+ design.

---

## 5. Metadata Fields

Each schema includes `_meta` for operational context:

```json
"_meta": {
  "layer": "L0",
  "record_count": 5001,
  "source_hash": "...",
  "output_hash": "...",
  "created": "2026-02-01",
  "l1_evolution": "Description of L1 transformation"
}
```

---

## 6. Changelog

### 2026-02-01: Post-Audit Schema Patch

**Flight Logs Schema** patched based on Task 4.2 quality audit findings:

| Change | Before | After | Reason |
|--------|--------|-------|--------|
| Year maximum | 2003 | 2020 | Data extends through 2015 |
| Data Source | `const: "Flight Log"` | `enum: ["Flight Log", "FOIA"]` | 270 FOIA-sourced records |
| Aircraft Tail # | Pattern enforced | Pattern removed | 1 non-N-number (121TH) |
| Pass # | Pattern enforced | Pattern removed | "No Records" value in FOIA subset |

**Black Book Schema:** No changes required — validated 100% clean.

**Validation Results Post-Patch:**
- Flight Logs: 5,001/5,001 valid (100%)
- Black Book: 2,324/2,324 valid (100%)

See `research/quality-analysis/l0-quality-audit.md` for full audit report.

---

## 7. Related

| Document | Relationship |
|----------|--------------|
| [validate_l0_schemas.py](../../pipelines/validation/validate_l0_schemas.py) | Validation script |
| [flight-logs.csv](../flight-logs.csv) | Flight data |
| [black-book.csv](../black-book.csv) | Contact data |
| [architecture.md](../../.kilocode/rules/memory-bank/architecture.md) | Layer model |
