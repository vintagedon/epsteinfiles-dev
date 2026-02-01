<!--
---
title: "Processing Pipelines"
description: "Scripts for transforming data between ARD layers"
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

# Processing Pipelines

Scripts for transforming data between ARD layers: raw → L0 → L1 → L2 → L3.

---

## 1. Contents

```
processing/
├── layer_0_canonical.py    # Raw → cleaned, schema'd records
├── layer_1_entities.py     # L0 → entity extraction
├── layer_1_classify.py     # L0 → document classification
├── layer_2_embed.py        # L1 → embeddings
├── layer_3_resolve.py      # L2 → entity resolution
├── layer_3_relationships.py # L2 → relationship extraction
└── README.md               # This file
```

---

## 2. Scripts

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `layer_0_canonical.py` | `data/raw/` | `data/layer-0-canonical/` | Parse, clean, apply schema |
| `layer_1_entities.py` | L0 records | `data/layer-1-scalars/entities/` | NER extraction |
| `layer_1_classify.py` | L0 records | `data/layer-1-scalars/classifications/` | Document typing |
| `layer_2_embed.py` | L1 records | `data/layer-2-vectors/` | Generate embeddings |
| `layer_3_resolve.py` | L1 entities | `data/layer-3-graphs/resolved_entities/` | Merge duplicate entities |
| `layer_3_relationships.py` | Resolved entities | `data/layer-3-graphs/relationships/` | Extract relationships |

---

## 3. Usage Pattern

```bash
# Process layer by layer
python pipelines/processing/layer_0_canonical.py
python pipelines/validation/validate_layer_0.py

python pipelines/processing/layer_1_entities.py
python pipelines/processing/layer_1_classify.py
python pipelines/validation/validate_layer_1.py

# Continue through layers...
```

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [ingestion/](../ingestion/) | Previous stage |
| [validation/](../validation/) | Quality checks |
| [data/](../../data/) | Output destination |
