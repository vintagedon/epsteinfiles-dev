#!/usr/bin/env python3
"""
Transform Black Book from L0 (core) to L1

Implements:
- BB-1: Multi-person entry decomposition
- BB-2: Phone normalization to E.164
- BB-3: Country standardization to ISO 3166-1
- BB-4: Entity type classification

Creates:
- l1.contacts: One row per L0 record with normalized fields
- l1.contact_persons: Decomposed individuals (links to L0)
- l1.phone_numbers: Normalized phone numbers

Usage:
    python transform_black_book_l1.py [--dry-run]

Requirements:
    pip install psycopg[binary] python-dotenv phonenumbers
"""

import argparse
import os
import re
import sys
import uuid
from pathlib import Path

import psycopg
from dotenv import load_dotenv

try:
    import phonenumbers
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    print("WARNING: phonenumbers library not installed. Phone normalization will be skipped.")

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Configuration
PGSQL_HOST = os.getenv("PGSQL_HOST")
PGSQL_PORT = os.getenv("PGSQL_PORT", "5432")
PGSQL_USER = os.getenv("PGSQL_USER")
PGSQL_PASSWORD = os.getenv("PGSQL_PASSWORD")
PGSQL_DATABASE = os.getenv("PGSQL_DATABASE")


def get_connection():
    """Connect to the project database."""
    return psycopg.connect(
        host=PGSQL_HOST,
        port=PGSQL_PORT,
        user=PGSQL_USER,
        password=PGSQL_PASSWORD,
        dbname=PGSQL_DATABASE
    )


# =============================================================================
# BB-3: Country Standardization
# =============================================================================

COUNTRY_MAP = {
    # Standard names
    "US": "US",
    "USA": "US",
    "United States": "US",
    "UK": "GB",
    "U.K.": "GB",
    "England": "GB",
    "Great Britain": "GB",
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
    "Monaco": "MC",
    "Mexico": "MX",
    "Japan": "JP",
    "Netherlands": "NL",
    "Ireland": "IE",
    "Austria": "AT",
    "Czech Republic": "CZ",
    "Poland": "PL",
    "Greece": "GR",
    "Turkey": "TR",
    "India": "IN",
    "Thailand": "TH",
    "Philippines": "PH",
    "Indonesia": "ID",
    "Malaysia": "MY",
    "New Zealand": "NZ",
    "Chile": "CL",
    "Colombia": "CO",
    "Venezuela": "VE",
    "Ecuador": "EC",
    "Uruguay": "UY",
    "Panama": "PA",
    "Costa Rica": "CR",
    "Dominican Republic": "DO",
    "Jamaica": "JM",
    "Barbados": "BB",
    "Trinidad": "TT",
    "Cayman Islands": "KY",
    "Bermuda": "BM",
    "Virgin Islands": "VI",
    "Puerto Rico": "PR",
    
    # Typos and variations
    "Columbia": "CO",  # Common typo for Colombia
    "Untied States": "US",
    
    # Cities used as countries (infer from context)
    "London": "GB",
    "New York": "US",
    "Paris": "FR",
    "Los Angeles": "US",
    "Miami": "US",
    "Palm Beach": "US",
}


def normalize_country(country: str | None) -> str | None:
    """
    Normalize country to ISO 3166-1 alpha-2.
    
    Returns None if unmappable.
    """
    if not country:
        return None
    
    country = country.strip()
    
    # Direct lookup
    if country in COUNTRY_MAP:
        return COUNTRY_MAP[country]
    
    # Case-insensitive lookup
    country_lower = country.lower()
    for key, value in COUNTRY_MAP.items():
        if key.lower() == country_lower:
            return value
    
    # Already ISO code?
    if len(country) == 2 and country.isupper():
        return country
    
    return None


# =============================================================================
# BB-4: Entity Type Classification
# =============================================================================

def classify_entity_type(row: dict) -> str:
    """
    Classify entity as individual, household, organization, or unknown.
    """
    company = row.get("company_text") or ""
    first_name = row.get("first_name") or ""
    surname = row.get("surname") or ""
    name = row.get("name") or ""
    
    # Has company but no individual name components
    if company and not first_name and not surname:
        return "organization"
    
    # Multi-person entry
    if " & " in name or " and " in name.lower():
        return "household"
    
    # Has name components
    if first_name or surname:
        return "individual"
    
    return "unknown"


# =============================================================================
# BB-1: Multi-Person Decomposition
# =============================================================================

def decompose_multi_person(name: str, surname: str | None, first_name: str | None) -> list[dict]:
    """
    Split multi-person entries into individual records.
    
    Patterns handled:
    - "Surname, First1 & First2"
    - "Surname First1 & First2"
    - "First1 & First2 Surname"
    
    Returns list of dicts with 'first', 'last', 'position' keys.
    """
    if not name:
        return [{"raw": "", "position": 1}]
    
    # Check for & or 'and' separator
    if " & " not in name and " and " not in name.lower():
        # Single person - use parsed components if available
        return [{
            "first": first_name or "",
            "last": surname or "",
            "raw": name,
            "position": 1
        }]
    
    # Pattern 1: "Surname, First1 & First2"
    match = re.match(r'^([^,]+),\s*(.+?)\s*&\s*(.+)$', name)
    if match:
        surname_part, first1, first2 = match.groups()
        return [
            {"first": first1.strip(), "last": surname_part.strip(), "position": 1},
            {"first": first2.strip(), "last": surname_part.strip(), "position": 2}
        ]
    
    # Pattern 2: "Surname First1 & First2" (no comma)
    match = re.match(r'^([A-Z][a-z]+)\s+(.+?)\s*&\s*(.+)$', name)
    if match:
        surname_part, first1, first2 = match.groups()
        return [
            {"first": first1.strip(), "last": surname_part.strip(), "position": 1},
            {"first": first2.strip(), "last": surname_part.strip(), "position": 2}
        ]
    
    # Pattern 3: "First1 & First2 Surname" 
    match = re.match(r'^(.+?)\s*&\s*(.+?)\s+([A-Z][a-z]+)$', name)
    if match:
        first1, first2, surname_part = match.groups()
        return [
            {"first": first1.strip(), "last": surname_part.strip(), "position": 1},
            {"first": first2.strip(), "last": surname_part.strip(), "position": 2}
        ]
    
    # Pattern with 'and' instead of &
    name_and = re.sub(r'\s+and\s+', ' & ', name, flags=re.IGNORECASE)
    if name_and != name:
        return decompose_multi_person(name_and, surname, first_name)
    
    # Couldn't parse - return as single with raw
    return [{
        "first": first_name or "",
        "last": surname or "",
        "raw": name,
        "position": 1
    }]


def generate_household_id(l0_record_id) -> str:
    """Generate deterministic household ID from L0 record ID."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
    return str(uuid.uuid5(namespace, str(l0_record_id)))


# =============================================================================
# BB-2: Phone Normalization
# =============================================================================

# Region hints based on country
REGION_MAP = {
    "GB": "GB",
    "UK": "GB",
    "US": "US",
    "FR": "FR",
    "CH": "CH",
    "ES": "ES",
    "IT": "IT",
    "DE": "DE",
    "AU": "AU",
    "BR": "BR",
    "CA": "CA",
    "SE": "SE",
    "IL": "IL",
    "SG": "SG",
    "HK": "HK",
    "ZA": "ZA",
    "JP": "JP",
    "MX": "MX",
    "NL": "NL",
    "IE": "IE",
    "AT": "AT",
    "BE": "BE",
    "RU": "RU",
    "IN": "IN",
    "NZ": "NZ",
}


def normalize_phone(raw: str, country_iso: str | None = None) -> dict:
    """
    Normalize phone number to E.164 format.
    
    Returns dict with:
    - raw_value: Original input
    - e164_format: Normalized E.164 (or None if invalid)
    - country_code: Numeric country code
    - national_format: Formatted for display
    - is_valid: Whether parsing succeeded
    - parse_region: Region used for parsing
    """
    if not PHONENUMBERS_AVAILABLE:
        return {
            "raw_value": raw,
            "e164_format": None,
            "country_code": None,
            "national_format": None,
            "is_valid": False,
            "parse_region": None
        }
    
    if not raw or not raw.strip():
        return {
            "raw_value": raw,
            "e164_format": None,
            "country_code": None,
            "national_format": None,
            "is_valid": False,
            "parse_region": None
        }
    
    raw = raw.strip()
    
    # Determine region
    region = REGION_MAP.get(country_iso, "US")
    
    # Override for zero-prefix (likely UK)
    if raw.startswith("0") and not raw.startswith("00") and not country_iso:
        region = "GB"
    
    try:
        parsed = phonenumbers.parse(raw, region)
        if phonenumbers.is_valid_number(parsed):
            return {
                "raw_value": raw,
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
    
    return {
        "raw_value": raw,
        "e164_format": None,
        "country_code": None,
        "national_format": None,
        "is_valid": False,
        "parse_region": region
    }


def extract_phones_from_row(row: dict, country_iso: str | None) -> list[dict]:
    """
    Extract and normalize all phone numbers from a black book row.
    
    Handles pipe-separated values in single fields.
    """
    phones = []
    
    phone_fields = [
        ("phone_general", "general"),
        ("phone_work", "work"),
        ("phone_home", "home"),
        ("phone_mobile", "mobile"),
    ]
    
    for field, phone_type in phone_fields:
        value = row.get(field)
        if not value:
            continue
        
        # Split on pipe for multi-number fields
        numbers = value.split("|") if "|" in value else [value]
        
        for num in numbers:
            num = num.strip()
            if num:
                normalized = normalize_phone(num, country_iso)
                normalized["phone_type"] = phone_type
                phones.append(normalized)
    
    return phones


# =============================================================================
# DDL
# =============================================================================

CONTACTS_DDL = """
CREATE TABLE IF NOT EXISTS l1.contacts (
    contact_id UUID PRIMARY KEY,
    
    -- L0 link
    l0_record_id UUID NOT NULL,  -- References core.black_book.record_id
    
    -- Original fields
    page INTEGER,
    name TEXT,
    company_text TEXT,
    surname TEXT,
    first_name TEXT,
    
    -- BB-3: Normalized location
    address TEXT,
    city TEXT,
    zip TEXT,
    country_raw TEXT,
    country_iso CHAR(2),
    
    -- BB-4: Entity classification
    entity_type VARCHAR(20) CHECK (entity_type IN ('individual', 'household', 'organization', 'unknown')),
    
    -- Email
    email TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contacts_l0 ON l1.contacts(l0_record_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON l1.contacts(surname, first_name);
CREATE INDEX IF NOT EXISTS idx_contacts_country ON l1.contacts(country_iso);
CREATE INDEX IF NOT EXISTS idx_contacts_entity_type ON l1.contacts(entity_type);
"""

CONTACT_PERSONS_DDL = """
CREATE TABLE IF NOT EXISTS l1.contact_persons (
    person_id UUID PRIMARY KEY,
    
    -- Links
    contact_id UUID REFERENCES l1.contacts(contact_id),
    l0_record_id UUID NOT NULL,
    household_id UUID,  -- Links people from same L0 record
    
    -- BB-1: Decomposed name
    extracted_first TEXT,
    extracted_last TEXT,
    extracted_raw TEXT,
    position_in_record INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contact_persons_contact ON l1.contact_persons(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_persons_household ON l1.contact_persons(household_id);
CREATE INDEX IF NOT EXISTS idx_contact_persons_name ON l1.contact_persons(extracted_last, extracted_first);
"""

PHONE_NUMBERS_DDL = """
CREATE TABLE IF NOT EXISTS l1.phone_numbers (
    phone_id UUID PRIMARY KEY,
    
    -- Links
    contact_id UUID REFERENCES l1.contacts(contact_id),
    l0_record_id UUID NOT NULL,
    
    -- BB-2: Phone data
    phone_type VARCHAR(20),
    raw_value TEXT,
    e164_format VARCHAR(20),
    country_code INTEGER,
    national_format VARCHAR(30),
    is_valid BOOLEAN,
    parse_region VARCHAR(2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_phone_numbers_contact ON l1.phone_numbers(contact_id);
CREATE INDEX IF NOT EXISTS idx_phone_numbers_e164 ON l1.phone_numbers(e164_format) WHERE e164_format IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_phone_numbers_valid ON l1.phone_numbers(is_valid);
"""


def create_tables(conn):
    """Create L1 black book tables."""
    print("Creating L1 black book tables...")
    
    with conn.cursor() as cur:
        cur.execute(CONTACTS_DDL)
        print("  Created l1.contacts")
        
        cur.execute(CONTACT_PERSONS_DDL)
        print("  Created l1.contact_persons")
        
        cur.execute(PHONE_NUMBERS_DDL)
        print("  Created l1.phone_numbers")
    
    conn.commit()


# =============================================================================
# Main Transform
# =============================================================================

def transform_black_book(dry_run: bool = False):
    """
    Transform black book from core to L1.
    """
    print("Transforming black book to L1...")
    
    with get_connection() as conn:
        # Create tables
        create_tables(conn)
        
        with conn.cursor() as cur:
            # Clear existing L1 data
            if not dry_run:
                cur.execute("TRUNCATE l1.phone_numbers CASCADE")
                cur.execute("TRUNCATE l1.contact_persons CASCADE")
                cur.execute("TRUNCATE l1.contacts CASCADE")
            
            # Fetch all L0 records
            cur.execute("""
                SELECT 
                    record_id, page, page_link, name, company_text, surname,
                    first_name, address_type, address, zip, city, country,
                    phone_general, phone_work, phone_home, phone_mobile, email
                FROM core.black_book
                ORDER BY page, name
            """)
            
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            
            print(f"  Processing {len(rows)} L0 records...")
            
            # Output collections
            contacts = []
            contact_persons = []
            phone_numbers = []
            
            # Stats
            stats = {
                "individual": 0,
                "household": 0,
                "organization": 0,
                "unknown": 0,
                "multi_person_entries": 0,
                "total_persons": 0,
                "phones_total": 0,
                "phones_valid": 0,
                "country_mapped": 0,
                "country_unmapped": 0,
            }
            
            for row_tuple in rows:
                row = dict(zip(columns, row_tuple))
                l0_record_id = row["record_id"]
                
                # BB-3: Country normalization
                country_raw = row.get("country")
                country_iso = normalize_country(country_raw)
                
                if country_iso:
                    stats["country_mapped"] += 1
                elif country_raw:
                    stats["country_unmapped"] += 1
                
                # BB-4: Entity classification
                entity_type = classify_entity_type(row)
                stats[entity_type] += 1
                
                # Create contact record
                contact_id = str(uuid.uuid4())
                contacts.append({
                    "contact_id": contact_id,
                    "l0_record_id": l0_record_id,
                    "page": row["page"],
                    "name": row["name"],
                    "company_text": row["company_text"],
                    "surname": row["surname"],
                    "first_name": row["first_name"],
                    "address": row["address"],
                    "city": row["city"],
                    "zip": row["zip"],
                    "country_raw": country_raw,
                    "country_iso": country_iso,
                    "entity_type": entity_type,
                    "email": row["email"],
                })
                
                # BB-1: Multi-person decomposition
                persons = decompose_multi_person(
                    row["name"],
                    row["surname"],
                    row["first_name"]
                )
                
                if len(persons) > 1:
                    stats["multi_person_entries"] += 1
                
                household_id = generate_household_id(l0_record_id) if len(persons) > 1 else None
                
                for person in persons:
                    stats["total_persons"] += 1
                    contact_persons.append({
                        "person_id": str(uuid.uuid4()),
                        "contact_id": contact_id,
                        "l0_record_id": l0_record_id,
                        "household_id": household_id,
                        "extracted_first": person.get("first", ""),
                        "extracted_last": person.get("last", ""),
                        "extracted_raw": person.get("raw", ""),
                        "position_in_record": person["position"],
                    })
                
                # BB-2: Phone normalization
                phones = extract_phones_from_row(row, country_iso)
                
                for phone in phones:
                    stats["phones_total"] += 1
                    if phone["is_valid"]:
                        stats["phones_valid"] += 1
                    
                    phone_numbers.append({
                        "phone_id": str(uuid.uuid4()),
                        "contact_id": contact_id,
                        "l0_record_id": l0_record_id,
                        "phone_type": phone["phone_type"],
                        "raw_value": phone["raw_value"],
                        "e164_format": phone["e164_format"],
                        "country_code": phone["country_code"],
                        "national_format": phone["national_format"],
                        "is_valid": phone["is_valid"],
                        "parse_region": phone["parse_region"],
                    })
            
            # Print stats
            print("\n  Entity type distribution:")
            print(f"    Individual:   {stats['individual']:,}")
            print(f"    Household:    {stats['household']:,}")
            print(f"    Organization: {stats['organization']:,}")
            print(f"    Unknown:      {stats['unknown']:,}")
            
            print("\n  Multi-person decomposition:")
            print(f"    Multi-person entries: {stats['multi_person_entries']}")
            print(f"    Total persons:        {stats['total_persons']}")
            
            print("\n  Phone normalization:")
            print(f"    Total phones:  {stats['phones_total']}")
            print(f"    Valid (E.164): {stats['phones_valid']}")
            if stats['phones_total'] > 0:
                pct = 100.0 * stats['phones_valid'] / stats['phones_total']
                print(f"    Success rate:  {pct:.1f}%")
            
            print("\n  Country normalization:")
            print(f"    Mapped:   {stats['country_mapped']}")
            print(f"    Unmapped: {stats['country_unmapped']}")
            
            if dry_run:
                print("\n  [DRY RUN] No data written")
                return
            
            # Insert contacts
            print("\n  Inserting contacts...")
            contact_cols = [
                "contact_id", "l0_record_id", "page", "name", "company_text",
                "surname", "first_name", "address", "city", "zip",
                "country_raw", "country_iso", "entity_type", "email"
            ]
            contact_placeholders = ", ".join(["%s"] * len(contact_cols))
            contact_insert = f"""
                INSERT INTO l1.contacts ({", ".join(contact_cols)})
                VALUES ({contact_placeholders})
            """
            contact_rows = [
                tuple(c[col] for col in contact_cols)
                for c in contacts
            ]
            cur.executemany(contact_insert, contact_rows)  # type: ignore[arg-type]
            
            # Insert contact persons
            print("  Inserting contact persons...")
            person_cols = [
                "person_id", "contact_id", "l0_record_id", "household_id",
                "extracted_first", "extracted_last", "extracted_raw", "position_in_record"
            ]
            person_placeholders = ", ".join(["%s"] * len(person_cols))
            person_insert = f"""
                INSERT INTO l1.contact_persons ({", ".join(person_cols)})
                VALUES ({person_placeholders})
            """
            person_rows = [
                tuple(p[col] for col in person_cols)
                for p in contact_persons
            ]
            cur.executemany(person_insert, person_rows)  # type: ignore[arg-type]
            
            # Insert phone numbers
            print("  Inserting phone numbers...")
            phone_cols = [
                "phone_id", "contact_id", "l0_record_id", "phone_type",
                "raw_value", "e164_format", "country_code", "national_format",
                "is_valid", "parse_region"
            ]
            phone_placeholders = ", ".join(["%s"] * len(phone_cols))
            phone_insert = f"""
                INSERT INTO l1.phone_numbers ({", ".join(phone_cols)})
                VALUES ({phone_placeholders})
            """
            phone_rows = [
                tuple(p[col] for col in phone_cols)
                for p in phone_numbers
            ]
            cur.executemany(phone_insert, phone_rows)  # type: ignore[arg-type]
            
            conn.commit()
            
            # Verify
            cur.execute("SELECT COUNT(*) FROM l1.contacts")
            row = cur.fetchone()
            contact_count = row[0] if row else 0
            
            cur.execute("SELECT COUNT(*) FROM l1.contact_persons")
            row = cur.fetchone()
            person_count = row[0] if row else 0
            
            cur.execute("SELECT COUNT(*) FROM l1.phone_numbers")
            row = cur.fetchone()
            phone_count = row[0] if row else 0
            
            cur.execute("SELECT COUNT(*) FROM l1.phone_numbers WHERE is_valid = TRUE")
            row = cur.fetchone()
            valid_phone_count = row[0] if row else 0
            
            print(f"\n  ✓ Inserted {contact_count} contacts")
            print(f"  ✓ Inserted {person_count} contact persons")
            print(f"  ✓ Inserted {phone_count} phone numbers ({valid_phone_count} valid)")


def main():
    parser = argparse.ArgumentParser(description="Transform black book to L1")
    parser.add_argument("--dry-run", action="store_true",
                        help="Process without writing to database")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Epstein Files ARD - Black Book L1 Transform")
    print("=" * 60)
    
    if not PHONENUMBERS_AVAILABLE:
        print("\nWARNING: Install phonenumbers for phone normalization:")
        print("  pip install phonenumbers")
        print()
    
    try:
        transform_black_book(dry_run=args.dry_run)
        print("\n✓ Transform completed successfully")
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
