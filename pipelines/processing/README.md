<!--
---
title: "Processing Pipelines"
description: "Scripts for transforming data between ARD layers"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: pipelines
---
-->

# Processing Pipelines

Scripts for transforming data between ARD layers: raw → L0 → L1 → L2 → L3.

---

## 1. Contents

```
processing/
├── extract_flight_logs.py      # PDF → L0 flight logs CSV
├── normalize_black_book.py     # Raw CSV → L0 black book CSV
├── README.md                   # This file
└── (future L1-L3 scripts)
```

---

## 2. Current Scripts

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `extract_flight_logs.py` | `data/raw/epstein-flight-logs-unredacted.pdf` | `data/layer-0-canonical/flight-logs.csv` | Extract tabular flight data with pdfplumber |
| `normalize_black_book.py` | `data/raw/epsteinsblackbook-com/black-book-lines.csv` | `data/layer-0-canonical/black-book.csv` | Dedupe, add record_id, validate schema |

---

## 3. Usage

### Layer 0 Extraction

```bash
# Flight logs (requires pdfplumber)
python pipelines/processing/extract_flight_logs.py

# Black book
python pipelines/processing/normalize_black_book.py

# Verify existing outputs without re-processing
python pipelines/processing/extract_flight_logs.py --verify-only
python pipelines/processing/normalize_black_book.py --verify-only
```

### Script Features

Both L0 scripts include:
- SHA-256 hash computation for input/output provenance
- Schema validation with expected column checks
- Metrics reporting (record counts, coverage percentages)
- `--verify-only` flag for reproducibility verification

---

## 4. Planned Scripts

| Script | Layer | Purpose |
|--------|-------|---------|
| `layer_1_entities.py` | L0 → L1 | NER extraction |
| `layer_1_classify.py` | L0 → L1 | Document classification |
| `layer_2_embed.py` | L1 → L2 | Generate embeddings |
| `layer_3_resolve.py` | L2 → L3 | Entity resolution |
| `layer_3_relationships.py` | L2 → L3 | Relationship extraction |

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [research/source-analysis/](../../research/source-analysis/) | Provenance documentation |
| [data/layer-0-canonical/](../../data/layer-0-canonical/) | L0 outputs |
| [validation/](../validation/) | Quality checks |
