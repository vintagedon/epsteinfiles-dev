#!/usr/bin/env python3
"""
Layer 0 Schema Validation

Validates L0 CSV files against JSON Schema definitions.
Reports field-level compliance and data quality metrics.

Usage:
    python validate_l0_schemas.py                    # Validate all
    python validate_l0_schemas.py --dataset flight  # Validate flight logs only
    python validate_l0_schemas.py --dataset book    # Validate black book only
    python validate_l0_schemas.py --sample 100      # Validate random sample

Dependencies:
    pip install jsonschema

Author: Epstein Files ARD Project
Date: 2026-02-01
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)


# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
SCHEMA_DIR = REPO_ROOT / "data" / "layer-0-canonical" / "schema"
DATA_DIR = REPO_ROOT / "data" / "layer-0-canonical"

# AI NOTE: DATASETS is the source of truth for dataset-to-schema mappings.
# Adding a new dataset requires: (1) entry here, (2) JSON schema file,
# (3) corresponding entry in quality_audit_l0.py if auditing is needed.
DATASETS = {
    "flight": {
        "schema": SCHEMA_DIR / "flight-logs.schema.json",
        "data": DATA_DIR / "flight-logs.csv",
        "name": "Flight Logs"
    },
    "book": {
        "schema": SCHEMA_DIR / "black-book.schema.json",
        "data": DATA_DIR / "black-book.csv",
        "name": "Black Book"
    }
}


def load_schema(schema_path: Path) -> dict:
    """Load and validate JSON Schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Validate the schema itself
    Draft7Validator.check_schema(schema)
    return schema


def coerce_types(row: dict, schema: dict) -> dict:
    """
    Coerce CSV string values to schema-expected types.
    
    AI NOTE: Python's csv.DictReader returns ALL values as strings. JSON Schema
    validation will fail if the schema expects integers (e.g., Year, ID) unless
    we coerce first. This function handles that translation. If you add new
    integer fields to schemas, they'll be handled automatically via type inspection.
    """
    properties = schema.get("properties", {})
    coerced = {}
    
    for key, value in row.items():
        prop_schema = properties.get(key, {})
        prop_type = prop_schema.get("type")
        
        # Handle null/empty values
        if value == "" or value is None:
            if prop_type == "integer":
                coerced[key] = None  # Will fail required check if needed
            elif isinstance(prop_type, list) and "null" in prop_type:
                coerced[key] = None
            else:
                coerced[key] = value
            continue
        
        # Type coercion
        if prop_type == "integer":
            try:
                coerced[key] = int(value)
            except ValueError:
                coerced[key] = value  # Keep as string, will fail validation
        elif isinstance(prop_type, list) and "integer" in prop_type:
            try:
                coerced[key] = int(value)
            except ValueError:
                coerced[key] = value
        else:
            coerced[key] = value
    
    return coerced


def validate_dataset(dataset_key: str, sample_size: Optional[int] = None) -> dict:
    """
    Validate a dataset against its schema.
    
    Returns dict with validation results and metrics.
    """
    config = DATASETS[dataset_key]
    
    print(f"\n{'='*60}")
    print(f"Validating: {config['name']}")
    print(f"Schema: {config['schema'].name}")
    print(f"Data: {config['data'].name}")
    print(f"{'='*60}")
    
    # Load schema
    schema = load_schema(config['schema'])
    validator = Draft7Validator(schema)
    
    # Track results
    results = {
        "dataset": config['name'],
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "errors_by_field": defaultdict(list),
        "errors_by_type": defaultdict(int),
        "sample_errors": []
    }
    
    # Read and validate CSV
    with open(config['data'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        rows = list(reader)
        results["total_rows"] = len(rows)
        
        # Sample if requested
        if sample_size and sample_size < len(rows):
            import random
            rows = random.sample(rows, sample_size)
            print(f"Validating random sample of {sample_size} rows")
        
        for i, row in enumerate(rows):
            # Coerce types from CSV strings
            coerced_row = coerce_types(row, schema)
            
            # Collect all errors for this row
            row_errors = list(validator.iter_errors(coerced_row))
            
            if row_errors:
                results["invalid_rows"] += 1
                
                for error in row_errors:
                    # Track by field
                    field = error.path[0] if error.path else "root"
                    results["errors_by_field"][field].append(str(error.message)[:100])
                    
                    # Track by error type
                    results["errors_by_type"][error.validator] += 1
                    
                    # Keep sample of full errors
                    if len(results["sample_errors"]) < 10:
                        results["sample_errors"].append({
                            "row": i + 2,  # +2 for header and 0-index
                            "field": field,
                            "message": str(error.message),
                            "value": error.instance
                        })
            else:
                results["valid_rows"] += 1
    
    return results


def print_results(results: dict):
    """Print validation results in human-readable format."""
    total = results["total_rows"]
    valid = results["valid_rows"]
    invalid = results["invalid_rows"]
    pct_valid = (valid / total * 100) if total > 0 else 0
    
    print("\n--- Results ---")
    print(f"Total rows:   {total:,}")
    print(f"Valid rows:   {valid:,} ({pct_valid:.1f}%)")
    print(f"Invalid rows: {invalid:,} ({100-pct_valid:.1f}%)")
    
    if results["errors_by_field"]:
        print("\n--- Errors by Field ---")
        for field, errors in sorted(results["errors_by_field"].items(), 
                                    key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  {field}: {len(errors)} errors")
    
    if results["errors_by_type"]:
        print("\n--- Errors by Type ---")
        for err_type, count in sorted(results["errors_by_type"].items(),
                                      key=lambda x: x[1], reverse=True):
            print(f"  {err_type}: {count}")
    
    if results["sample_errors"]:
        print("\n--- Sample Errors (first 5) ---")
        for err in results["sample_errors"][:5]:
            print(f"  Row {err['row']}, Field '{err['field']}':")
            print(f"    Value: {repr(err['value'])[:50]}")
            print(f"    Error: {err['message'][:80]}")


def main():
    parser = argparse.ArgumentParser(description="Validate L0 datasets against JSON schemas")
    parser.add_argument("--dataset", choices=["flight", "book", "all"], default="all",
                        help="Which dataset to validate")
    parser.add_argument("--sample", type=int, default=None,
                        help="Validate random sample of N rows (default: all)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()
    
    datasets_to_validate = list(DATASETS.keys()) if args.dataset == "all" else [args.dataset]
    
    all_results = {}
    all_valid = True
    
    for ds_key in datasets_to_validate:
        results = validate_dataset(ds_key, args.sample)
        all_results[ds_key] = results
        
        if not args.json:
            print_results(results)
        
        if results["invalid_rows"] > 0:
            all_valid = False
    
    if args.json:
        # Convert defaultdicts to regular dicts for JSON serialization
        for key in all_results:
            all_results[key]["errors_by_field"] = dict(all_results[key]["errors_by_field"])
            all_results[key]["errors_by_type"] = dict(all_results[key]["errors_by_type"])
        print(json.dumps(all_results, indent=2))
    
    # Summary
    if not args.json:
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        for ds_key, results in all_results.items():
            status = "✅ PASS" if results["invalid_rows"] == 0 else "⚠️  ISSUES"
            print(f"{DATASETS[ds_key]['name']}: {status} ({results['valid_rows']}/{results['total_rows']} valid)")
    
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
