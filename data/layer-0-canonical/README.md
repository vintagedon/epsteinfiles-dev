<!--
---
title: "Layer 0: Canonical"
description: "Cleaned, deduplicated records with uniform schema and provenance"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: data
  - layer: L0
---
-->

# Layer 0: Canonical

Cleaned, deduplicated records with validated schemas and provenance links.

---

## 1. Contents

```
layer-0-canonical/
├── flight-logs.csv         # 5,001 flight log entries
├── black-book.csv          # 2,324 contact entries
├── schema/                 # JSON Schema definitions
│   ├── flight-logs.schema.json
│   ├── black-book.schema.json
│   └── README.md
└── README.md               # This file
```

---

## 2. Datasets

| Dataset | Records | Columns | Coverage |
|---------|---------|---------|----------|
| [flight-logs.csv](flight-logs.csv) | 5,001 | 22 | 1995 – 2015 |
| [black-book.csv](black-book.csv) | 2,324 | 17 | 95 pages |

---

## 3. What This Layer Provides

| Capability | Description |
|------------|-------------|
| Validated Schema | JSON Schema draft-07 definitions |
| Deduplication | Exact duplicates removed (3 from black book) |
| Provenance | SHA-256 chains to source files |
| Deterministic IDs | Reproducible UUIDs from row content |

---

## 4. Schema Validation

```bash
# Validate both datasets
python pipelines/validation/validate_l0_schemas.py

# Validate specific dataset
python pipelines/validation/validate_l0_schemas.py --dataset flight
python pipelines/validation/validate_l0_schemas.py --dataset book
```

See [schema/README.md](schema/README.md) for schema documentation.

---

## 5. Provenance

| Dataset | Source | Documentation |
|---------|--------|---------------|
| Flight Logs | Internet Archive (Bradley Edwards exhibits) | [flight-logs-provenance.md](../../research/source-analysis/flight-logs-provenance.md) |
| Black Book | epsteinsblackbook.com (Wayback Machine) | [black-book-provenance.md](../../research/source-analysis/black-book-provenance.md) |

---

## 6. L1 Evolution

L0 preserves source structure. L1 processing will decompose per [GDR architecture](../../research/gdr-artifacts/epstein-schema-architecture.md):

| L0 Table | L1 Tables |
|----------|-----------|
| flight-logs | `flight_events` + `flight_passengers` + `identity_mentions` |
| black-book | `identity_mentions` + `contact_info` |

---

## 7. Related

| Document | Relationship |
|----------|--------------|
| [raw/](../raw/) | Input source files |
| [schema/](schema/) | JSON Schema definitions |
| [pipelines/processing/](../../pipelines/processing/) | Extraction scripts |
| [pipelines/validation/](../../pipelines/validation/) | Validation scripts |
