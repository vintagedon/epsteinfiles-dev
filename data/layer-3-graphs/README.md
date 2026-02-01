<!--
---
title: "Layer 3: Graphs"
description: "Entity resolution and relationship structures"
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

# Layer 3: Graphs

Resolved entities and relationship structures enabling network analysis.

---

## 1. Contents

```
layer-3-graphs/
├── resolved_entities/      # Deduplicated entity records
│   └── canonical_entities.parquet
├── relationships/          # Typed edges between entities
│   └── relationships.parquet
├── networks/               # Pre-computed graph structures
│   ├── cooccurrence.graphml
│   └── temporal.graphml
├── resolution_log/         # Entity merge decisions
│   └── merge_log.parquet
├── validation/
│   └── l3_validation_report.md
└── README.md               # This file
```

---

## 2. What This Layer Provides

| Capability | Description |
|------------|-------------|
| Entity Resolution | "J.E.", "Jeffrey", "Epstein" → single canonical entity |
| Relationship Typing | Co-occurrence vs. explicit mention vs. inferred |
| Temporal Graphs | When relationships appear in the record |
| Merge Provenance | Which mentions were unified and why |

---

## 3. Query Patterns Enabled

- Network traversal: "Who is connected to Person X within 2 hops?"
- Path finding: "Connection path between Person A and Person B"
- Centrality: "Most connected entities"
- Temporal: "Relationships active in 2005"
- Cross-source: "Who appears in both flight logs and black book?"

---

## 4. Graph Schema

### Canonical Entity

| Field | Type | Description |
|-------|------|-------------|
| `canonical_id` | uuid | Resolved entity identifier |
| `canonical_name` | string | Best name form |
| `entity_type` | enum | person, organization, location |
| `source_entities` | list[uuid] | L1 entities merged into this |
| `confidence` | float | Resolution confidence |
| `attributes` | dict | Merged attributes |

### Relationship

| Field | Type | Description |
|-------|------|-------------|
| `relationship_id` | uuid | Unique identifier |
| `source_entity` | uuid | From entity |
| `target_entity` | uuid | To entity |
| `relationship_type` | enum | cooccurrence, mentioned_with, flight_together, etc. |
| `weight` | float | Strength (e.g., mention count) |
| `first_seen` | date | Earliest evidence |
| `last_seen` | date | Latest evidence |
| `evidence` | list[uuid] | Records supporting this relationship |

---

## 5. Resolution Approach

Entity resolution uses multiple signals:

1. **String similarity**: Edit distance, phonetic matching
2. **Embedding similarity**: L2 entity vectors
3. **Context overlap**: Shared co-mentions
4. **Manual review**: Flagged ambiguous cases

All merge decisions are logged with rationale for auditability.

---

## 6. Related

| Document | Relationship |
|----------|--------------|
| [layer-2-vectors/](../layer-2-vectors/) | Input to this layer |
| [pipelines/processing/](../../pipelines/processing/) | Resolution scripts |
| [architecture.md](../../.kilocode/rules/memory-bank/architecture.md) | Full schema details |
