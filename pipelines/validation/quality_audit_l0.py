#!/usr/bin/env python3
"""
Layer 0 Quality Audit

Comprehensive data quality analysis beyond schema validation.
Produces metrics JSON and console summary for report generation.

Usage:
    python quality_audit_l0.py                    # Full audit, console output
    python quality_audit_l0.py --json             # Output metrics as JSON
    python quality_audit_l0.py --output FILE      # Write JSON to file

Author: Epstein Files ARD Project
Date: 2026-02-01
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

from datetime import datetime

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "layer-0-canonical"

# AI NOTE: DATASETS must stay in sync with validate_l0_schemas.py.
# Adding a new dataset requires entries in both files.
DATASETS = {
    "flight": {
        "file": DATA_DIR / "flight-logs.csv",
        "name": "Flight Logs",
        "id_col": "ID"
    },
    "book": {
        "file": DATA_DIR / "black-book.csv", 
        "name": "Black Book",
        "id_col": "record_id"
    }
}


def load_csv(path: Path) -> list[dict]:
    """Load CSV as list of dicts."""
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def completeness_matrix(rows: list[dict]) -> dict:
    """Calculate % populated for each column."""
    if not rows:
        return {}
    
    columns = rows[0].keys()
    total = len(rows)
    
    matrix = {}
    for col in columns:
        populated = sum(1 for r in rows if r.get(col) and r[col].strip())
        matrix[col] = {
            "populated": populated,
            "missing": total - populated,
            "pct_populated": round(populated / total * 100, 1)
        }
    
    return matrix


def value_distribution(rows: list[dict], column: str, top_n: int = 10) -> dict:
    """Get value frequency distribution for a column."""
    values = [r.get(column, "") for r in rows]
    counter = Counter(values)
    
    return {
        "unique_count": len(counter),
        "top_values": counter.most_common(top_n),
        "empty_count": counter.get("", 0)
    }


def audit_flight_logs(rows: list[dict]) -> dict:
    """
    Flight logs specific quality checks.
    
    AI NOTE: The pattern regexes here (date_pattern, tail_pattern, pass_pattern)
    define what counts as "valid" for reporting purposes. These are intentionally
    stricter than the JSON schema to surface quality issues. Changing these
    patterns affects the audit report but not schema validation.
    """
    metrics = {
        "total_records": len(rows),
        "completeness": completeness_matrix(rows),
        "distributions": {},
        "anomalies": {},
        "patterns": {}
    }
    
    # Key distributions
    metrics["distributions"]["Year"] = value_distribution(rows, "Year")
    metrics["distributions"]["Aircraft Type"] = value_distribution(rows, "Aircraft Type")
    metrics["distributions"]["Known"] = value_distribution(rows, "Known")
    metrics["distributions"]["Data Source"] = value_distribution(rows, "Data Source")
    
    # Date format check
    date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
    date_issues = []
    for i, r in enumerate(rows):
        date_val = r.get("Date", "")
        if date_val and not date_pattern.match(date_val):
            date_issues.append({"row": i+2, "value": date_val})
    metrics["patterns"]["date_format_issues"] = {
        "count": len(date_issues),
        "samples": date_issues[:5]
    }
    
    # Tail number check (should be N-number)
    tail_pattern = re.compile(r'^N[0-9A-Z]+$')
    tail_issues = []
    tail_values = Counter()
    for i, r in enumerate(rows):
        tail = r.get("Aircraft Tail #", "")
        tail_values[tail] += 1
        if tail and not tail_pattern.match(tail):
            tail_issues.append({"row": i+2, "value": tail})
    metrics["patterns"]["tail_number_issues"] = {
        "count": len(tail_issues),
        "samples": tail_issues[:10],
        "unique_tails": len(tail_values)
    }
    metrics["distributions"]["Aircraft Tail #"] = {
        "unique_count": len(tail_values),
        "top_values": tail_values.most_common(10)
    }
    
    # Airport code distribution
    dep_codes = Counter(r.get("DEP: Code", "") for r in rows)
    arr_codes = Counter(r.get("ARR: Code", "") for r in rows)
    metrics["distributions"]["DEP: Code"] = {
        "unique_count": len(dep_codes),
        "top_values": dep_codes.most_common(15)
    }
    metrics["distributions"]["ARR: Code"] = {
        "unique_count": len(arr_codes),
        "top_values": arr_codes.most_common(15)
    }
    
    # Name anomalies
    unknown_patterns = ["Unknown", "Female", "Male", "Unidentified", "?"]
    name_anomalies = defaultdict(int)
    initials_only = 0
    
    for r in rows:
        first = r.get("First Name", "")
        last = r.get("Last Name", "")
        full = f"{first} {last}".strip()
        
        # Check for unknown markers
        for pattern in unknown_patterns:
            if pattern.lower() in full.lower():
                name_anomalies[pattern] += 1
                break
        
        # Check for initials only (single char first AND single char/empty last)
        if len(first) <= 2 and len(last) <= 2 and first and (last or first):
            initials_only += 1
    
    metrics["anomalies"]["name_anomalies"] = dict(name_anomalies)
    metrics["anomalies"]["initials_only_count"] = initials_only
    metrics["anomalies"]["known_no_count"] = sum(1 for r in rows if r.get("Known") == "No")
    metrics["anomalies"]["known_yes_count"] = sum(1 for r in rows if r.get("Known") == "Yes")
    
    # Unique ID duplicates
    unique_ids = Counter(r.get("Unique ID", "") for r in rows)
    duplicates = {k: v for k, v in unique_ids.items() if v > 1}
    metrics["anomalies"]["duplicate_unique_ids"] = {
        "count": len(duplicates),
        "total_duplicate_rows": sum(duplicates.values()) - len(duplicates),
        "samples": list(duplicates.items())[:5]
    }
    
    # Pass # patterns
    pass_pattern = re.compile(r'^Pass \d+$')
    pass_issues = Counter()
    for r in rows:
        pass_val = r.get("Pass #", "")
        if pass_val and not pass_pattern.match(pass_val):
            pass_issues[pass_val] += 1
    metrics["patterns"]["pass_number_issues"] = {
        "count": sum(pass_issues.values()),
        "values": dict(pass_issues)
    }
    
    # Year range
    years = [int(r.get("Year", 0)) for r in rows if r.get("Year", "").isdigit()]
    if years:
        metrics["patterns"]["year_range"] = {
            "min": min(years),
            "max": max(years),
            "distribution": dict(Counter(years))
        }
    
    return metrics


def audit_black_book(rows: list[dict]) -> dict:
    """
    Black book specific quality checks.
    
    AI NOTE: Phone format detection is heuristic, not exhaustive. The categories
    (international_plus, us_parens, etc.) are for reporting only—they inform
    L1 normalization strategy but don't affect L0 data.
    """
    metrics = {
        "total_records": len(rows),
        "completeness": completeness_matrix(rows),
        "distributions": {},
        "anomalies": {},
        "patterns": {}
    }
    
    # Key distributions
    metrics["distributions"]["Country"] = value_distribution(rows, "Country", top_n=20)
    metrics["distributions"]["Page"] = value_distribution(rows, "Page", top_n=20)
    
    # Wayback URL format check
    wayback_pattern = re.compile(r'^https?://web\.archive\.org/')
    url_issues = []
    for i, r in enumerate(rows):
        url = r.get("Page-Link", "")
        if url and not wayback_pattern.match(url):
            url_issues.append({"row": i+2, "value": url[:100]})
    metrics["patterns"]["wayback_url_issues"] = {
        "count": len(url_issues),
        "samples": url_issues[:5]
    }
    
    # Phone format analysis
    phone_cols = ["Phone (no specifics)", "Phone (w) – work", "Phone (h) – home", "Phone (p) – portable/mobile"]
    phone_formats = defaultdict(int)
    multi_phone_count = 0
    
    for r in rows:
        for col in phone_cols:
            phone = r.get(col, "")
            if not phone:
                continue
            
            # Check for multiple numbers (pipe separated)
            if "|" in phone:
                multi_phone_count += 1
            
            # Categorize format
            if phone.startswith("+"):
                phone_formats["international_plus"] += 1
            elif re.match(r'^\(\d{3}\)', phone):
                phone_formats["us_parens"] += 1
            elif re.match(r'^\d{3}-\d{3}-\d{4}', phone):
                phone_formats["us_dashes"] += 1
            elif re.match(r'^\d{10,}$', phone):
                phone_formats["digits_only"] += 1
            elif re.match(r'^0\d', phone):
                phone_formats["intl_zero_prefix"] += 1
            else:
                phone_formats["other"] += 1
    
    metrics["patterns"]["phone_formats"] = dict(phone_formats)
    metrics["patterns"]["multi_phone_entries"] = multi_phone_count
    
    # Email analysis
    emails = [r.get("Email", "") for r in rows if r.get("Email")]
    email_domains = Counter()
    truncated_emails = 0
    
    for email in emails:
        if "@" in email:
            domain = email.split("@")[-1].lower()
            email_domains[domain] += 1
        else:
            truncated_emails += 1
    
    metrics["patterns"]["email_analysis"] = {
        "total_with_email": len(emails),
        "truncated_no_at": truncated_emails,
        "top_domains": email_domains.most_common(10)
    }
    
    # Multi-person name detection
    multi_person_markers = [" & ", " and ", ", and ", " AND "]
    multi_person_count = 0
    multi_person_samples = []
    
    for i, r in enumerate(rows):
        name = r.get("Name", "")
        for marker in multi_person_markers:
            if marker in name:
                multi_person_count += 1
                if len(multi_person_samples) < 10:
                    multi_person_samples.append({"row": i+2, "name": name})
                break
    
    metrics["anomalies"]["multi_person_entries"] = {
        "count": multi_person_count,
        "samples": multi_person_samples
    }
    
    # Organization vs individual detection (heuristic: has company, no first name)
    org_entries = 0
    for r in rows:
        company = r.get("Company/Add. Text", "")
        first = r.get("First Name", "")
        surname = r.get("Surname", "")
        
        # Likely org: has company text but no parsed individual name
        if company and not first and not surname:
            org_entries += 1
    
    metrics["anomalies"]["likely_organizations"] = org_entries
    
    # Country normalization needs
    countries = Counter(r.get("Country", "") for r in rows if r.get("Country"))
    metrics["patterns"]["country_variations"] = {
        "unique_count": len(countries),
        "all_values": dict(countries)
    }
    
    # Duplicate record_id check
    record_ids = Counter(r.get("record_id", "") for r in rows)
    duplicates = {k: v for k, v in record_ids.items() if v > 1}
    metrics["anomalies"]["duplicate_record_ids"] = {
        "count": len(duplicates),
        "samples": list(duplicates.items())[:5]
    }
    
    return metrics


def print_summary(flight_metrics: dict, book_metrics: dict):
    """Print human-readable summary."""
    print("\n" + "="*70)
    print("L0 QUALITY AUDIT SUMMARY")
    print("="*70)
    
    # Flight Logs
    print("\n--- FLIGHT LOGS ---")
    print(f"Total records: {flight_metrics['total_records']:,}")
    
    print("\nCompleteness (bottom 5):")
    comp = sorted(flight_metrics['completeness'].items(), key=lambda x: x[1]['pct_populated'])
    for col, stats in comp[:5]:
        print(f"  {col}: {stats['pct_populated']}% ({stats['missing']:,} missing)")
    
    print("\nName Anomalies:")
    for anomaly, count in flight_metrics['anomalies'].get('name_anomalies', {}).items():
        print(f"  '{anomaly}' pattern: {count:,}")
    print(f"  Initials only: {flight_metrics['anomalies'].get('initials_only_count', 0):,}")
    print(f"  Known=No: {flight_metrics['anomalies'].get('known_no_count', 0):,}")
    
    print("\nPattern Issues:")
    print(f"  Date format issues: {flight_metrics['patterns']['date_format_issues']['count']}")
    print(f"  Tail number issues: {flight_metrics['patterns']['tail_number_issues']['count']}")
    print(f"  Pass # issues: {flight_metrics['patterns']['pass_number_issues']['count']}")
    
    if flight_metrics['patterns'].get('year_range'):
        yr = flight_metrics['patterns']['year_range']
        print(f"  Year range: {yr['min']} - {yr['max']}")
    
    dup = flight_metrics['anomalies']['duplicate_unique_ids']
    print(f"  Duplicate Unique IDs: {dup['count']} ({dup['total_duplicate_rows']} extra rows)")
    
    # Black Book
    print("\n--- BLACK BOOK ---")
    print(f"Total records: {book_metrics['total_records']:,}")
    
    print("\nCompleteness (bottom 5):")
    comp = sorted(book_metrics['completeness'].items(), key=lambda x: x[1]['pct_populated'])
    for col, stats in comp[:5]:
        print(f"  {col}: {stats['pct_populated']}% ({stats['missing']:,} missing)")
    
    print("\nPhone Format Distribution:")
    for fmt, count in sorted(book_metrics['patterns']['phone_formats'].items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {count:,}")
    print(f"  Multi-number entries: {book_metrics['patterns']['multi_phone_entries']}")
    
    print("\nEmail Analysis:")
    email = book_metrics['patterns']['email_analysis']
    print(f"  Records with email: {email['total_with_email']:,}")
    print(f"  Truncated (no @): {email['truncated_no_at']}")
    
    print("\nEntry Type Anomalies:")
    print(f"  Multi-person entries: {book_metrics['anomalies']['multi_person_entries']['count']}")
    print(f"  Likely organizations: {book_metrics['anomalies']['likely_organizations']}")
    
    print("\nCountry Variations:")
    countries = book_metrics['patterns']['country_variations']
    print(f"  Unique values: {countries['unique_count']}")
    
    dup = book_metrics['anomalies']['duplicate_record_ids']
    print(f"  Duplicate record_ids: {dup['count']}")
    
    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description="L0 Data Quality Audit")
    parser.add_argument("--json", action="store_true", help="Output as JSON only")
    parser.add_argument("--output", type=str, help="Write JSON to file")
    args = parser.parse_args()
    
    # Load data
    flight_rows = load_csv(DATASETS["flight"]["file"])
    book_rows = load_csv(DATASETS["book"]["file"])
    
    # Run audits
    flight_metrics = audit_flight_logs(flight_rows)
    book_metrics = audit_black_book(book_rows)
    
    results = {
        "audit_date": datetime.now().isoformat(),
        "flight_logs": flight_metrics,
        "black_book": book_metrics
    }
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    elif args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Metrics written to {args.output}")
        print_summary(flight_metrics, book_metrics)
    else:
        print_summary(flight_metrics, book_metrics)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
