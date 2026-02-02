-- ============================================================================
-- Epstein Files ARD - Database DDL
-- ============================================================================
-- 
-- This script creates the full database schema for the Epstein Files ARD.
-- Run against a fresh PostgreSQL 16+ instance with pgvector extension available.
--
-- Usage:
--   createdb epsteinfiles_ard
--   psql -d epsteinfiles_ard -f create_epsteinfiles_db.sql
--
-- Generated: 2026-02-01
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Extensions
-- ----------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- For soundex()
CREATE EXTENSION IF NOT EXISTS vector;         -- For pgvector embeddings

-- ----------------------------------------------------------------------------
-- Schemas
-- ----------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS core;      -- L0 source of truth
CREATE SCHEMA IF NOT EXISTS l1;        -- Layer 1: Scalars
CREATE SCHEMA IF NOT EXISTS l2;        -- Layer 2: Vectors (future)
CREATE SCHEMA IF NOT EXISTS l3;        -- Layer 3: Graphs (future)
CREATE SCHEMA IF NOT EXISTS ingest;    -- Staging area

-- ============================================================================
-- CORE SCHEMA (L0)
-- ============================================================================

-- Flight logs from Internet Archive + FOIA releases
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
    unique_id TEXT NOT NULL,  -- Not actually unique in source data (4 collisions)
    first_name TEXT,
    last_name TEXT,
    last_first TEXT,
    first_last TEXT,
    comment TEXT,
    initials TEXT,
    known TEXT,
    data_source TEXT,
    imported_at TIMESTAMP DEFAULT NOW()
);

-- Black book contacts from epsteinsblackbook.com
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
    imported_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- L1 SCHEMA (Layer 1: Scalars)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Flight Events (deduplicated flights)
-- ----------------------------------------------------------------------------

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

-- ----------------------------------------------------------------------------
-- Flight Passengers (one per L0 record)
-- ----------------------------------------------------------------------------

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
    
    -- Identity confidence (FL-1)
    identity_confidence DECIMAL(2,1),
    known TEXT,  -- Original Yes/No
    
    -- Victim protection (FL-2)
    potential_victim BOOLEAN DEFAULT FALSE,
    suppress_from_public BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flight_passengers_flight ON l1.flight_passengers(flight_id);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_l0 ON l1.flight_passengers(l0_id);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_name ON l1.flight_passengers(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_confidence ON l1.flight_passengers(identity_confidence);

-- Public view with victim protection
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

-- ----------------------------------------------------------------------------
-- Contacts (one per L0 black book record)
-- ----------------------------------------------------------------------------

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
    
    -- Normalized location (BB-3)
    address TEXT,
    city TEXT,
    zip TEXT,
    country_raw TEXT,
    country_iso CHAR(2),
    
    -- Entity classification (BB-4)
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

-- ----------------------------------------------------------------------------
-- Contact Persons (decomposed from multi-person entries, BB-1)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1.contact_persons (
    person_id UUID PRIMARY KEY,
    
    -- Links
    contact_id UUID REFERENCES l1.contacts(contact_id),
    l0_record_id UUID NOT NULL,
    household_id UUID,  -- Links people from same L0 record
    
    -- Decomposed name
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

-- ----------------------------------------------------------------------------
-- Phone Numbers (normalized to E.164, BB-2)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS l1.phone_numbers (
    phone_id UUID PRIMARY KEY,
    
    -- Links
    contact_id UUID REFERENCES l1.contacts(contact_id),
    l0_record_id UUID NOT NULL,
    
    -- Phone data
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

-- ----------------------------------------------------------------------------
-- Identity Mentions (unified for entity resolution)
-- ----------------------------------------------------------------------------

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
    parse_type VARCHAR(20) CHECK (parse_type IN ('Person', 'Corporation', 'Household', 'Unknown')),
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
--     ON l1.identity_mentions USING ivfflat (name_embedding vector_cosine_ops)
--     WITH (lists = 100);

-- ============================================================================
-- L2 SCHEMA (Layer 2: Vectors) - Placeholder for M06
-- ============================================================================

-- Tables will be added in M06:
-- - l2.document_embeddings
-- - l2.name_embeddings (or populated in l1.identity_mentions)

-- ============================================================================
-- L3 SCHEMA (Layer 3: Graphs) - Placeholder for M07
-- ============================================================================

-- Tables/views will be added in M07:
-- - l3.resolved_entities
-- - l3.entity_mention_map
-- - l3.network_edges (materialized view)
-- - l3.mv_flight_cooccurrence (materialized view)

-- ============================================================================
-- END OF DDL
-- ============================================================================
