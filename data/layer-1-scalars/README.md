<!--
---
title: "Layer 1: Scalars"
description: "Derived quantities: entities, classifications, temporal markers"
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

# Layer 1: Scalars

Derived quantities computed from Layer 0: extracted entities, document classifications, temporal markers.

---

## 1. Contents

```
layer-1-scalars/
├── entities/               # Extracted named entities
│   ├── persons.parquet
│   ├── organizations.parquet
│   └── locations.parquet
├── classifications/        # Document type labels
│   └── doc_types.parquet
├── temporal/               # Date extractions and normalizations
│   └── timeline.parquet
├── mentions/               # Entity-to-record linkages
│   └── entity_mentions.parquet
├── validation/
│   └── l1_validation_report.md
└── README.md               # This file
```

---

## 2. What This Layer Provides

| Capability | Description |
|------------|-------------|
| Named Entities | People, organizations, locations extracted via NER |
| Document Types | Classification (flight log, contact entry, etc.) |
| Temporal Markers | Normalized dates, date ranges |
| Mention Links | Which entities appear in which records |

---

## 3. Query Patterns Enabled

- Faceted search: "All documents mentioning Person X"
- Time filtering: "Activity between Jan-Mar 2005"
- Type filtering: "Only flight logs"
- Co-mention: "Documents mentioning both Person X and Person Y"

---

## 4. Entity Schema

### Person Entity

| Field | Type | Description |
|-------|------|-------------|
| `entity_id` | uuid | Unique identifier |
| `surface_forms` | list[string] | All name variants found |
| `mention_count` | int | Number of mentions |
| `first_seen` | date | Earliest mention date |
| `last_seen` | date | Latest mention date |
| `confidence` | float | Extraction confidence |

### Entity Mention

| Field | Type | Description |
|-------|------|-------------|
| `mention_id` | uuid | Unique identifier |
| `entity_id` | uuid | Link to entity |
| `record_id` | uuid | Link to L0 record |
| `surface_form` | string | Text as it appeared |
| `context` | string | Surrounding text |
| `position` | int | Character offset |

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [layer-0-canonical/](../layer-0-canonical/) | Input to this layer |
| [layer-2-vectors/](../layer-2-vectors/) | Next processing stage |
| [pipelines/processing/](../../pipelines/processing/) | Transformation scripts |
