<!--
---
title: "Validation Pipelines"
description: "Quality gates and schema validation scripts"
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

# Validation Pipelines

Quality gates ensuring each layer meets schema and quality requirements before proceeding.

---

## 1. Contents

```
validation/
├── validate_layer_0.py     # Schema conformance, completeness
├── validate_layer_1.py     # Entity quality, coverage
├── validate_layer_2.py     # Embedding integrity
├── validate_layer_3.py     # Graph consistency
├── validate_provenance.py  # Source linkage verification
└── README.md               # This file
```

---

## 2. Scripts

| Script | Checks | Output |
|--------|--------|--------|
| `validate_layer_0.py` | Schema match, required fields, provenance links | `data/layer-0-canonical/validation/` |
| `validate_layer_1.py` | Entity coverage, confidence thresholds | `data/layer-1-scalars/validation/` |
| `validate_layer_2.py` | Vector dimensions, null checks | `data/layer-2-vectors/validation/` |
| `validate_layer_3.py` | Graph connectivity, orphan detection | `data/layer-3-graphs/validation/` |
| `validate_provenance.py` | Every record traces to source | Project-wide report |

---

## 3. Quality Gates

Each layer must pass validation before downstream processing:

| Check | Threshold | Action on Failure |
|-------|-----------|-------------------|
| Schema conformance | 100% | Block |
| Required fields populated | 100% | Block |
| Provenance links valid | 100% | Block |
| Entity extraction confidence | >80% mean | Warning |
| Embedding completeness | 100% | Block |

---

## 4. Usage

```bash
# Validate after processing
python pipelines/validation/validate_layer_0.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "Layer 0 validated, proceeding to Layer 1"
else
    echo "Validation failed, review report"
fi
```

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [processing/](../processing/) | Produces data to validate |
| [tasks.md](../../.kilocode/rules/memory-bank/tasks.md) | Quality checklist definitions |
