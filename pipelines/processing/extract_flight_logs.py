#!/usr/bin/env python3
"""
Extract Flight Logs from PDF to CSV (Layer 0)

This script extracts structured flight log data from the Internet Archive's
"EPSTEIN FLIGHT LOGS UNREDACTED" PDF into a clean CSV format suitable for
Layer 0 processing.

Source: https://archive.org/details/epstein-flight-logs-unredacted_202304
Origin: Bradley Edwards court exhibits (Epstein v. Edwards, Case No. 50 2009 CA 040800)

Usage:
    python pipelines/processing/extract_flight_logs.py
    python pipelines/processing/extract_flight_logs.py --verify-only

Output:
    data/layer-0-canonical/flight-logs.csv

Dependencies:
    pip install pdfplumber

Author: Epstein Files ARD Project
Date: 2026-02-01
"""

import argparse
import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PDF = REPO_ROOT / "data" / "raw" / "epstein-flight-logs-unredacted.pdf"
OUTPUT_CSV = REPO_ROOT / "data" / "layer-0-canonical" / "flight-logs.csv"

# Expected schema (22 columns)
# AI NOTE: This list defines the contract with downstream consumers. Changes here
# require updates to: flight-logs.schema.json, validate_l0_schemas.py, and any
# L1 transformation pipelines that depend on column positions.
EXPECTED_COLUMNS = [
    "ID",
    "Date",
    "Year",
    "Aircraft Model",
    "Aircraft Tail #",
    "Aircraft Type",
    "# of Seats",
    "DEP: Code",
    "ARR: Code",
    "DEP",
    "ARR",
    "Flight_No.",
    "Pass #",
    "Unique ID",
    "First Name",
    "Last Name",
    "Last, First",
    "First Last",
    "Comment",
    "Initials",
    "Known",
    "Data Source",
]


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_tables_from_pdf(pdf_path: Path) -> tuple[list[str], list[list[str]]]:
    """
    Extract tabular data from PDF using pdfplumber.
    
    Returns:
        tuple: (header_row, data_rows)
    """
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(1)
    
    all_rows = []
    header = None
    
    print(f"Opening PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages...")
        
        for i, page in enumerate(pdf.pages):
            if (i + 1) % 20 == 0:
                print(f"  Page {i + 1}/{total_pages}")
            
            tables = page.extract_tables()
            if not tables:
                continue
                
            for table in tables:
                for j, row in enumerate(table):
                    if not row or not any(row):
                        continue
                    
                    # Clean cell values
                    cleaned = [
                        (c.replace("\n", " ").strip() if c else "")
                        for c in row
                    ]
                    
                    # First row of first page is header
                    if header is None and i == 0 and j == 0:
                        header = cleaned
                        # AI NOTE: The PDF renderer sometimes doubles the "ID" column
                        # header as "IIDD". This is a known artifact of pdfplumber's
                        # text extraction on this specific document. Do not remove
                        # this fix without re-testing extraction.
                        if header[0] == "IIDD":
                            header[0] = "ID"
                    else:
                        # AI NOTE: The PDF contains repeated header rows on each page.
                        # We detect and skip these by checking if the first column
                        # contains the header text. This assumes "ID"/"IIDD" never
                        # appears as a valid data value in column 0.
                        if cleaned[0] not in ("ID", "IIDD"):
                            all_rows.append(cleaned)
    
    print(f"Extracted {len(all_rows)} data rows")
    
    # Guard against empty PDF (no header found)
    if header is None:
        print("ERROR: No header row found in PDF")
        sys.exit(1)
    
    return header, all_rows


def validate_extraction(header: list[str], rows: list[list[str]]) -> dict:
    """
    Validate extracted data against expected schema.
    
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
    if len(header) != len(EXPECTED_COLUMNS):
        results["errors"].append(
            f"Column count mismatch: got {len(header)}, expected {len(EXPECTED_COLUMNS)}"
        )
        results["passed"] = False
    
    for i, (got, expected) in enumerate(zip(header, EXPECTED_COLUMNS)):
        if got != expected:
            results["errors"].append(
                f"Column {i} mismatch: got '{got}', expected '{expected}'"
            )
            results["passed"] = False
    
    # Check row consistency
    bad_rows = sum(1 for r in rows if len(r) != len(header))
    if bad_rows > 0:
        results["errors"].append(f"{bad_rows} rows have inconsistent column count")
        results["passed"] = False
    
    # Compute metrics
    results["metrics"]["total_rows"] = len(rows)
    results["metrics"]["unique_flights"] = len(set(r[11] for r in rows if r[11]))  # Flight_No.
    results["metrics"]["unique_dates"] = len(set(r[1] for r in rows if r[1]))  # Date
    results["metrics"]["unique_passengers"] = len(set(r[17] for r in rows if r[17]))  # First Last
    results["metrics"]["known_passengers"] = sum(1 for r in rows if r[20] == "Yes")  # Known
    results["metrics"]["unknown_passengers"] = sum(1 for r in rows if r[20] == "No")
    
    # Date range
    dates = [r[1] for r in rows if r[1] and "/" in r[1]]
    if dates:
        date_objects = [datetime.strptime(d, "%m/%d/%Y") for d in dates]
        results["metrics"]["date_range"] = f"{min(date_objects).strftime('%m/%d/%Y')} to {max(date_objects).strftime('%m/%d/%Y')}"
    
    # Sanity checks
    if results["metrics"]["total_rows"] < 4000:
        results["warnings"].append(
            f"Row count ({results['metrics']['total_rows']}) lower than expected (~5000)"
        )
    
    known_pct = (
        results["metrics"]["known_passengers"] / results["metrics"]["total_rows"] * 100
        if results["metrics"]["total_rows"] > 0
        else 0
    )
    if known_pct < 75:
        results["warnings"].append(
            f"Known passenger percentage ({known_pct:.1f}%) lower than expected (~82%)"
        )
    
    return results


def write_csv(header: list[str], rows: list[list[str]], output_path: Path) -> None:
    """Write extracted data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
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
        description="Extract flight logs from PDF to CSV"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing CSV, don't re-extract",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_PDF,
        help=f"Input PDF path (default: {INPUT_PDF})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_CSV,
        help=f"Output CSV path (default: {OUTPUT_CSV})",
    )
    args = parser.parse_args()
    
    print("Flight Logs Extraction Script")
    print(f"Run time: {datetime.now().isoformat()}")
    print()
    
    # Verify input exists
    if not args.input.exists():
        print(f"ERROR: Input PDF not found: {args.input}")
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
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        
        results = validate_extraction(header, rows)
        print_validation_report(results)
        
        output_hash = compute_file_hash(args.output)
        print(f"\nOutput SHA-256: {output_hash}")
        
        sys.exit(0 if results["passed"] else 1)
    
    # Extract from PDF
    header, rows = extract_tables_from_pdf(args.input)
    
    # Validate extraction
    results = validate_extraction(header, rows)
    print_validation_report(results)
    
    if not results["passed"]:
        print("\nExtraction failed validation. Not writing output.")
        sys.exit(1)
    
    # Write output
    write_csv(header, rows, args.output)
    
    # Final verification
    output_hash = compute_file_hash(args.output)
    print(f"\nOutput SHA-256: {output_hash}")
    print("\nExtraction complete.")


if __name__ == "__main__":
    main()
