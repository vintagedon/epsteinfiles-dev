<!--
---
title: "Flight Logs Source Provenance"
description: "Provenance chain and quality assessment for flight log dataset"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: provenance
  - domain: flight-logs
  - layer: L0
---
-->

# Flight Logs Source Provenance

Complete provenance chain from original court exhibits to Layer 0 canonical dataset.

---

## 1. Source Identification

| Attribute | Value |
|-----------|-------|
| Title | EPSTEIN FLIGHT LOGS UNREDACTED |
| Archive URL | https://archive.org/details/epstein-flight-logs-unredacted_202304 |
| Upload Date | April 2023 |
| Original Source | Bradley Edwards court exhibits |
| Legal Case | Epstein v. Edwards, Case No. 50 2009 CA 040800 |
| Coverage | January 1996 – September 2002 |

---

## 2. Provenance Chain

```
Court Exhibits (Bradley Edwards)
    ↓
Internet Archive (April 2023)
    ↓
Local Raw: data/raw/epstein-flight-logs-unredacted.pdf
    ↓
Layer 0: data/layer-0-canonical/flight-logs.csv
```

---

## 3. File Hashes

| File | SHA-256 |
|------|---------|
| `epstein-flight-logs-unredacted.pdf` | `d30f3807f9e2b0a2dc112221607f2190e6fe6e8535e3ce198e4e6d723c7d7b15` |
| `flight-logs.csv` | `af9ed4eb4a6af7f3444e210338d0d98aca0d8e40a16928bf133876115db0095d` |

---

## 4. Extraction Metrics

| Metric | Value |
|--------|-------|
| Total Records | 5,001 |
| Unique Flights | 1,418 |
| Unique Dates | 1,184 |
| Unique Passengers | 438 |
| Known Passengers | 4,118 (82.3%) |
| Unknown Passengers | 883 (17.7%) |
| Date Range | 1/1/1996 – 9/9/2002 |
| Source Pages | 116 |

---

## 5. Schema (22 Columns)

| Column | Type | Description |
|--------|------|-------------|
| ID | int | Unique record identifier |
| Date | date | Flight date (M/D/YYYY) |
| Year | int | Year extracted |
| Aircraft Model | string | e.g., G-1159B, B-727-31 |
| Aircraft Tail # | string | FAA registration (N908JE, N909JE) |
| Aircraft Type | string | Aircraft category |
| # of Seats | int | Passenger capacity |
| DEP: Code | string | ICAO departure code |
| ARR: Code | string | ICAO arrival code |
| DEP | string | Full departure location |
| ARR | string | Full arrival location |
| Flight_No. | string | Flight number |
| Pass # | int | Passenger position on manifest |
| Unique ID | string | Composite key |
| First Name | string | Passenger first name |
| Last Name | string | Passenger last name |
| Last, First | string | Formatted name |
| First Last | string | Formatted name |
| Comment | string | Notes from source |
| Initials | string | Abbreviation used in original logs |
| Known | enum | Yes/No – identity confirmed by source |
| Data Source | string | Always "Flight Log" |

---

## 6. Data Quality Notes

**Strengths:**
- Pre-structured tabular format in source PDF
- High identification rate (82% known passengers)
- Complete date coverage for operational period
- Aircraft and route information preserved

**Limitations:**
- "Known" flag represents source's assessment, not independently verified
- Some passenger entries are initials only (17.7%)
- No crew manifest data
- Coverage ends September 2002 (not complete operational history)

---

## 7. Extraction Process

| Step | Tool | Validation |
|------|------|------------|
| PDF table extraction | pdfplumber | Schema column count |
| Header normalization | Python | Expected column names |
| Row cleaning | Python | Consistent column count per row |
| Output | CSV | SHA-256 hash |

Extraction script: `pipelines/processing/extract_flight_logs.py`

Verify existing extraction:
```bash
python pipelines/processing/extract_flight_logs.py --verify-only
```

---

## 8. Related Documents

| Document | Relationship |
|----------|--------------|
| [extract_flight_logs.py](../../pipelines/processing/extract_flight_logs.py) | Extraction script |
| [flight-logs.csv](../../data/layer-0-canonical/flight-logs.csv) | Output dataset |
| [raw/](../../data/raw/) | Source files |
