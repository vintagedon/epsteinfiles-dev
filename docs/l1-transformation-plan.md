# Layer 1 Transformation Plan

**Created:** 2026-02-01  
**Based on:** Task 4.2 Quality Audit (`research/quality-analysis/l0-quality-audit.md`)  
**Status:** Approved for M05 implementation

---

## Overview

This document captures the approved transformation decisions for L0 → L1 processing. All transformations maintain provenance links to L0 records.

**Guiding Principles:**
1. L0 data is immutable — transformations create new L1 tables, not modifications
2. Every L1 record links back to its L0 source via foreign key
3. Lossy transformations (e.g., phone normalization) preserve original values
4. GDR architecture patterns guide table design

---

## Flight Logs Transformations

### FL-1: Identity Confidence Scoring

**Issue:** 17.7% of passengers cannot be resolved to named individuals  
**Source Field:** `Known`, `First Name`, `Last Name`

| Pattern | Confidence Score | Count |
|---------|-----------------|-------|
| Known = "Yes" | 1.0 | 4,118 |
| Known = "No", full name present | 0.7 | varies |
| Initials only (e.g., "A S") | 0.3 | 459 |
| Descriptive (e.g., "Female (1)") | 0.1 | 128 |
| Unknown ("?") | 0.0 | 438 |

**L1 Implementation:**
```sql
ALTER TABLE l1.flight_passengers ADD COLUMN identity_confidence DECIMAL(2,1);
```

**Transformation Logic:**
```python
def compute_confidence(row):
    if row["Known"] == "Yes":
        return 1.0
    if "?" in row["First Name"] or "?" in row["Last Name"]:
        return 0.0
    if "Female" in row["First Name"] or "Male" in row["First Name"]:
        return 0.1
    if len(row["First Name"]) <= 2 and len(row["Last Name"]) <= 2:
        return 0.3
    return 0.7
```

---

### FL-2: Victim Protection Flags

**Issue:** "Female (1)", "Male (1)" entries may represent victims  
**Ethical Constraint:** K-anonymity required for public-facing views

**L1 Implementation:**
```sql
ALTER TABLE l1.flight_passengers ADD COLUMN potential_victim BOOLEAN DEFAULT FALSE;
ALTER TABLE l1.flight_passengers ADD COLUMN suppress_from_public BOOLEAN DEFAULT FALSE;
```

**Flagging Logic:**
- `potential_victim = TRUE` when First Name matches `/^(Female|Male)\s*\(\d+\)$/`
- `suppress_from_public = TRUE` when `potential_victim = TRUE` OR `identity_confidence < 0.3`

**Public View:**
```sql
CREATE VIEW public.flight_passengers AS
SELECT * FROM l1.flight_passengers
WHERE suppress_from_public = FALSE;
```

---

### FL-3: Date Normalization

**Issue:** Dates in M/D/YYYY format (US locale)  
**Target:** ISO 8601 (YYYY-MM-DD)

**L1 Implementation:**
```sql
ALTER TABLE l1.flight_events ADD COLUMN flight_date DATE;
-- Derived from L0.Date via parsing
```

**Transformation:**
```python
from datetime import datetime
def normalize_date(date_str):
    return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
```

---

### FL-4: Name Parsing with probablepeople

**Issue:** Names need decomposition for entity resolution  
**Tool:** `probablepeople` library (CRF-based parsing)

**L1 Implementation:**
```sql
CREATE TABLE l1.identity_mentions (
    mention_id UUID PRIMARY KEY,
    source_table VARCHAR(50),  -- 'flight_logs' or 'black_book'
    source_id VARCHAR(100),    -- L0 record identifier
    raw_name TEXT,
    parsed_prefix VARCHAR(20),
    parsed_first VARCHAR(100),
    parsed_middle VARCHAR(100),
    parsed_last VARCHAR(100),
    parsed_suffix VARCHAR(20),
    parsed_nickname VARCHAR(100),
    parse_confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Transformation:**
```python
import probablepeople as pp

def parse_name(full_name):
    try:
        parsed, name_type = pp.tag(full_name)
        return {
            "parsed_first": parsed.get("GivenName", ""),
            "parsed_last": parsed.get("Surname", ""),
            "parsed_middle": parsed.get("MiddleName", ""),
            "parsed_prefix": parsed.get("PrefixMarital") or parsed.get("PrefixOther", ""),
            "parsed_suffix": parsed.get("SuffixGenerational") or parsed.get("SuffixOther", ""),
            "parse_confidence": 0.9 if name_type == "Person" else 0.5
        }
    except pp.RepeatedLabelError:
        return {"raw_name": full_name, "parse_confidence": 0.0}
```

---

## Black Book Transformations

### BB-1: Multi-Person Entry Decomposition

**Issue:** 293 records (12.6%) contain multiple people  
**Pattern:** "Surname, First1 & First2" or "Surname First1 & First2"

**L1 Implementation:**
```sql
CREATE TABLE l1.contact_persons (
    person_id UUID PRIMARY KEY,
    l0_record_id UUID REFERENCES l0.black_book(record_id),
    household_id UUID,  -- Links people from same L0 record
    extracted_name TEXT,
    position_in_record INT,  -- 1 = primary, 2 = secondary
    -- Parsed name fields from identity_mentions
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Decomposition Logic:**
```python
import re

def decompose_multi_person(name):
    """
    Split 'Agnew, Marie Claire & John' into:
    - ('Marie Claire', 'Agnew')
    - ('John', 'Agnew')
    """
    # Pattern: Surname, First1 & First2
    match = re.match(r'^([^,]+),\s*(.+?)\s*&\s*(.+)$', name)
    if match:
        surname, first1, first2 = match.groups()
        return [
            {"first": first1.strip(), "last": surname.strip(), "position": 1},
            {"first": first2.strip(), "last": surname.strip(), "position": 2}
        ]
    
    # Pattern: Surname First1 & First2 (no comma)
    match = re.match(r'^([^\s,]+)\s+(.+?)\s*&\s*(.+)$', name)
    if match:
        surname, first1, first2 = match.groups()
        return [
            {"first": first1.strip(), "last": surname.strip(), "position": 1},
            {"first": first2.strip(), "last": surname.strip(), "position": 2}
        ]
    
    # Single person
    return [{"raw": name, "position": 1}]
```

**Household Linking:**
- Generate `household_id = UUID5(namespace, l0_record_id)` for all persons from same L0 record
- Enables queries like "all contacts from same household"

---

### BB-2: Phone Normalization to E.164

**Issue:** 6+ phone formats, unusable for matching  
**Tool:** `phonenumbers` library (Google libphonenumber port)

**L1 Implementation:**
```sql
CREATE TABLE l1.phone_numbers (
    phone_id UUID PRIMARY KEY,
    l0_record_id UUID REFERENCES l0.black_book(record_id),
    phone_type VARCHAR(20),  -- 'general', 'work', 'home', 'mobile'
    raw_value TEXT,
    e164_format VARCHAR(20),  -- +12125551234
    country_code INT,
    national_format VARCHAR(30),
    is_valid BOOLEAN,
    parse_region VARCHAR(2),  -- Region used for parsing
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Transformation:**
```python
import phonenumbers

COUNTRY_MAP = {
    "UK": "GB", "England": "GB", "London": "GB",
    "US": "US", "New York": "US",
    "France": "FR", "Switzerland": "CH", "Spain": "ES",
    "Italy": "IT", "Germany": "DE", "Australia": "AU",
    # ... full mapping
}

def normalize_phone(raw: str, country: str = None) -> dict:
    # Determine region
    region = COUNTRY_MAP.get(country, "US")
    
    # Override for zero-prefix (likely UK)
    if raw.startswith("0") and not country:
        region = "GB"
    
    try:
        parsed = phonenumbers.parse(raw, region)
        if phonenumbers.is_valid_number(parsed):
            return {
                "e164_format": phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                ),
                "country_code": parsed.country_code,
                "national_format": phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.NATIONAL
                ),
                "is_valid": True,
                "parse_region": region
            }
    except phonenumbers.NumberParseException:
        pass
    
    return {"raw_value": raw, "is_valid": False, "parse_region": region}
```

**Multi-Number Handling:**
- 958 records have pipe-separated numbers in single field
- Split on `|` before normalization
- Create separate `phone_numbers` row for each

---

### BB-3: Country Standardization to ISO 3166-1

**Issue:** 28 country variations including cities as countries  
**Target:** ISO 3166-1 alpha-2 codes

**L1 Implementation:**
```sql
ALTER TABLE l1.contacts ADD COLUMN country_iso CHAR(2);
ALTER TABLE l1.contacts ADD COLUMN country_raw TEXT;  -- Preserve original
```

**Mapping Table:**
```python
COUNTRY_NORMALIZE = {
    # Direct mappings
    "US": "US",
    "UK": "GB",
    "France": "FR",
    "Switzerland": "CH",
    "Spain": "ES",
    "Italy": "IT",
    "Australia": "AU",
    "Germany": "DE",
    "Brazil": "BR",
    "Canada": "CA",
    "Sweden": "SE",
    "Israel": "IL",
    "Singapore": "SG",
    "Hong Kong": "HK",
    "South Africa": "ZA",
    "Kenya": "KE",
    "Peru": "PE",
    "Argentina": "AR",
    "Portugal": "PT",
    "Belgium": "BE",
    "Nigeria": "NG",
    "Russia": "RU",
    "Saudi Arabia": "SA",
    "Bahamas": "BS",
    
    # Corrections
    "England": "GB",
    "Columbia": "CO",  # Typo for Colombia
    
    # Cities → Countries (infer from context)
    "London": "GB",
    "New York": "US",
}
```

---

### BB-4: Entity Type Classification

**Issue:** 226 records are organizations, not individuals  
**Impact:** Entity resolution should handle differently

**L1 Implementation:**
```sql
ALTER TABLE l1.contacts ADD COLUMN entity_type VARCHAR(20) 
    CHECK (entity_type IN ('individual', 'household', 'organization', 'unknown'));
```

**Classification Logic:**
```python
def classify_entity(row):
    company = row.get("Company/Add. Text", "")
    first = row.get("First Name", "")
    surname = row.get("Surname", "")
    name = row.get("Name", "")
    
    # Has company but no individual name components
    if company and not first and not surname:
        return "organization"
    
    # Multi-person entry
    if " & " in name or " and " in name.lower():
        return "household"
    
    # Has name components
    if first or surname:
        return "individual"
    
    return "unknown"
```

---

## Cross-Dataset: Entity Resolution Preparation

### ER-1: Unified Identity Mentions Table

Both datasets feed into `l1.identity_mentions` for cross-reference:

```sql
CREATE INDEX idx_identity_soundex ON l1.identity_mentions 
    USING btree (soundex(parsed_last), soundex(parsed_first));

CREATE INDEX idx_identity_embedding ON l1.identity_mentions 
    USING ivfflat (name_embedding vector_cosine_ops);
```

**Resolution Pipeline (M05-M06):**
1. Parse all names with `probablepeople`
2. Generate Soundex codes for blocking
3. Generate embeddings with `sentence-transformers`
4. Candidate pair generation via blocking
5. Similarity scoring (Soundex + embedding + Jaro-Winkler)
6. Threshold-based clustering
7. Manual review queue for ambiguous matches

---

## Implementation Priority

| ID | Transformation | Priority | Complexity | Dependencies |
|----|---------------|----------|------------|--------------|
| FL-1 | Identity confidence | High | Low | None |
| FL-2 | Victim protection | High | Low | FL-1 |
| FL-3 | Date normalization | High | Low | None |
| FL-4 | Name parsing | High | Medium | probablepeople |
| BB-1 | Multi-person decomposition | High | Medium | None |
| BB-2 | Phone normalization | High | Medium | phonenumbers |
| BB-3 | Country standardization | Medium | Low | None |
| BB-4 | Entity type classification | Medium | Low | None |
| ER-1 | Entity resolution prep | Medium | High | FL-4, BB-1 |

---

## Dependencies

**Python Libraries:**
```
probablepeople>=0.5.5
phonenumbers>=8.13.0
python-Levenshtein>=0.21.0  # For Jaro-Winkler
```

**PostgreSQL Extensions:**
```sql
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- For soundex()
CREATE EXTENSION IF NOT EXISTS vector;         -- For pgvector
```

---

## Validation Criteria

Each transformation must pass:

1. **Completeness:** All L0 records have corresponding L1 records
2. **Provenance:** Every L1 record links to L0 source
3. **Reversibility:** Original values preserved (e.g., `raw_value` alongside `e164_format`)
4. **Consistency:** Normalized values follow documented standards

**Validation Queries:**
```sql
-- Check L0 → L1 completeness
SELECT COUNT(*) FROM l0.flight_logs l0
LEFT JOIN l1.flight_passengers l1 ON l0.id = l1.l0_id
WHERE l1.l0_id IS NULL;  -- Should be 0

-- Check phone normalization coverage
SELECT 
    COUNT(*) FILTER (WHERE is_valid) as valid,
    COUNT(*) FILTER (WHERE NOT is_valid) as invalid,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_valid) / COUNT(*), 1) as valid_pct
FROM l1.phone_numbers;
```
