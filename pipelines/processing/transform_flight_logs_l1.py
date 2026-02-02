#!/usr/bin/env python3
"""
Transform Flight Logs from L0 (core) to L1

Implements:
- FL-1: Identity confidence scoring
- FL-2: Victim protection flags  
- FL-3: Date normalization (ISO 8601)
- FL-4: Name extraction (stored in l1.identity_mentions via Task 5.4)

Creates:
- l1.flight_events: One row per unique flight
- l1.flight_passengers: One row per passenger instance (links to L0)

Usage:
    python transform_flight_logs_l1.py [--dry-run]

Requirements:
    pip install psycopg[binary] python-dotenv
"""

import argparse
import hashlib
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

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
# FL-1: Identity Confidence Scoring
# =============================================================================

def compute_identity_confidence(row: dict) -> float:
    """
    Compute confidence score for passenger identity.
    
    Returns:
        1.0 - Known = "Yes"
        0.7 - Known = "No" but full name present
        0.3 - Initials only
        0.1 - Descriptive (Female/Male with number)
        0.0 - Unknown ("?")
    """
    known = row.get("known", "")
    first_name = row.get("first_name", "") or ""
    last_name = row.get("last_name", "") or ""
    
    # Known individuals
    if known == "Yes":
        return 1.0
    
    # Unknown marker
    if "?" in first_name or "?" in last_name:
        return 0.0
    
    # Descriptive entries (potential victims)
    if re.match(r'^(Female|Male)\s*(\(\d+\))?$', first_name, re.IGNORECASE):
        return 0.1
    
    # Check for initials only (1-2 chars each)
    first_is_initials = len(first_name.strip()) <= 2
    last_is_initials = len(last_name.strip()) <= 2
    
    if first_is_initials and last_is_initials:
        return 0.3
    
    # Has name but not verified
    return 0.7


# =============================================================================
# FL-2: Victim Protection Flags
# =============================================================================

def compute_victim_flags(row: dict, confidence: float) -> tuple[bool, bool]:
    """
    Determine victim protection flags.
    
    Returns:
        (potential_victim, suppress_from_public)
    """
    first_name = row.get("first_name", "") or ""
    
    # Pattern: "Female (1)", "Male (2)", etc.
    potential_victim = bool(
        re.match(r'^(Female|Male)\s*\(\d+\)$', first_name, re.IGNORECASE)
    )
    
    # Suppress if potential victim OR very low confidence
    suppress_from_public = potential_victim or confidence < 0.3
    
    return potential_victim, suppress_from_public


# =============================================================================
# FL-3: Date Normalization
# =============================================================================

def normalize_date(date_str: str) -> str | None:
    """
    Convert M/D/YYYY to ISO 8601 (YYYY-MM-DD).
    
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


# =============================================================================
# Flight Event Extraction
# =============================================================================

def generate_flight_id(row: dict) -> str:
    """
    Generate deterministic UUID for a flight based on its identifying attributes.
    
    Flight identity: date + aircraft_tail + dep_code + arr_code + flight_no
    """
    components = [
        row.get("date", ""),
        row.get("aircraft_tail", ""),
        row.get("dep_code", ""),
        row.get("arr_code", ""),
        str(row.get("flight_no", ""))
    ]
    
    key = "|".join(components)
    hash_bytes = hashlib.sha256(key.encode()).digest()[:16]
    return str(uuid.UUID(bytes=hash_bytes))


# =============================================================================
# DDL
# =============================================================================

FLIGHT_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS l1.flight_events (
    flight_id UUID PRIMARY KEY,
    
    -- Temporal
    flight_date DATE,
    flight_date_raw TEXT,  -- Original M/D/YYYY
    year INTEGER,
    
    -- Aircraft
    aircraft_model TEXT,
    aircraft_tail TEXT,
    aircraft_type TEXT,
    num_seats INTEGER,
    
    -- Route
    dep_code TEXT,
    arr_code TEXT,
    dep_location TEXT,
    arr_location TEXT,
    flight_no TEXT,
    
    -- Source
    data_source TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flight_events_date ON l1.flight_events(flight_date);
CREATE INDEX IF NOT EXISTS idx_flight_events_tail ON l1.flight_events(aircraft_tail);
CREATE INDEX IF NOT EXISTS idx_flight_events_route ON l1.flight_events(dep_code, arr_code);
"""

FLIGHT_PASSENGERS_DDL = """
CREATE TABLE IF NOT EXISTS l1.flight_passengers (
    passenger_id UUID PRIMARY KEY,
    
    -- Links
    flight_id UUID REFERENCES l1.flight_events(flight_id),
    l0_id INTEGER NOT NULL,  -- References core.flight_logs.id
    
    -- Passenger info
    first_name TEXT,
    last_name TEXT,
    first_last TEXT,
    initials TEXT,
    pass_position TEXT,
    comment TEXT,
    
    -- FL-1: Identity confidence
    identity_confidence DECIMAL(2,1),
    known TEXT,  -- Original Yes/No
    
    -- FL-2: Victim protection
    potential_victim BOOLEAN DEFAULT FALSE,
    suppress_from_public BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flight_passengers_flight ON l1.flight_passengers(flight_id);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_l0 ON l1.flight_passengers(l0_id);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_name ON l1.flight_passengers(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_confidence ON l1.flight_passengers(identity_confidence);
"""

PUBLIC_VIEW_DDL = """
CREATE OR REPLACE VIEW l1.flight_passengers_public AS
SELECT 
    passenger_id,
    flight_id,
    l0_id,
    first_name,
    last_name,
    first_last,
    initials,
    pass_position,
    identity_confidence,
    known,
    created_at
FROM l1.flight_passengers
WHERE suppress_from_public = FALSE;
"""


def create_tables(conn):
    """Create L1 flight tables."""
    print("Creating L1 flight tables...")
    
    with conn.cursor() as cur:
        cur.execute(FLIGHT_EVENTS_DDL)
        print("  Created l1.flight_events")
        
        cur.execute(FLIGHT_PASSENGERS_DDL)
        print("  Created l1.flight_passengers")
        
        cur.execute(PUBLIC_VIEW_DDL)
        print("  Created l1.flight_passengers_public view")
    
    conn.commit()


# =============================================================================
# Main Transform
# =============================================================================

def transform_flight_logs(dry_run: bool = False):
    """
    Transform flight logs from core to L1.
    """
    print("Transforming flight logs to L1...")
    
    with get_connection() as conn:
        # Create tables
        create_tables(conn)
        
        with conn.cursor() as cur:
            # Clear existing L1 data
            if not dry_run:
                cur.execute("TRUNCATE l1.flight_passengers CASCADE")
                cur.execute("TRUNCATE l1.flight_events CASCADE")
            
            # Fetch all L0 records
            cur.execute("""
                SELECT 
                    id, date, year, aircraft_model, aircraft_tail, aircraft_type,
                    num_seats, dep_code, arr_code, dep_location, arr_location,
                    flight_no, pass_position, unique_id, first_name, last_name,
                    last_first, first_last, comment, initials, known, data_source
                FROM core.flight_logs
                ORDER BY id
            """)
            
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            
            print(f"  Processing {len(rows)} L0 records...")
            
            # Track unique flights
            flights_seen = {}  # flight_id -> flight_data
            passengers = []
            
            # Counters
            stats = {
                "confidence_1.0": 0,
                "confidence_0.7": 0,
                "confidence_0.3": 0,
                "confidence_0.1": 0,
                "confidence_0.0": 0,
                "potential_victims": 0,
                "suppressed": 0
            }
            
            for row_tuple in rows:
                row = dict(zip(columns, row_tuple))
                
                # Generate flight ID
                flight_id = generate_flight_id(row)
                
                # Extract flight if not seen
                if flight_id not in flights_seen:
                    flights_seen[flight_id] = {
                        "flight_id": flight_id,
                        "flight_date": normalize_date(row["date"]),
                        "flight_date_raw": row["date"],
                        "year": row["year"],
                        "aircraft_model": row["aircraft_model"],
                        "aircraft_tail": row["aircraft_tail"],
                        "aircraft_type": row["aircraft_type"],
                        "num_seats": row["num_seats"],
                        "dep_code": row["dep_code"],
                        "arr_code": row["arr_code"],
                        "dep_location": row["dep_location"],
                        "arr_location": row["arr_location"],
                        "flight_no": row["flight_no"],
                        "data_source": row["data_source"]
                    }
                
                # Compute transforms
                confidence = compute_identity_confidence(row)
                potential_victim, suppress = compute_victim_flags(row, confidence)
                
                # Track stats
                stats[f"confidence_{confidence}"] += 1
                if potential_victim:
                    stats["potential_victims"] += 1
                if suppress:
                    stats["suppressed"] += 1
                
                # Generate passenger ID
                passenger_id = str(uuid.uuid4())
                
                passengers.append({
                    "passenger_id": passenger_id,
                    "flight_id": flight_id,
                    "l0_id": row["id"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "first_last": row["first_last"],
                    "initials": row["initials"],
                    "pass_position": row["pass_position"],
                    "comment": row["comment"],
                    "identity_confidence": confidence,
                    "known": row["known"],
                    "potential_victim": potential_victim,
                    "suppress_from_public": suppress
                })
            
            print(f"  Extracted {len(flights_seen)} unique flights")
            print(f"  Extracted {len(passengers)} passenger records")
            
            # Print stats
            print("\n  Identity confidence distribution:")
            print(f"    1.0 (verified):    {stats['confidence_1.0']:,}")
            print(f"    0.7 (unverified):  {stats['confidence_0.7']:,}")
            print(f"    0.3 (initials):    {stats['confidence_0.3']:,}")
            print(f"    0.1 (descriptive): {stats['confidence_0.1']:,}")
            print(f"    0.0 (unknown):     {stats['confidence_0.0']:,}")
            print(f"\n  Victim protection:")
            print(f"    Potential victims: {stats['potential_victims']}")
            print(f"    Suppressed:        {stats['suppressed']}")
            
            if dry_run:
                print("\n  [DRY RUN] No data written")
                return
            
            # Insert flights
            print("\n  Inserting flight events...")
            flight_cols = [
                "flight_id", "flight_date", "flight_date_raw", "year",
                "aircraft_model", "aircraft_tail", "aircraft_type", "num_seats",
                "dep_code", "arr_code", "dep_location", "arr_location",
                "flight_no", "data_source"
            ]
            flight_placeholders = ", ".join(["%s"] * len(flight_cols))
            flight_insert = f"""
                INSERT INTO l1.flight_events ({", ".join(flight_cols)})
                VALUES ({flight_placeholders})
            """
            
            flight_rows = [
                tuple(f[col] for col in flight_cols)
                for f in flights_seen.values()
            ]
            cur.executemany(flight_insert, flight_rows)  # type: ignore[arg-type]
            
            # Insert passengers
            print("  Inserting passenger records...")
            pass_cols = [
                "passenger_id", "flight_id", "l0_id", "first_name", "last_name",
                "first_last", "initials", "pass_position", "comment",
                "identity_confidence", "known", "potential_victim", "suppress_from_public"
            ]
            pass_placeholders = ", ".join(["%s"] * len(pass_cols))
            pass_insert = f"""
                INSERT INTO l1.flight_passengers ({", ".join(pass_cols)})
                VALUES ({pass_placeholders})
            """
            
            pass_rows = [
                tuple(p[col] for col in pass_cols)
                for p in passengers
            ]
            cur.executemany(pass_insert, pass_rows)  # type: ignore[arg-type]
            
            conn.commit()
            
            # Verify
            cur.execute("SELECT COUNT(*) FROM l1.flight_events")
            row = cur.fetchone()
            event_count = row[0] if row else 0
            
            cur.execute("SELECT COUNT(*) FROM l1.flight_passengers")
            row = cur.fetchone()
            pass_count = row[0] if row else 0
            
            cur.execute("SELECT COUNT(*) FROM l1.flight_passengers_public")
            row = cur.fetchone()
            public_count = row[0] if row else 0
            
            print(f"\n  ✓ Inserted {event_count} flight events")
            print(f"  ✓ Inserted {pass_count} passenger records")
            print(f"  ✓ Public view contains {public_count} records ({pass_count - public_count} suppressed)")


def main():
    parser = argparse.ArgumentParser(description="Transform flight logs to L1")
    parser.add_argument("--dry-run", action="store_true",
                        help="Process without writing to database")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Epstein Files ARD - Flight Logs L1 Transform")
    print("=" * 60)
    
    try:
        transform_flight_logs(dry_run=args.dry_run)
        print("\n✓ Transform completed successfully")
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
