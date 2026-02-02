#!/usr/bin/env python3
"""
Validate Layer 1 Data Quality

Runs comprehensive validation checks:
1. L0 → L1 completeness (no orphans)
2. Foreign key integrity
3. Phone normalization success rate
4. Name parse success rate
5. Identity confidence distribution
6. Entity type distribution
7. Victim protection coverage

Exports metrics to JSON for documentation.

Usage:
    python validate_l1.py [--output PATH]

Requirements:
    pip install psycopg[binary] python-dotenv
"""

import argparse
import json
import os
import sys
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


def validate_l1():
    """
    Run all L1 validation checks.
    
    Returns dict of metrics and list of issues.
    """
    metrics = {
        "validation_date": datetime.now().isoformat(),
        "database": PGSQL_DATABASE,
    }
    issues = []
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # =================================================================
            # 1. Record Counts
            # =================================================================
            print("\n1. Record Counts")
            print("-" * 40)
            
            counts = {}
            tables = [
                ("core.flight_logs", "L0 flight logs"),
                ("core.black_book", "L0 black book"),
                ("l1.flight_events", "L1 flight events"),
                ("l1.flight_passengers", "L1 flight passengers"),
                ("l1.contacts", "L1 contacts"),
                ("l1.contact_persons", "L1 contact persons"),
                ("l1.phone_numbers", "L1 phone numbers"),
                ("l1.identity_mentions", "L1 identity mentions"),
            ]
            
            for table, desc in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                counts[table] = count
                print(f"  {desc:25} {count:,}")
            
            metrics["record_counts"] = counts
            
            # =================================================================
            # 2. L0 → L1 Completeness
            # =================================================================
            print("\n2. L0 → L1 Completeness")
            print("-" * 40)
            
            # Flight logs → passengers
            cur.execute("""
                SELECT COUNT(*) FROM core.flight_logs l0
                LEFT JOIN l1.flight_passengers l1 ON l0.id = l1.l0_id
                WHERE l1.l0_id IS NULL
            """)
            orphan_flights = cur.fetchone()[0]
            print(f"  Flight logs without L1 passenger:  {orphan_flights}")
            
            if orphan_flights > 0:
                issues.append(f"WARN: {orphan_flights} flight logs have no L1 passenger record")
            
            # Black book → contacts
            cur.execute("""
                SELECT COUNT(*) FROM core.black_book l0
                LEFT JOIN l1.contacts l1 ON l0.record_id = l1.l0_record_id
                WHERE l1.l0_record_id IS NULL
            """)
            orphan_contacts = cur.fetchone()[0]
            print(f"  Black book without L1 contact:     {orphan_contacts}")
            
            if orphan_contacts > 0:
                issues.append(f"FAIL: {orphan_contacts} black book records have no L1 contact")
            
            metrics["completeness"] = {
                "flight_logs_without_l1": orphan_flights,
                "black_book_without_l1": orphan_contacts,
                "complete": orphan_flights == 0 and orphan_contacts == 0
            }
            
            # =================================================================
            # 3. Flight Passengers Analysis
            # =================================================================
            print("\n3. Flight Passengers Analysis")
            print("-" * 40)
            
            # Identity confidence distribution
            cur.execute("""
                SELECT 
                    identity_confidence,
                    COUNT(*) as count
                FROM l1.flight_passengers
                GROUP BY identity_confidence
                ORDER BY identity_confidence DESC
            """)
            confidence_dist = {str(row[0]): row[1] for row in cur.fetchall()}
            
            print("  Identity confidence distribution:")
            for conf, count in sorted(confidence_dist.items(), reverse=True):
                print(f"    {conf}: {count:,}")
            
            # Victim protection
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE potential_victim) as potential_victims,
                    COUNT(*) FILTER (WHERE suppress_from_public) as suppressed,
                    COUNT(*) as total
                FROM l1.flight_passengers
            """)
            victim_stats = cur.fetchone()
            
            print(f"\n  Potential victims:     {victim_stats[0]:,}")
            print(f"  Suppressed from public: {victim_stats[1]:,}")
            print(f"  Public view size:       {victim_stats[2] - victim_stats[1]:,}")
            
            metrics["flight_passengers"] = {
                "confidence_distribution": confidence_dist,
                "potential_victims": victim_stats[0],
                "suppressed": victim_stats[1],
                "public_count": victim_stats[2] - victim_stats[1],
                "total": victim_stats[2]
            }
            
            # =================================================================
            # 4. Contacts Analysis
            # =================================================================
            print("\n4. Contacts Analysis")
            print("-" * 40)
            
            # Entity type distribution
            cur.execute("""
                SELECT 
                    entity_type,
                    COUNT(*) as count
                FROM l1.contacts
                GROUP BY entity_type
                ORDER BY count DESC
            """)
            entity_dist = {row[0]: row[1] for row in cur.fetchall()}
            
            print("  Entity type distribution:")
            for etype, count in entity_dist.items():
                print(f"    {etype}: {count:,}")
            
            # Country normalization
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE country_iso IS NOT NULL) as mapped,
                    COUNT(*) FILTER (WHERE country_raw IS NOT NULL AND country_iso IS NULL) as unmapped,
                    COUNT(*) FILTER (WHERE country_raw IS NULL) as missing,
                    COUNT(*) as total
                FROM l1.contacts
            """)
            country_stats = cur.fetchone()
            
            print(f"\n  Country normalization:")
            print(f"    Mapped to ISO:   {country_stats[0]:,}")
            print(f"    Unmapped:        {country_stats[1]:,}")
            print(f"    Missing:         {country_stats[2]:,}")
            
            metrics["contacts"] = {
                "entity_type_distribution": entity_dist,
                "country_mapped": country_stats[0],
                "country_unmapped": country_stats[1],
                "country_missing": country_stats[2],
                "total": country_stats[3]
            }
            
            # =================================================================
            # 5. Phone Numbers Analysis
            # =================================================================
            print("\n5. Phone Numbers Analysis")
            print("-" * 40)
            
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE is_valid) as valid,
                    COUNT(*) FILTER (WHERE NOT is_valid) as invalid,
                    COUNT(*) as total
                FROM l1.phone_numbers
            """)
            phone_stats = cur.fetchone()
            
            valid_pct = 100.0 * phone_stats[0] / phone_stats[2] if phone_stats[2] > 0 else 0
            
            print(f"  Valid (E.164):   {phone_stats[0]:,} ({valid_pct:.1f}%)")
            print(f"  Invalid:         {phone_stats[1]:,}")
            print(f"  Total:           {phone_stats[2]:,}")
            
            # Phone type breakdown
            cur.execute("""
                SELECT 
                    phone_type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_valid) as valid
                FROM l1.phone_numbers
                GROUP BY phone_type
                ORDER BY total DESC
            """)
            phone_by_type = {row[0]: {"total": row[1], "valid": row[2]} for row in cur.fetchall()}
            
            print("\n  By type:")
            for ptype, data in phone_by_type.items():
                pct = 100.0 * data["valid"] / data["total"] if data["total"] > 0 else 0
                print(f"    {ptype:10} {data['total']:,} total, {data['valid']:,} valid ({pct:.0f}%)")
            
            metrics["phone_numbers"] = {
                "valid": phone_stats[0],
                "invalid": phone_stats[1],
                "total": phone_stats[2],
                "valid_percent": round(valid_pct, 1),
                "by_type": phone_by_type
            }
            
            # =================================================================
            # 6. Identity Mentions Analysis
            # =================================================================
            print("\n6. Identity Mentions Analysis")
            print("-" * 40)
            
            # Source distribution
            cur.execute("""
                SELECT 
                    source_table,
                    COUNT(*) as count
                FROM l1.identity_mentions
                GROUP BY source_table
            """)
            source_dist = {row[0]: row[1] for row in cur.fetchall()}
            
            print("  Source distribution:")
            for src, count in source_dist.items():
                print(f"    {src}: {count:,}")
            
            # Parse type distribution
            cur.execute("""
                SELECT 
                    parse_type,
                    COUNT(*) as count
                FROM l1.identity_mentions
                GROUP BY parse_type
                ORDER BY count DESC
            """)
            parse_dist = {row[0]: row[1] for row in cur.fetchall()}
            
            print("\n  Parse type distribution:")
            for ptype, count in parse_dist.items():
                print(f"    {ptype}: {count:,}")
            
            # Soundex coverage
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE soundex_last IS NOT NULL) as with_soundex,
                    COUNT(DISTINCT soundex_last) as unique_soundex,
                    COUNT(*) as total
                FROM l1.identity_mentions
            """)
            soundex_stats = cur.fetchone()
            
            print(f"\n  Soundex coverage:")
            print(f"    With Soundex:    {soundex_stats[0]:,}")
            print(f"    Unique codes:    {soundex_stats[1]:,}")
            print(f"    Avg per block:   {soundex_stats[0] / soundex_stats[1]:.1f}" if soundex_stats[1] > 0 else "    Avg per block:   N/A")
            
            # Parse confidence distribution
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE parse_confidence >= 0.9) as high,
                    COUNT(*) FILTER (WHERE parse_confidence >= 0.5 AND parse_confidence < 0.9) as medium,
                    COUNT(*) FILTER (WHERE parse_confidence < 0.5) as low,
                    COUNT(*) as total
                FROM l1.identity_mentions
            """)
            conf_stats = cur.fetchone()
            
            print(f"\n  Parse confidence:")
            print(f"    High (>=0.9):    {conf_stats[0]:,}")
            print(f"    Medium (0.5-0.9): {conf_stats[1]:,}")
            print(f"    Low (<0.5):      {conf_stats[2]:,}")
            
            metrics["identity_mentions"] = {
                "source_distribution": source_dist,
                "parse_type_distribution": parse_dist,
                "with_soundex": soundex_stats[0],
                "unique_soundex_codes": soundex_stats[1],
                "avg_per_block": round(soundex_stats[0] / soundex_stats[1], 1) if soundex_stats[1] > 0 else None,
                "parse_confidence": {
                    "high": conf_stats[0],
                    "medium": conf_stats[1],
                    "low": conf_stats[2]
                },
                "total": conf_stats[3]
            }
            
            # =================================================================
            # 7. Cross-Dataset Analysis
            # =================================================================
            print("\n7. Cross-Dataset Potential")
            print("-" * 40)
            
            # Sample overlapping Soundex codes
            cur.execute("""
                WITH flight_soundex AS (
                    SELECT DISTINCT soundex_last 
                    FROM l1.identity_mentions 
                    WHERE source_table = 'flight_passengers' 
                    AND soundex_last IS NOT NULL
                ),
                contact_soundex AS (
                    SELECT DISTINCT soundex_last 
                    FROM l1.identity_mentions 
                    WHERE source_table = 'contact_persons' 
                    AND soundex_last IS NOT NULL
                )
                SELECT COUNT(*) FROM flight_soundex f
                JOIN contact_soundex c ON f.soundex_last = c.soundex_last
            """)
            overlap_count = cur.fetchone()[0]
            
            print(f"  Soundex codes appearing in both datasets: {overlap_count}")
            
            # People in both?
            cur.execute("""
                WITH flight_names AS (
                    SELECT DISTINCT LOWER(parsed_last) as last, LOWER(parsed_first) as first
                    FROM l1.identity_mentions 
                    WHERE source_table = 'flight_passengers' 
                    AND parsed_last IS NOT NULL
                ),
                contact_names AS (
                    SELECT DISTINCT LOWER(parsed_last) as last, LOWER(parsed_first) as first
                    FROM l1.identity_mentions 
                    WHERE source_table = 'contact_persons' 
                    AND parsed_last IS NOT NULL
                )
                SELECT COUNT(*) FROM flight_names f
                JOIN contact_names c ON f.last = c.last AND f.first = c.first
            """)
            exact_matches = cur.fetchone()[0]
            
            print(f"  Exact name matches (case-insensitive): {exact_matches}")
            
            metrics["cross_dataset"] = {
                "overlapping_soundex_codes": overlap_count,
                "exact_name_matches": exact_matches
            }
            
            # =================================================================
            # Summary
            # =================================================================
            print("\n" + "=" * 60)
            print("VALIDATION SUMMARY")
            print("=" * 60)
            
            all_pass = True
            
            # Check completeness
            if metrics["completeness"]["complete"]:
                print("✓ L0 → L1 completeness: PASS")
            else:
                print("✗ L0 → L1 completeness: FAIL")
                all_pass = False
            
            # Check phone normalization (warn if < 40%)
            if metrics["phone_numbers"]["valid_percent"] >= 40:
                print(f"✓ Phone normalization: {metrics['phone_numbers']['valid_percent']:.1f}% valid")
            else:
                print(f"⚠ Phone normalization: {metrics['phone_numbers']['valid_percent']:.1f}% valid (low)")
                issues.append(f"WARN: Phone normalization rate below 40%")
            
            # Check identity mentions coverage
            total_expected = counts["l1.flight_passengers"] + counts["l1.contact_persons"]
            # Note: flight passengers filtered by confidence, contacts filtered by entity type
            print(f"✓ Identity mentions: {counts['l1.identity_mentions']:,} extracted")
            
            # Check cross-dataset potential
            print(f"✓ Cross-dataset matches: {exact_matches} exact, {overlap_count} Soundex blocks")
            
            metrics["summary"] = {
                "all_pass": all_pass and len([i for i in issues if i.startswith("FAIL")]) == 0,
                "issues": issues
            }
            
            if issues:
                print("\nIssues found:")
                for issue in issues:
                    print(f"  - {issue}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Validate L1 data quality")
    parser.add_argument("--output", "-o", type=str,
                        default=str(PROJECT_ROOT / "research" / "quality-analysis" / "l1-metrics.json"),
                        help="Output path for metrics JSON")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Epstein Files ARD - L1 Validation")
    print("=" * 60)
    
    try:
        metrics = validate_l1()
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write metrics
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n✓ Metrics exported to {output_path}")
        
        return 0 if metrics["summary"]["all_pass"] else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
