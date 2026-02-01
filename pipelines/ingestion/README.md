<!--
---
title: "Ingestion Pipelines"
description: "Scripts for acquiring source data from DOJ and other official releases"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: pipelines
---
-->

# Ingestion Pipelines

Scripts for acquiring source data from the DOJ Epstein Library and other official releases.

---

## 1. Contents

```
ingestion/
├── acquire_flight_logs.py  # Download flight log PDFs
├── acquire_black_book.py   # Download contact book
├── generate_checksums.py   # SHA-256 for all files
├── update_manifest.py      # Update provenance documentation
└── README.md               # This file
```

---

## 2. Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `acquire_flight_logs.py` | Download flight log parts from DOJ | `data/raw/flight-logs/` |
| `acquire_black_book.py` | Download contact book | `data/raw/black-book/` |
| `generate_checksums.py` | Create SHA-256 checksums | `checksums.sha256` per batch |
| `update_manifest.py` | Document provenance | `data/raw/MANIFEST.md` |

---

## 3. Usage

```bash
# Acquire flight logs
python pipelines/ingestion/acquire_flight_logs.py

# Generate checksums for new batch
python pipelines/ingestion/generate_checksums.py --batch flight-logs

# Update manifest
python pipelines/ingestion/update_manifest.py
```

---

## 4. Provenance Requirements

Every acquisition must capture:

- Source URL
- Download timestamp
- HTTP response headers (for caching/versioning)
- File checksums
- Any errors encountered

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [data/raw/](../../data/raw/) | Output destination |
| [processing/](../processing/) | Next stage |
