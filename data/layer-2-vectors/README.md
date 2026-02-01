<!--
---
title: "Layer 2: Vectors"
description: "Embedding representations for similarity search"
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

# Layer 2: Vectors

Embedding representations enabling similarity search and semantic clustering.

---

## 1. Contents

```
layer-2-vectors/
├── record_embeddings/      # Document-level embeddings
│   └── records.parquet     # record_id + vector
├── chunk_embeddings/       # Chunk-level for long documents
│   └── chunks.parquet      # chunk_id + record_id + vector
├── entity_embeddings/      # Entity description embeddings
│   └── entities.parquet    # entity_id + vector
├── metadata/
│   ├── model_info.json     # Embedding model details
│   └── chunking_config.json
├── validation/
│   └── l2_validation_report.md
└── README.md               # This file
```

---

## 2. What This Layer Provides

| Capability | Description |
|------------|-------------|
| Record Vectors | One embedding per L0 record |
| Chunk Vectors | Multiple embeddings for longer content |
| Entity Vectors | Embeddings of entity descriptions |
| Model Provenance | Which model, which version |

---

## 3. Query Patterns Enabled

- Similarity search: "Documents similar to this one"
- Semantic clustering: "Group documents by topic"
- Anomaly detection: "Records unlike typical patterns"
- Cross-modal: "Entities similar to this description"

---

## 4. Embedding Schema

### Record Embedding

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | uuid | Link to L0 record |
| `embedding` | vector(dim) | Dense representation |
| `model` | string | Model identifier |
| `created_at` | timestamp | Generation time |

### Chunk Embedding

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | uuid | Unique identifier |
| `record_id` | uuid | Parent record |
| `chunk_index` | int | Position in record |
| `text` | string | Chunk content |
| `embedding` | vector(dim) | Dense representation |

---

## 5. Storage Notes

Vector data is large. Options:

- **Parquet files**: For export/portability
- **pgvector**: For live similarity queries
- **Both**: Parquet as source of truth, pgvector as query layer

---

## 6. Related

| Document | Relationship |
|----------|--------------|
| [layer-1-scalars/](../layer-1-scalars/) | Input to this layer |
| [layer-3-graphs/](../layer-3-graphs/) | Next processing stage |
| [tech.md](../../.kilocode/rules/memory-bank/tech.md) | Embedding model details |
