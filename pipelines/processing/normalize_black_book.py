#!/usr/bin/env python3
"""
Normalize Black Book CSV for Layer 0

Minimal transformation of the epsteinsblackbook.com extraction:
- Remove exact duplicate rows
- Add record_id for L0 consistency
- Validate schema
- Preserve all original columns (transformations happen in PostgreSQL)

Source: epsteinsblackbook.com (Wayback Machine archived images)
Provenance: Page-Link column contains per-page image URLs

Usage:
    python pipelines/processing/normalize_black_book.py
    python pipelines/processing/normalize_black_book.py --verify-only

Output:
    data/layer-0-canonical/black-book.csv

Author: Epstein Files ARD Project
Date: 2026-02-01
"""

import argparse
import csv
import hashlib
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "data" / "raw" / "epsteinsblackbook-com" / "black-book-lines.csv"
OUTPUT_CSV = REPO_ROOT / "data" / "layer-0-canonical" / "black-book.csv"

# Expected schema (16 columns from source + 1 added)
SOURCE_COLUMNS = [
    "Page",
    "Page-Link",
    "Name",
    "Company/Add. Text",
    "Surname",
    "First Name",
    "Address-Type",
    "Address",
    "Zip",
    "City",
    "Country",
    "Phone (no specifics)",
    "Phone (w) – work",
    "Phone (h) – home",
    "Phone (p) – portable/mobile",
    "Email",
]

OUTPUT_COLUMNS = ["record_id"] + SOURCE_COLUMNS


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_and_dedupe(csv_path: Path) -> tuple[list[str], list[dict]]:
    """
    Load CSV and remove exact duplicate rows.
    
    Returns:
        tuple: (header, deduplicated_rows_as_dicts)
    """
    print(f"Loading: {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    
    print(f"  Loaded {len(rows)} rows")
    
    # Dedupe by converting to tuple for hashing
    seen = set()
    unique_rows = []
    duplicates = 0
    
    for row in rows:
        row_tuple = tuple(row.values())
        if row_tuple not in seen:
            seen.add(row_tuple)
            unique_rows.append(row)
        else:
            duplicates += 1
    
    print(f"  Removed {duplicates} exact duplicates")
    print(f"  Unique rows: {len(unique_rows)}")
    
    return header, unique_rows


def add_record_ids(rows: list[dict]) -> list[dict]:
    """Add deterministic UUIDs based on row content."""
    for row in rows:
        # Create deterministic UUID from row content
        content = "|".join(str(v) for v in row.values())
        # Use sha256 for consistency and best practice, then truncate for UUID
        row_hash = hashlib.sha256(content.encode()).hexdigest()
        row["record_id"] = str(uuid.UUID(row_hash[:32]))
    return rows


def validate_data(header: list[str], rows: list[dict]) -> dict:
    """
    Validate data against expected schema.
    
    Returns:
        dict: Validation results with pass/fail and metrics
    """
    results = {
        "passed": True,
        "errors": [],
        "warnings": [],
        "metrics": {},
    }
    
    # Check header columns
    missing = set(SOURCE_COLUMNS) - set(header)
    extra = set(header) - set(SOURCE_COLUMNS)
    if missing:
        results["errors"].append(f"Missing columns: {missing}")
        results["passed"] = False
    if extra:
        results["warnings"].append(f"Extra columns: {extra}")
    
    # Compute metrics
    results["metrics"]["total_rows"] = len(rows)
    results["metrics"]["unique_names"] = len(set(r["Name"] for r in rows if r["Name"]))
    results["metrics"]["unique_surnames"] = len(set(r["Surname"] for r in rows if r["Surname"]))
    
    # Page coverage
    pages = [int(r["Page"]) for r in rows if r["Page"]]
    if pages:
        results["metrics"]["page_range"] = f"{min(pages)} - {max(pages)}"
        results["metrics"]["unique_pages"] = len(set(pages))
    
    # Country distribution
    countries = {}
    for r in rows:
        c = r["Country"].strip() if r["Country"] else "Unknown"
        countries[c] = countries.get(c, 0) + 1
    results["metrics"]["top_countries"] = dict(
        sorted(countries.items(), key=lambda x: -x[1])[:5]
    )
    
    # Data completeness
    has_phone = sum(
        1 for r in rows 
        if any([
            r["Phone (no specifics)"],
            r["Phone (w) – work"],
            r["Phone (h) – home"],
            r["Phone (p) – portable/mobile"],
        ])
    )
    has_email = sum(1 for r in rows if r["Email"])
    has_address = sum(1 for r in rows if r["Address"])
    
    results["metrics"]["phone_coverage"] = f"{has_phone} ({has_phone/len(rows)*100:.1f}%)"
    results["metrics"]["email_coverage"] = f"{has_email} ({has_email/len(rows)*100:.1f}%)"
    results["metrics"]["address_coverage"] = f"{has_address} ({has_address/len(rows)*100:.1f}%)"
    
    # Sanity checks
    if results["metrics"]["total_rows"] < 2000:
        results["warnings"].append(
            f"Row count ({results['metrics']['total_rows']}) lower than expected (~2300)"
        )
    
    # Check provenance links
    has_provenance = sum(1 for r in rows if r["Page-Link"])
    if has_provenance < len(rows) * 0.95:
        results["warnings"].append(
            f"Only {has_provenance}/{len(rows)} rows have Page-Link provenance"
        )
    
    return results


def write_csv(rows: list[dict], output_path: Path) -> None:
    """Write normalized data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Wrote {len(rows)} rows to {output_path}")


def print_validation_report(results: dict) -> None:
    """Print formatted validation report."""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    
    status = "✓ PASSED" if results["passed"] else "✗ FAILED"
    print(f"\nStatus: {status}")
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  ✗ {err}")
    
    if results["warnings"]:
        print("\nWarnings:")
        for warn in results["warnings"]:
            print(f"  ⚠ {warn}")
    
    print("\nMetrics:")
    for key, value in results["metrics"].items():
        print(f"  {key}: {value}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Black Book CSV for Layer 0"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing CSV, don't re-process",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_CSV,
        help=f"Input CSV path (default: {INPUT_CSV})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_CSV,
        help=f"Output CSV path (default: {OUTPUT_CSV})",
    )
    args = parser.parse_args()
    
    print("Black Book Normalization Script")
    print(f"Run time: {datetime.now().isoformat()}")
    print()
    
    # Verify input exists
    if not args.input.exists():
        print(f"ERROR: Input CSV not found: {args.input}")
        sys.exit(1)
    
    # Compute input hash for provenance
    input_hash = compute_file_hash(args.input)
    print(f"Input: {args.input}")
    print(f"SHA-256: {input_hash}")
    print()
    
    if args.verify_only:
        # Verify existing output
        if not args.output.exists():
            print(f"ERROR: Output CSV not found: {args.output}")
            sys.exit(1)
        
        print("Verifying existing CSV...")
        with open(args.output, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Strip record_id for validation
        header = [c for c in reader.fieldnames if c != "record_id"]
        results = validate_data(header, rows)
        print_validation_report(results)
        
        output_hash = compute_file_hash(args.output)
        print(f"\nOutput SHA-256: {output_hash}")
        
        sys.exit(0 if results["passed"] else 1)
    
    # Load and dedupe
    header, rows = load_and_dedupe(args.input)
    
    # Validate
    results = validate_data(header, rows)
    print_validation_report(results)
    
    if not results["passed"]:
        print("\nData failed validation. Not writing output.")
        sys.exit(1)
    
    # Add record IDs
    rows = add_record_ids(rows)
    
    # Reorder columns for output
    rows = [{col: r.get(col, "") for col in OUTPUT_COLUMNS} for r in rows]
    
    # Write output
    write_csv(rows, args.output)
    
    # Final verification
    output_hash = compute_file_hash(args.output)
    print(f"\nOutput SHA-256: {output_hash}")
    print("\nNormalization complete.")


if __name__ == "__main__":
    main()
