<!--
---
title: "Data"
description: "ARD layer outputs and raw source files"
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

# Data

Storage for all ARD layers, from raw source files through processed outputs.

---

## 1. Contents

```
data/
├── raw/                    # Original DOJ files (gitignored)
├── layer-0-canonical/      # Cleaned, deduplicated, uniform schema
├── layer-1-scalars/        # Derived quantities (entities, classifications)
├── layer-2-vectors/        # Embeddings
├── layer-3-graphs/         # Relationship structures
└── README.md               # This file
```

---

## 2. Layer Progression

| Layer | Contents | Query Patterns Enabled |
|-------|----------|------------------------|
| [raw/](raw/) | Source files as acquired | Provenance verification |
| [layer-0-canonical/](layer-0-canonical/) | Cleaned, schema'd records | Basic filtering, joins |
| [layer-1-scalars/](layer-1-scalars/) | Entities, doc types, dates | Physics-based selection |
| [layer-2-vectors/](layer-2-vectors/) | Embeddings | Similarity search |
| [layer-3-graphs/](layer-3-graphs/) | Relationships | Network queries |

Each layer builds on the one below.

---

## 3. Storage Strategy

| Layer | Format | Git Status | Reasoning |
|-------|--------|------------|-----------|
| raw | Original (PDF, images) | .gitignored | Large, reproducible from source |
| layer-0 | Parquet/CSV | Committed or LFS | Version-controlled outputs |
| layer-1 | Parquet + PostgreSQL | Committed + cluster | SQL query patterns |
| layer-2 | PostgreSQL + pgvector | Cluster only | Vector search requires DB |
| layer-3 | PostgreSQL | Cluster only | Graph queries |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent |
| [Pipelines](../pipelines/) | Processing scripts |
| [Architecture](../.kilocode/rules/memory-bank/architecture.md) | Schema definitions |
