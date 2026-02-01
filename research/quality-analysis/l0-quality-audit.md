# Layer 0 Quality Audit Report

**Audit Date:** 2026-02-01  
**Datasets:** Flight Logs (5,001 records), Black Book (2,324 records)  
**Methodology:** Schema validation + comprehensive field analysis  
**Artifacts:** `l0-audit-metrics.json` (raw metrics), `quality_audit_l0.py` (reproducible)

---

## Executive Summary

| Dataset | Schema Valid | Health Score | Critical Issues |
|---------|--------------|--------------|-----------------|
| Flight Logs | 73.5% | **Moderate** | Year range mismatch, FOIA subset anomalies |
| Black Book | 100% | **Good** | Phone format chaos, multi-person entries |

**Key Findings:**

1. Flight logs contain records through 2015, not 2002 as originally documented (schema update needed)
2. 270 flight records are from FOIA source with different conventions ("No Records" instead of passenger data)
3. Black book has 293 multi-person entries requiring decomposition for entity resolution
4. Phone formats are highly inconsistent — normalization essential for L1
5. Country values need standardization (28 variations including "UK" vs "England" vs "London")

---

## 1. Flight Logs Analysis

### 1.1 Schema Validation Results

| Metric | Value |
|--------|-------|
| Total records | 5,001 |
| Valid rows | 3,678 (73.5%) |
| Invalid rows | 1,323 (26.5%) |

**Validation Failures by Type:**

| Error Type | Count | Root Cause |
|------------|-------|------------|
| Year maximum exceeded | 1,258 | Schema set max=2003, data extends to 2015 |
| Pass # pattern mismatch | 270 | "No Records" value from FOIA subset |
| Data Source const mismatch | 270 | "FOIA" instead of "Flight Log" |
| Tail # pattern mismatch | 1 | Non-N-number: "121TH" |

**Recommendation:** Update schema to relax Year maximum (set to 2020) and expand Data Source enum to include "FOIA". These are valid records from a different source batch.

### 1.2 Completeness Matrix

| Column | % Populated | Missing | Notes |
|--------|-------------|---------|-------|
| Comment | 9.4% | 4,530 | Expected — comments are rare |
| Last Name | 95.2% | 241 | Unidentified passengers |
| Flight_No. | 97.6% | 118 | FOIA records lack flight numbers |
| All others | 100% | 0 | Fully populated |

### 1.3 Temporal Coverage

| Year | Records | % of Total |
|------|---------|------------|
| 1995 | 27 | 0.5% |
| 1996-2000 | 1,784 | 35.7% |
| 2001-2005 | 2,999 | 60.0% |
| 2006-2015 | 191 | 3.8% |

Peak activity: 2002 (745 records), 2001 (672), 2004 (649)

The schema's original coverage note ("January 1996 - September 2002") is incomplete. Data extends through 2015, with a long tail of post-2005 records likely from FOIA supplemental releases.

### 1.4 Name Anomalies

| Category | Count | % of Total | Examples |
|----------|-------|------------|----------|
| Known = No | 883 | 17.7% | Unverified identities |
| "?" pattern | 438 | 8.8% | `?, ?` — completely unknown |
| Initials only | 459 | 9.2% | `A S`, `JE`, `GM` |
| "Female" pattern | 97 | 1.9% | `Female (1)`, `Female (2)` |
| "Male" pattern | 31 | 0.6% | `Male (1)` |

**Combined unidentified:** ~18% of passengers cannot be directly resolved to named individuals.

### 1.5 Aircraft and Route Patterns

**Aircraft (6 unique tail numbers):**

| Tail # | Model | Type | Records |
|--------|-------|------|---------|
| N908JE | G-1159B | Jet | ~4,900 |
| Others | Various | Mixed | ~100 |

Single dominant aircraft — the Gulfstream II "Lolita Express"

**Top Routes:**

| Departure | Arrival | Count |
|-----------|---------|-------|
| PBI (West Palm Beach) | TEB (Teterboro) | High |
| TEB | PBI | High |
| SXM (St. Maarten) | Various | Moderate |

### 1.6 Data Integrity

**Duplicate Unique IDs:** 4 IDs appear twice (8 rows total)

These may be legitimate (same person on same flight in different passenger positions) or data entry errors. Requires manual review.

---

## 2. Black Book Analysis

### 2.1 Schema Validation Results

| Metric | Value |
|--------|-------|
| Total records | 2,324 |
| Valid rows | 2,324 (100%) |
| Invalid rows | 0 |

Schema validates cleanly. All Wayback URLs match expected format.

### 2.2 Completeness Matrix

| Column | % Populated | Missing | Notes |
|--------|-------------|---------|-------|
| Address-Type | 10.5% | 2,081 | Rarely specified |
| Email | 17.5% | 1,918 | Period-appropriate |
| Phone (mobile) | 25.5% | 1,732 | Mobile phones less common in era |
| Phone (work) | 29.4% | 1,641 | — |
| Company/Add. Text | 37.1% | 1,462 | — |
| Country | 66.0% | 792 | Significant gap |
| Phone (home) | 81.4% | 433 | Primary contact method |
| Phone (general) | 85.5% | 337 | — |
| Name, Page, Page-Link | 100% | 0 | Core fields complete |

### 2.3 Phone Format Analysis

**Format Distribution (all phone columns combined):**

| Format | Count | % | Example |
|--------|-------|---|---------|
| International zero-prefix | 2,151 | 55.5% | `0207 123 4567` |
| Other/unclassified | 1,284 | 33.1% | Various |
| US dashes | 285 | 7.4% | `212-555-1234` |
| Digits only | 50 | 1.3% | `2125551234` |
| US parentheses | 44 | 1.1% | `(212) 555-1234` |
| International plus | 37 | 1.0% | `+44 20 7123 4567` |

**Multi-number entries:** 958 records have pipe-separated multiple numbers in a single field.

**L1 Proposal:** Normalize to E.164 format using `phonenumbers` library (Python port of libphonenumber). Parse country context from Country field when available, default to US for ambiguous formats.

### 2.4 Email Analysis

| Metric | Value |
|--------|-------|
| Records with email | 406 (17.5%) |
| Truncated (no @) | 7 |

**Top Domains:**

| Domain | Count | Notes |
|--------|-------|-------|
| aol.com | 70 | Period-appropriate |
| yahoo.com | 11 | — |
| hotmail.com | 9 | — |
| earthlink.net | 7 | — |
| albertopinto.com | 7 | Business domain |

The heavy AOL presence is consistent with late 1990s/early 2000s address book.

### 2.5 Entry Type Anomalies

**Multi-Person Entries:** 293 records (12.6%)

| Pattern | Example |
|---------|---------|
| Surname, First1 & First2 | `Agnew, Marie Claire & John` |
| Surname First1 & First2 | `Allan Nick & Sarah` |
| Hyphenated + dual | `Alun-Jones, Jeremy & Deborah` |

These are household entries that need decomposition into separate identity records for entity resolution.

**Likely Organizations:** 226 records (9.7%)

Records with Company/Add. Text populated but no parsed First Name or Surname — likely business contacts rather than individuals.

### 2.6 Country Normalization Needs

**28 unique values requiring standardization:**

| Issue Type | Examples | Resolution |
|------------|----------|------------|
| UK variations | `UK`, `England`, `London` | → `GB` (ISO 3166-1) |
| US variations | `US`, `New York` | → `US` |
| Spelling | `Columbia` | → `Colombia` |
| City as country | `London`, `New York` | Infer from context |

**Full distribution:**

| Country | Records |
|---------|---------|
| US | 910 |
| UK | 381 |
| France | 135 |
| Spain | 16 |
| Italy | 16 |
| Others (23) | 78 |
| Missing | 792 |

---

## 3. Cross-Dataset Observations

### 3.1 Name Overlap Potential

Both datasets contain named individuals that may refer to the same people. Entity resolution in L1 should:

1. Parse all names using `probablepeople` (per GDR architecture)
2. Create unified identity_mentions table
3. Apply Soundex + embedding similarity for candidate matching
4. Manual review for high-confidence matches

### 3.2 Temporal Alignment

| Dataset | Coverage |
|---------|----------|
| Flight Logs | 1995-2015 (bulk 1996-2005) |
| Black Book | Undated (estimated late 1990s - early 2000s) |

The black book appears to be a snapshot, not a time-series. Cross-referencing with flight dates may establish "known by date X" relationships.

---

## 4. L1 Remediation Proposals

### 4.1 Flight Logs Transformations

| Issue | Impact | Proposal | Priority | GDR Alignment |
|-------|--------|----------|----------|---------------|
| Schema year max | Validation failures | Update schema max to 2020 | **High** | — |
| FOIA source subset | Pattern mismatches | Add "FOIA" to Data Source enum | **High** | — |
| Unknown passengers | Entity resolution gaps | Create `identity_confidence` score (known=1.0, initials=0.3, unknown=0.1) | Medium | Aligns with identity_mentions table |
| "Female (1)" entries | Victim identification risk | Preserve as separate entity class, apply K-anonymity rules | Medium | K-anonymity views |
| Duplicate Unique IDs | Data integrity | Manual review, add `duplicate_flag` column | Low | — |

### 4.2 Black Book Transformations

| Issue | Impact | Proposal | Priority | GDR Alignment |
|-------|--------|----------|----------|---------------|
| Phone format chaos | Unusable for matching | Normalize to E.164 using `phonenumbers` library | **High** | — |
| Multi-person entries | Entity resolution fails | Decompose into separate records, link via `household_id` | **High** | identity_mentions |
| Country variations | Geographic analysis fails | Standardize to ISO 3166-1 alpha-2 codes | Medium | — |
| Multi-number fields | Query complexity | Explode to separate rows in `phone_numbers` table | Medium | — |
| Organization entries | Mixed entity types | Add `entity_type` enum (individual, household, organization) | Medium | — |
| Truncated emails | Minor data loss | Flag but preserve | Low | — |

### 4.3 Phone Normalization Strategy

**Recommended approach using `phonenumbers` library:**

```python
import phonenumbers

def normalize_phone(raw: str, default_region: str = "US") -> dict:
    """
    Parse and normalize phone number.
    Returns dict with E.164 format, country code, and parse confidence.
    """
    try:
        parsed = phonenumbers.parse(raw, default_region)
        if phonenumbers.is_valid_number(parsed):
            return {
                "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                "country_code": parsed.country_code,
                "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
                "valid": True
            }
    except phonenumbers.NumberParseException:
        pass
    
    return {"raw": raw, "valid": False}
```

**Region inference logic:**
1. If Country field populated, use ISO mapping (UK→GB, etc.)
2. If phone starts with `0`, infer UK (most common in dataset)
3. If phone starts with `+`, parse directly
4. Else default to US

**Expected outcome:** ~85% parseable, ~15% require manual review or remain raw.

---

## 5. Schema Update Recommendations

### 5.1 Flight Logs Schema Patch

```json
{
  "Year": {
    "maximum": 2020  // was 2003
  },
  "Data Source": {
    "enum": ["Flight Log", "FOIA"]  // was const "Flight Log"
  }
}
```

### 5.2 Black Book Schema — No Changes

Schema is appropriately permissive. Quality issues are data issues, not schema issues.

---

## 6. Next Steps

1. **Immediate (Task 4.3):** Apply schema patches, document decisions
2. **M05 prep:** Create L1 transformation pipeline with:
   - `probablepeople` name parsing
   - `phonenumbers` phone normalization
   - Country standardization lookup table
   - Multi-person entry decomposition
3. **Entity resolution design:** Define matching thresholds and manual review workflow

---

## Appendix: Audit Reproducibility

**Run audit:**
```bash
python pipelines/validation/quality_audit_l0.py --output research/quality-analysis/l0-audit-metrics.json
```

**Run schema validation:**
```bash
python pipelines/validation/validate_l0_schemas.py
```

**Metrics artifact:** `research/quality-analysis/l0-audit-metrics.json`
