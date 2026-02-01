<!--
---
title: "Research"
description: "Source analysis, GDR artifacts, and investigation notes"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: research
---
-->

# Research

Source analysis, Gemini Deep Research artifacts, and investigation notes.

---

## 1. Contents

```
research/
├── gdr-artifacts/          # Gemini Deep Research prompts and outputs
├── source-analysis/        # Provenance documentation for source datasets
└── README.md               # This file
```

---

## 2. Purpose

This directory captures research artifacts that inform processing decisions:

| Folder | Purpose |
|--------|---------|
| [gdr-artifacts/](gdr-artifacts/) | Deep research outputs, synthesized patterns |
| [source-analysis/](source-analysis/) | Dataset provenance, quality assessments |

---

## 3. Current Documents

### Source Analysis

| Document | Dataset | Status |
|----------|---------|--------|
| [flight-logs-provenance.md](source-analysis/flight-logs-provenance.md) | Flight logs (5,001 records) | ✅ Complete |
| [black-book-provenance.md](source-analysis/black-book-provenance.md) | Black book (2,324 records) | ✅ Complete |

### GDR Artifacts

| Document | Topic | Status |
|----------|-------|--------|
| [epstein-schema-architecture.md](gdr-artifacts/epstein-schema-architecture.md) | L1+ schema patterns | ✅ Complete |

---

## 4. GDR Methodology

GDR prompts follow NSB (Negative Space Bounding) v0.4:

1. **Anchors** — Immutable context facts
2. **Walls** — Domain exclusions
3. **Gates** — Conditional inclusion criteria
4. **Questions** — Specific research questions
5. **Deliverables** — Expected outputs

See `/mnt/skills/user/gdr-prompt/SKILL.md` for full methodology.

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [L0 Schemas](../data/layer-0-canonical/schema/) | Schema definitions |
| [notebooks/](../notebooks/) | Exploratory analysis |
| [docs/case-study/](../docs/case-study/) | Methodology documentation |
