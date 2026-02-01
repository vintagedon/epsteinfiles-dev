<!--
---
title: "Pipelines"
description: "Data processing scripts for ingestion, transformation, and validation"
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

# Pipelines

Data processing scripts organized by function: ingestion, processing, and validation.

---

## 1. Contents

```
pipelines/
├── ingestion/              # Data acquisition scripts
├── processing/             # Layer transformation scripts
├── validation/             # Quality check scripts
└── README.md               # This file
```

---

## 2. Subdirectories

| Directory | Purpose |
|-----------|---------|
| [ingestion/](ingestion/) | Download source files, generate checksums, document provenance |
| [processing/](processing/) | Transform data between layers (L0→L1→L2→L3) |
| [validation/](validation/) | Quality gates, schema validation, sanity checks |

---

## 3. Pipeline Conventions

All scripts follow common patterns:

- **Idempotent**: Safe to re-run without side effects
- **Logged**: Output includes timestamps and record counts
- **Validated**: Input checks before processing
- **Documented**: Script headers explain purpose and usage

---

## 4. Execution Order

```
ingestion/acquire_*.py     →  data/raw/
processing/layer_0_*.py    →  data/layer-0-canonical/
processing/layer_1_*.py    →  data/layer-1-scalars/
processing/layer_2_*.py    →  data/layer-2-vectors/
processing/layer_3_*.py    →  data/layer-3-graphs/
```

Run validation scripts after each layer completes.

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [data/](../data/) | Output destination |
| [tech.md](../.kilocode/rules/memory-bank/tech.md) | Environment setup |
| [tasks.md](../.kilocode/rules/memory-bank/tasks.md) | Workflow documentation |
