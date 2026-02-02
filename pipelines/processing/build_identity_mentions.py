#!/usr/bin/env python3
"""
Build Unified Identity Mentions Table

Extracts names from:
- l1.flight_passengers
- l1.contact_persons

Parses with probablepeople and creates l1.identity_mentions with:
- Parsed name components
- Soundex codes for blocking
- Placeholder vector column for M06 embeddings

Usage:
    python build_identity_mentions.py [--dry-run]

Requirements:
    pip install psycopg[binary] python-dotenv probablepeople
"""

import argparse
import os
import sys
import uuid
from pathlib import Path

import psycopg
from dotenv import load_dotenv

try:
    import probablepeople as pp
    PROBABLEPEOPLE_AVAILABLE = True
except ImportError:
    PROBABLEPEOPLE_AVAILABLE = False
    print("WARNING: probablepeople library not installed. Name parsing will be limited.")

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
# Name Parsing
# =============================================================================

def parse_name_with_probablepeople(full_name: str) -> dict:
    """
    Parse a name using probablepeople CRF model.
    
    Returns dict with:
    - parsed_prefix, parsed_first, parsed_middle, parsed_last, parsed_suffix
    - parsed_nickname
    - parse_type: 'Person', 'Corporation', or 'Unknown'
    - parse_confidence: 0.0-1.0
    """
    if not PROBABLEPEOPLE_AVAILABLE:
        return fallback_parse(full_name)
    
    if not full_name or not full_name.strip():
        return {
            "parsed_prefix": None,
            "parsed_first": None,
            "parsed_middle": None,
            "parsed_last": None,
            "parsed_suffix": None,
            "parsed_nickname": None,
            "parse_type": "Unknown",
            "parse_confidence": 0.0
        }
    
    full_name = full_name.strip()
    
    try:
        parsed, name_type = pp.tag(full_name)
        
        return {
            "parsed_prefix": parsed.get("PrefixMarital") or parsed.get("PrefixOther"),
            "parsed_first": parsed.get("GivenName"),
            "parsed_middle": parsed.get("MiddleName"),
            "parsed_last": parsed.get("Surname"),
            "parsed_suffix": parsed.get("SuffixGenerational") or parsed.get("SuffixOther"),
            "parsed_nickname": parsed.get("Nickname"),
            "parse_type": name_type,
            "parse_confidence": 0.9 if name_type == "Person" else 0.5
        }
        
    except pp.RepeatedLabelError:
        # Ambiguous parse - fall back
        return fallback_parse(full_name)
    except Exception:
        return fallback_parse(full_name)


def fallback_parse(full_name: str) -> dict:
    """
    Simple fallback parser when probablepeople fails.
    
    Handles:
    - "Last, First" format
    - "First Last" format
    """
    if not full_name or not full_name.strip():
        return {
            "parsed_prefix": None,
            "parsed_first": None,
            "parsed_middle": None,
            "parsed_last": None,
            "parsed_suffix": None,
            "parsed_nickname": None,
            "parse_type": "Unknown",
            "parse_confidence": 0.0
        }
    
    full_name = full_name.strip()
    
    # Try "Last, First" format
    if "," in full_name:
        parts = full_name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip() if len(parts) > 1 else None
        return {
            "parsed_prefix": None,
            "parsed_first": first,
            "parsed_middle": None,
            "parsed_last": last,
            "parsed_suffix": None,
            "parsed_nickname": None,
            "parse_type": "Person",
            "parse_confidence": 0.5
        }
    
    # Try "First Last" format
    parts = full_name.split()
    if len(parts) >= 2:
        return {
            "parsed_prefix": None,
            "parsed_first": parts[0],
            "parsed_middle": " ".join(parts[1:-1]) if len(parts) > 2 else None,
            "parsed_last": parts[-1],
            "parsed_suffix": None,
            "parsed_nickname": None,
            "parse_type": "Person",
            "parse_confidence": 0.3
        }
    
    # Single word - assume last name
    return {
        "parsed_prefix": None,
        "parsed_first": None,
        "parsed_middle": None,
        "parsed_last": full_name,
        "parsed_suffix": None,
        "parsed_nickname": None,
        "parse_type": "Unknown",
        "parse_confidence": 0.1
    }


# =============================================================================
# DDL
# =============================================================================

IDENTITY_MENTIONS_DDL = """
CREATE TABLE IF NOT EXISTS l1.identity_mentions (
    mention_id UUID PRIMARY KEY,
    
    -- Source tracking
    source_table VARCHAR(50) NOT NULL,  -- 'flight_passengers' or 'contact_persons'
    source_id UUID NOT NULL,            -- passenger_id or person_id
    l0_source_table VARCHAR(50),        -- 'flight_logs' or 'black_book'
    l0_source_id TEXT,                  -- L0 record identifier
    
    -- Raw name as extracted
    raw_name TEXT,
    
    -- Parsed components (from probablepeople)
    parsed_prefix VARCHAR(20),
    parsed_first VARCHAR(100),
    parsed_middle VARCHAR(100),
    parsed_last VARCHAR(100),
    parsed_suffix VARCHAR(20),
    parsed_nickname VARCHAR(100),
    
    -- Parse metadata
    parse_type VARCHAR(20),       -- 'Person', 'Corporation', 'Unknown'
    parse_confidence DECIMAL(3,2),
    
    -- Blocking codes (for entity resolution)
    soundex_first VARCHAR(4),
    soundex_last VARCHAR(4),
    
    -- Placeholder for M06 embeddings
    name_embedding vector(384),   -- Will be populated in M06
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for entity resolution blocking
CREATE INDEX IF NOT EXISTS idx_identity_mentions_soundex 
    ON l1.identity_mentions(soundex_last, soundex_first);

CREATE INDEX IF NOT EXISTS idx_identity_mentions_source 
    ON l1.identity_mentions(source_table, source_id);

CREATE INDEX IF NOT EXISTS idx_identity_mentions_name 
    ON l1.identity_mentions(parsed_last, parsed_first);

CREATE INDEX IF NOT EXISTS idx_identity_mentions_confidence 
    ON l1.identity_mentions(parse_confidence);

-- Note: Vector index will be created in M06 after embeddings are populated
-- CREATE INDEX idx_identity_mentions_embedding 
--     ON l1.identity_mentions USING ivfflat (name_embedding vector_cosine_ops);
"""


def create_tables(conn):
    """Create identity mentions table."""
    print("Creating l1.identity_mentions table...")
    
    with conn.cursor() as cur:
        cur.execute(IDENTITY_MENTIONS_DDL)
        print("  Created l1.identity_mentions with Soundex indexes")
    
    conn.commit()


# =============================================================================
# Main Build
# =============================================================================

def build_identity_mentions(dry_run: bool = False):
    """
    Build unified identity mentions from flight passengers and contact persons.
    """
    print("Building unified identity mentions...")
    
    with get_connection() as conn:
        # Create table
        create_tables(conn)
        
        with conn.cursor() as cur:
            # Clear existing data
            if not dry_run:
                cur.execute("TRUNCATE l1.identity_mentions")
            
            mentions = []
            stats = {
                "flight_passengers": 0,
                "contact_persons": 0,
                "high_confidence": 0,
                "low_confidence": 0,
            }
            parse_types = {}  # Track dynamically
            
            # =================================================================
            # Extract from flight_passengers
            # =================================================================
            print("\n  Extracting from l1.flight_passengers...")
            
            cur.execute("""
                SELECT 
                    fp.passenger_id,
                    fp.l0_id,
                    fp.first_name,
                    fp.last_name,
                    fp.first_last,
                    fp.identity_confidence
                FROM l1.flight_passengers fp
                WHERE fp.identity_confidence >= 0.3  -- Skip unknowns and descriptives
            """)
            
            flight_rows = cur.fetchall()
            print(f"    Found {len(flight_rows)} passenger records (confidence >= 0.3)")
            
            for row in flight_rows:
                passenger_id, l0_id, first_name, last_name, first_last, identity_conf = row
                
                # Use first_last as the canonical name to parse
                raw_name = first_last or f"{first_name or ''} {last_name or ''}".strip()
                
                if not raw_name:
                    continue
                
                parsed = parse_name_with_probablepeople(raw_name)
                
                # Override with known components if parse failed
                if not parsed["parsed_first"] and first_name:
                    parsed["parsed_first"] = first_name
                if not parsed["parsed_last"] and last_name:
                    parsed["parsed_last"] = last_name
                
                # Soundex codes will be computed via SQL function after insert
                
                mention = {
                    "mention_id": str(uuid.uuid4()),
                    "source_table": "flight_passengers",
                    "source_id": str(passenger_id),
                    "l0_source_table": "flight_logs",
                    "l0_source_id": str(l0_id),
                    "raw_name": raw_name,
                    "parsed_prefix": parsed["parsed_prefix"],
                    "parsed_first": parsed["parsed_first"],
                    "parsed_middle": parsed["parsed_middle"],
                    "parsed_last": parsed["parsed_last"],
                    "parsed_suffix": parsed["parsed_suffix"],
                    "parsed_nickname": parsed["parsed_nickname"],
                    "parse_type": parsed["parse_type"],
                    "parse_confidence": parsed["parse_confidence"],
                }
                
                mentions.append(mention)
                stats["flight_passengers"] += 1
                
                # Track parse type dynamically
                ptype = parsed['parse_type'].lower()
                parse_types[ptype] = parse_types.get(ptype, 0) + 1
                
                if parsed["parse_confidence"] >= 0.7:
                    stats["high_confidence"] += 1
                else:
                    stats["low_confidence"] += 1
            
            # =================================================================
            # Extract from contact_persons
            # =================================================================
            print("\n  Extracting from l1.contact_persons...")
            
            cur.execute("""
                SELECT 
                    cp.person_id,
                    cp.l0_record_id,
                    cp.extracted_first,
                    cp.extracted_last,
                    cp.extracted_raw,
                    c.entity_type
                FROM l1.contact_persons cp
                JOIN l1.contacts c ON cp.contact_id = c.contact_id
                WHERE c.entity_type IN ('individual', 'household')  -- Skip organizations
            """)
            
            contact_rows = cur.fetchall()
            print(f"    Found {len(contact_rows)} contact person records")
            
            for row in contact_rows:
                person_id, l0_record_id, first, last, raw, entity_type = row
                
                # Build name to parse
                if raw and raw.strip():
                    raw_name = raw.strip()
                elif first or last:
                    raw_name = f"{first or ''} {last or ''}".strip()
                else:
                    continue
                
                parsed = parse_name_with_probablepeople(raw_name)
                
                # Override with extracted components if available
                if not parsed["parsed_first"] and first:
                    parsed["parsed_first"] = first
                if not parsed["parsed_last"] and last:
                    parsed["parsed_last"] = last
                
                mention = {
                    "mention_id": str(uuid.uuid4()),
                    "source_table": "contact_persons",
                    "source_id": str(person_id),
                    "l0_source_table": "black_book",
                    "l0_source_id": str(l0_record_id),
                    "raw_name": raw_name,
                    "parsed_prefix": parsed["parsed_prefix"],
                    "parsed_first": parsed["parsed_first"],
                    "parsed_middle": parsed["parsed_middle"],
                    "parsed_last": parsed["parsed_last"],
                    "parsed_suffix": parsed["parsed_suffix"],
                    "parsed_nickname": parsed["parsed_nickname"],
                    "parse_type": parsed["parse_type"],
                    "parse_confidence": parsed["parse_confidence"],
                }
                
                mentions.append(mention)
                stats["contact_persons"] += 1
                
                # Track parse type dynamically
                ptype = parsed['parse_type'].lower()
                parse_types[ptype] = parse_types.get(ptype, 0) + 1
                
                if parsed["parse_confidence"] >= 0.7:
                    stats["high_confidence"] += 1
                else:
                    stats["low_confidence"] += 1
            
            # =================================================================
            # Print stats
            # =================================================================
            print(f"\n  Source distribution:")
            print(f"    Flight passengers: {stats['flight_passengers']:,}")
            print(f"    Contact persons:   {stats['contact_persons']:,}")
            print(f"    Total:             {len(mentions):,}")
            
            print(f"\n  Parse type distribution:")
            for ptype, count in sorted(parse_types.items(), key=lambda x: -x[1]):
                print(f"    {ptype.capitalize():12} {count:,}")
            
            print(f"\n  Confidence distribution:")
            print(f"    High (>=0.7): {stats['high_confidence']:,}")
            print(f"    Low (<0.7):   {stats['low_confidence']:,}")
            
            if dry_run:
                print("\n  [DRY RUN] No data written")
                return
            
            # =================================================================
            # Insert mentions
            # =================================================================
            print("\n  Inserting identity mentions...")
            
            cols = [
                "mention_id", "source_table", "source_id", "l0_source_table",
                "l0_source_id", "raw_name", "parsed_prefix", "parsed_first",
                "parsed_middle", "parsed_last", "parsed_suffix", "parsed_nickname",
                "parse_type", "parse_confidence"
            ]
            placeholders = ", ".join(["%s"] * len(cols))
            insert_sql = f"""
                INSERT INTO l1.identity_mentions ({", ".join(cols)})
                VALUES ({placeholders})
            """
            
            rows_to_insert = [
                tuple(m[col] for col in cols)
                for m in mentions
            ]
            
            # Batch insert
            batch_size = 1000
            for i in range(0, len(rows_to_insert), batch_size):
                batch = rows_to_insert[i:i + batch_size]
                cur.executemany(insert_sql, batch)
            
            # =================================================================
            # Update Soundex codes via SQL
            # =================================================================
            print("  Computing Soundex codes...")
            
            cur.execute("""
                UPDATE l1.identity_mentions
                SET 
                    soundex_first = soundex(parsed_first),
                    soundex_last = soundex(parsed_last)
                WHERE parsed_first IS NOT NULL OR parsed_last IS NOT NULL
            """)
            
            conn.commit()
            
            # =================================================================
            # Verify
            # =================================================================
            cur.execute("SELECT COUNT(*) FROM l1.identity_mentions")
            total_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM l1.identity_mentions 
                WHERE soundex_last IS NOT NULL
            """)
            soundex_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(DISTINCT soundex_last) FROM l1.identity_mentions 
                WHERE soundex_last IS NOT NULL
            """)
            unique_soundex = cur.fetchone()[0]
            
            print(f"\n  ✓ Inserted {total_count:,} identity mentions")
            print(f"  ✓ {soundex_count:,} have Soundex codes")
            print(f"  ✓ {unique_soundex:,} unique surname Soundex codes (blocking groups)")


def main():
    parser = argparse.ArgumentParser(description="Build unified identity mentions")
    parser.add_argument("--dry-run", action="store_true",
                        help="Process without writing to database")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Epstein Files ARD - Build Identity Mentions")
    print("=" * 60)
    
    if not PROBABLEPEOPLE_AVAILABLE:
        print("\nWARNING: Install probablepeople for better name parsing:")
        print("  pip install probablepeople")
        print()
    
    try:
        build_identity_mentions(dry_run=args.dry_run)
        print("\n✓ Build completed successfully")
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
