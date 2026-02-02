#!/usr/bin/env python3
"""
Import L0 CSVs to PostgreSQL

Creates the epsteinfiles_ard database, schemas, and tables,
then imports flight-logs.csv and black-book.csv into core schema.

Usage:
    python import_l0_to_postgres.py [--create-db] [--skip-import]

Requirements:
    pip install psycopg[binary] python-dotenv
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Configuration
PGSQL_HOST = os.getenv("PGSQL_HOST", "10.25.20.8")
PGSQL_PORT = os.getenv("PGSQL_PORT", "5432")
PGSQL_USER = os.getenv("PGSQL_USER")
PGSQL_PASSWORD = os.getenv("PGSQL_PASSWORD")
PGSQL_DATABASE = os.getenv("PGSQL_DATABASE", "epsteinfiles_ard")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

# Data paths
DATA_DIR = PROJECT_ROOT / "data" / "layer-0-canonical"
FLIGHT_LOGS_CSV = DATA_DIR / "flight-logs.csv"
BLACK_BOOK_CSV = DATA_DIR / "black-book.csv"


def get_admin_connection():
    """Connect to postgres database (for admin operations)."""
    return psycopg.connect(
        host=PGSQL_HOST,
        port=PGSQL_PORT,
        user=PGSQL_USER,
        password=PGSQL_PASSWORD,
        dbname="postgres",
        autocommit=True
    )


def get_connection():
    """Connect to the project database."""
    return psycopg.connect(
        host=PGSQL_HOST,
        port=PGSQL_PORT,
        user=PGSQL_USER,
        password=PGSQL_PASSWORD,
        dbname=PGSQL_DATABASE
    )


def create_database():
    """Create the epsteinfiles_ard database if it doesn't exist."""
    print(f"Creating database: {PGSQL_DATABASE}")
    
    with get_admin_connection() as conn:
        # Check if database exists
        result = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (PGSQL_DATABASE,)
        ).fetchone()
        
        if result:
            print(f"  Database {PGSQL_DATABASE} already exists")
            return False
        
        # Create database
        conn.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(PGSQL_DATABASE))
        )
        print(f"  Created database {PGSQL_DATABASE}")
        return True


def setup_schemas_and_extensions():
    """Create schemas and enable required extensions."""
    print("Setting up schemas and extensions...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Extensions
            cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("  Enabled extensions: fuzzystrmatch, vector")
            
            # Schemas
            schemas = ["core", "l1", "l2", "l3", "ingest"]
            for schema in schemas:
                cur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(schema)
                    )
                )
            print(f"  Created schemas: {', '.join(schemas)}")
        
        conn.commit()


def create_tables():
    """Create L0 tables in core schema."""
    print("Creating L0 tables...")
    
    # Flight logs table DDL
    flight_logs_ddl = """
    CREATE TABLE IF NOT EXISTS core.flight_logs (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        year INTEGER NOT NULL,
        aircraft_model TEXT,
        aircraft_tail TEXT,
        aircraft_type TEXT,
        num_seats INTEGER,
        dep_code TEXT,
        arr_code TEXT,
        dep_location TEXT,
        arr_location TEXT,
        flight_no TEXT,
        pass_position TEXT,
        unique_id TEXT NOT NULL,  -- Not actually unique in source data
        first_name TEXT,
        last_name TEXT,
        last_first TEXT,
        first_last TEXT,
        comment TEXT,
        initials TEXT,
        known TEXT,
        data_source TEXT,
        
        -- Metadata
        imported_at TIMESTAMP DEFAULT NOW()
    )
    """
    
    # Black book table DDL
    black_book_ddl = """
    CREATE TABLE IF NOT EXISTS core.black_book (
        record_id UUID PRIMARY KEY,
        page INTEGER NOT NULL,
        page_link TEXT NOT NULL,
        name TEXT NOT NULL,
        company_text TEXT,
        surname TEXT,
        first_name TEXT,
        address_type TEXT,
        address TEXT,
        zip TEXT,
        city TEXT,
        country TEXT,
        phone_general TEXT,
        phone_work TEXT,
        phone_home TEXT,
        phone_mobile TEXT,
        email TEXT,
        
        -- Metadata
        imported_at TIMESTAMP DEFAULT NOW()
    )
    """
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(flight_logs_ddl)
            print("  Created core.flight_logs")
            
            cur.execute(black_book_ddl)
            print("  Created core.black_book")
        
        conn.commit()


def import_flight_logs():
    """Import flight-logs.csv to core.flight_logs."""
    print(f"Importing flight logs from {FLIGHT_LOGS_CSV}")
    
    if not FLIGHT_LOGS_CSV.exists():
        print(f"  ERROR: File not found: {FLIGHT_LOGS_CSV}")
        return 0
    
    # Column mapping: CSV header -> DB column
    column_map = {
        "ID": "id",
        "Date": "date",
        "Year": "year",
        "Aircraft Model": "aircraft_model",
        "Aircraft Tail #": "aircraft_tail",
        "Aircraft Type": "aircraft_type",
        "# of Seats": "num_seats",
        "DEP: Code": "dep_code",
        "ARR: Code": "arr_code",
        "DEP": "dep_location",
        "ARR": "arr_location",
        "Flight_No.": "flight_no",
        "Pass #": "pass_position",
        "Unique ID": "unique_id",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Last, First": "last_first",
        "First Last": "first_last",
        "Comment": "comment",
        "Initials": "initials",
        "Known": "known",
        "Data Source": "data_source"
    }
    
    db_columns = list(column_map.values())
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Clear existing data
            cur.execute("TRUNCATE core.flight_logs")
            
            # Read and insert
            with open(FLIGHT_LOGS_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                batch = []
                total = 0
                
                for row in reader:
                    values = []
                    for csv_col, db_col in column_map.items():
                        val = row.get(csv_col, "")
                        # Handle nulls and type conversions
                        if val == "":
                            val = None
                        elif db_col in ("id", "year", "num_seats"):
                            val = int(val) if val else None
                        values.append(val)
                    
                    batch.append(tuple(values))
                    
                    if len(batch) >= BATCH_SIZE:
                        _insert_batch(cur, "core.flight_logs", db_columns, batch)
                        total += len(batch)
                        batch = []
                
                # Insert remaining
                if batch:
                    _insert_batch(cur, "core.flight_logs", db_columns, batch)
                    total += len(batch)
            
            conn.commit()
            print(f"  Imported {total} flight log records")
            return total


def import_black_book():
    """Import black-book.csv to core.black_book."""
    print(f"Importing black book from {BLACK_BOOK_CSV}")
    
    if not BLACK_BOOK_CSV.exists():
        print(f"  ERROR: File not found: {BLACK_BOOK_CSV}")
        return 0
    
    # Column mapping: CSV header -> DB column
    column_map = {
        "record_id": "record_id",
        "Page": "page",
        "Page-Link": "page_link",
        "Name": "name",
        "Company/Add. Text": "company_text",
        "Surname": "surname",
        "First Name": "first_name",
        "Address-Type": "address_type",
        "Address": "address",
        "Zip": "zip",
        "City": "city",
        "Country": "country",
        "Phone (no specifics)": "phone_general",
        "Phone (w) – work": "phone_work",
        "Phone (h) – home": "phone_home",
        "Phone (p) – portable/mobile": "phone_mobile",
        "Email": "email"
    }
    
    db_columns = list(column_map.values())
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Clear existing data
            cur.execute("TRUNCATE core.black_book")
            
            # Read and insert
            with open(BLACK_BOOK_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                batch = []
                total = 0
                
                for row in reader:
                    values = []
                    for csv_col, db_col in column_map.items():
                        val = row.get(csv_col, "")
                        # Handle nulls and type conversions
                        if val == "":
                            val = None
                        elif db_col == "page":
                            val = int(val) if val else None
                        values.append(val)
                    
                    batch.append(tuple(values))
                    
                    if len(batch) >= BATCH_SIZE:
                        _insert_batch(cur, "core.black_book", db_columns, batch)
                        total += len(batch)
                        batch = []
                
                # Insert remaining
                if batch:
                    _insert_batch(cur, "core.black_book", db_columns, batch)
                    total += len(batch)
            
            conn.commit()
            print(f"  Imported {total} black book records")
            return total


def _insert_batch(cursor, table: str, columns: list, rows: list):
    """Insert a batch of rows using executemany."""
    placeholders = ", ".join(["%s"] * len(columns))
    col_names = ", ".join(columns)
    
    query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
    cursor.executemany(query, rows)  # type: ignore[arg-type]


def verify_counts():
    """Verify row counts match expected values."""
    print("Verifying import counts...")
    
    expected = {
        "core.flight_logs": 5001,
        "core.black_book": 2324
    }
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            all_pass = True
            for table, expected_count in expected.items():
                cur.execute(f"SELECT COUNT(*) FROM {table}")  # type: ignore[arg-type]
                row = cur.fetchone()
                actual = row[0] if row else 0
                status = "✓" if actual == expected_count else "✗"
                print(f"  {status} {table}: {actual} rows (expected {expected_count})")
                if actual != expected_count:
                    all_pass = False
            
            return all_pass


def main():
    parser = argparse.ArgumentParser(description="Import L0 CSVs to PostgreSQL")
    parser.add_argument("--create-db", action="store_true", 
                        help="Create database (requires admin access)")
    parser.add_argument("--skip-import", action="store_true",
                        help="Skip CSV import (setup only)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Epstein Files ARD - L0 Import")
    print("=" * 60)
    print(f"Host: {PGSQL_HOST}:{PGSQL_PORT}")
    print(f"Database: {PGSQL_DATABASE}")
    print()
    
    try:
        # Step 1: Create database (optional)
        if args.create_db:
            create_database()
        
        # Step 2: Setup schemas and extensions
        setup_schemas_and_extensions()
        
        # Step 3: Create tables
        create_tables()
        
        # Step 4: Import data
        if not args.skip_import:
            import_flight_logs()
            import_black_book()
            
            # Step 5: Verify
            if verify_counts():
                print("\n✓ Import completed successfully")
                return 0
            else:
                print("\n✗ Import completed with count mismatches")
                return 1
        else:
            print("\n✓ Setup completed (import skipped)")
            return 0
            
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
