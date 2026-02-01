<!--
---
title: "Layer 0: Canonical"
description: "Cleaned, deduplicated records with uniform schema"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: data
---
-->

# Layer 0: Canonical

Cleaned, deduplicated records with uniform schema and provenance links.

---

## 1. Contents

```
layer-0-canonical/
├── flight_logs.parquet     # Normalized flight log entries
├── black_book.parquet      # Normalized contact entries
├── schema/                 # Schema definitions
│   ├── flight_log.json
│   └── contact.json
├── validation/             # Quality reports
│   └── l0_validation_report.md
└── README.md               # This file
```

---

## 2. What This Layer Provides

| Capability | Description |
|------------|-------------|
| Uniform Schema | All records follow defined structure |
| Deduplication | Exact duplicates removed |
| Provenance | Every record links to source file and page |
| Clean Text | OCR corrections, encoding normalization |

---

## 3. Query Patterns Enabled

- Basic filtering: "All flight logs from 2005"
- Joins: "Flight entries matching contact book names"
- Provenance lookup: "Which source file contains this record?"

---

## 4. Schema Overview

### Flight Log Entry

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | uuid | Unique identifier |
| `source_file` | string | Original PDF filename |
| `page_number` | int | Page in source |
| `date` | date | Flight date |
| `aircraft` | string | Aircraft identifier |
| `route_from` | string | Departure location |
| `route_to` | string | Arrival location |
| `passengers` | list[string] | Raw passenger names |
| `raw_text` | string | Original OCR text |

### Contact Entry

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | uuid | Unique identifier |
| `source_file` | string | Original filename |
| `page_number` | int | Page in source |
| `name` | string | Primary name |
| `phone_numbers` | list[string] | Phone numbers |
| `addresses` | list[string] | Addresses |
| `raw_text` | string | Original text |

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [raw/](../raw/) | Input to this layer |
| [layer-1-scalars/](../layer-1-scalars/) | Next processing stage |
| [pipelines/processing/](../../pipelines/processing/) | Transformation scripts |
