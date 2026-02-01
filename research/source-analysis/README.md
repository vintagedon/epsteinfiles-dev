<!--
---
title: "Source Analysis"
description: "Provenance documentation and quality assessments for source datasets"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: research
---
-->

# Source Analysis

Provenance documentation and quality assessments for each source dataset entering the ARD pipeline.

---

## 1. Contents

```
source-analysis/
├── flight-logs-provenance.md   # Flight logs: Internet Archive → L0
├── black-book-provenance.md    # Black book: epsteinsblackbook.com → L0 (pending)
└── README.md                   # This file
```

---

## 2. Purpose

Each provenance document captures:

| Section | Content |
|---------|---------|
| Source Identification | Origin, URL, legal case reference |
| Provenance Chain | Path from original to L0 |
| File Hashes | SHA-256 at each transformation |
| Extraction Metrics | Record counts, coverage, quality |
| Schema | Column definitions |
| Data Quality Notes | Strengths and limitations |

---

## 3. Documents

| Document | Dataset | Status |
|----------|---------|--------|
| [flight-logs-provenance.md](flight-logs-provenance.md) | Flight logs (5,001 records) | ✅ Complete |
| [black-book-provenance.md](black-book-provenance.md) | Black book (2,324 records) | ✅ Complete |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [data/raw/](../../data/raw/) | Source files |
| [data/layer-0-canonical/](../../data/layer-0-canonical/) | Processed outputs |
| [pipelines/processing/](../../pipelines/processing/) | Extraction scripts |
