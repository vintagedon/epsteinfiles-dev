<!--
---
title: "Black Book Source Provenance"
description: "Provenance chain and quality assessment for black book contact dataset"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: provenance
  - domain: black-book
  - layer: L0
---
-->

# Black Book Source Provenance

Complete provenance chain from original scanned images to Layer 0 canonical dataset.

---

## 1. Source Identification

| Attribute | Value |
|-----------|-------|
| Title | Epstein's Black Book (Unredacted) |
| Intermediary | epsteinsblackbook.com (extraction) |
| Original Images | Wayback Machine archived scans |
| Coverage | 95 pages of contact entries |
| Content Type | Personal contact book / address book |

---

## 2. Provenance Chain

```
Original Scanned Images
    ↓
Wayback Machine Archive (per-page URLs in Page-Link column)
    ↓
epsteinsblackbook.com extraction (black-book-lines.csv)
    ↓
Local Raw: data/raw/epsteinsblackbook-com/black-book-lines.csv
    ↓
Layer 0: data/layer-0-canonical/black-book.csv
```

**Note:** Each record contains a `Page-Link` column with the Wayback Machine URL for the source image, providing row-level provenance.

---

## 3. File Hashes

| File | SHA-256 |
|------|---------|
| `black-book-lines.csv` (source) | `4574d246daf6a3a85522923290440c31d954ea651ee39d19cfc292b231abb957` |
| `black-book.csv` (L0) | `2ab191865205df4998e888023bb5a669f757faaa7a54abd5993943cbe6eac4ec` |

---

## 4. Normalization Metrics

| Metric | Value |
|--------|-------|
| Source Records | 2,327 |
| Duplicates Removed | 3 |
| L0 Records | 2,324 |
| Unique Names | 1,667 |
| Unique Surnames | 1,287 |
| Page Range | 1 – 95 |

---

## 5. Data Completeness

| Field | Coverage |
|-------|----------|
| Phone (any) | 2,240 (96.4%) |
| Address | 1,377 (59.3%) |
| Email | 406 (17.5%) |
| Page-Link (provenance) | 100% |

---

## 6. Geographic Distribution

| Country | Records |
|---------|---------|
| US | 910 |
| Unknown | 799 |
| UK | 381 |
| France | 135 |
| Spain | 16 |

---

## 7. Schema (17 Columns)

| Column | Type | Description |
|--------|------|-------------|
| record_id | uuid | L0 unique identifier (added) |
| Page | int | Source page number |
| Page-Link | url | Wayback Machine image URL |
| Name | string | Display name |
| Company/Add. Text | string | Company or additional context |
| Surname | string | Parsed surname |
| First Name | string | Parsed first name |
| Address-Type | string | Address category |
| Address | string | Street address |
| Zip | string | Postal code |
| City | string | City |
| Country | string | Country |
| Phone (no specifics) | string | General phone |
| Phone (w) – work | string | Work phone |
| Phone (h) – home | string | Home phone |
| Phone (p) – portable/mobile | string | Mobile phone |
| Email | string | Email address |

---

## 8. Data Quality Notes

**Strengths:**
- High phone coverage (96%)
- Row-level provenance via Page-Link
- Pre-parsed name fields (Surname, First Name)
- Complete page coverage (1-95)

**Limitations:**
- 799 records missing country (34%)
- Email coverage low (17%)
- Third-party extraction (epsteinsblackbook.com) - not independently verified against source images
- Some entries are organizations/services, not individuals

---

## 9. Normalization Process

| Step | Action | Validation |
|------|--------|------------|
| Load | Read source CSV | Schema column check |
| Dedupe | Remove exact duplicates | 3 removed |
| Add IDs | Deterministic UUID from row hash | Reproducible |
| Output | Write to L0 | SHA-256 hash |

Normalization script: `pipelines/processing/normalize_black_book.py`

Verify existing output:
```bash
python pipelines/processing/normalize_black_book.py --verify-only
```

---

## 10. Related Documents

| Document | Relationship |
|----------|--------------|
| [normalize_black_book.py](../../pipelines/processing/normalize_black_book.py) | Normalization script |
| [black-book.csv](../../data/layer-0-canonical/black-book.csv) | Output dataset |
| [raw/epsteinsblackbook-com/](../../data/raw/epsteinsblackbook-com/) | Source files |
| [flight-logs-provenance.md](flight-logs-provenance.md) | Companion dataset |
