-- ============================================================================
-- DocuMind S6 Demo Setup Script
-- ============================================================================
-- This script sets up the database to the correct state for Session 6 (RAG).
-- It includes all tables created in S3-S5 and populates with demo data.
--
-- Run this in your Supabase SQL Editor to prepare for S6.
-- ============================================================================

-- ============================================================================
-- STEP 1: Enable Required Extensions
-- ============================================================================

-- Enable vector extension for embeddings (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- STEP 2: Create Core Tables (S4: MCP and A2A Communication)
-- ============================================================================

-- Drop existing tables if they exist (for clean reset)
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS query_feedback CASCADE;
DROP TABLE IF EXISTS evaluation_runs CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Core document storage table (created in S4)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT,
    file_type VARCHAR(50),
    source_url TEXT,
    uploaded_by TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast sorting by creation date
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);

-- ============================================================================
-- STEP 3: Create Document Chunks Table (S5: Multi-Agent Systems)
-- ============================================================================

-- Document chunks for RAG (created in S5)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding vector(1536),
    word_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector index for semantic search using HNSW algorithm
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

-- Index for fast lookup by document
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);

-- ============================================================================
-- STEP 4: Create Conversation Memory Tables (For S6 RAG)
-- ============================================================================

-- Conversation tracking
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    context JSONB DEFAULT '{}'::jsonb
);

-- Message history within conversations
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast message lookup
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- ============================================================================
-- STEP 5: Create Feedback and Evaluation Tables (For S6+ RAG Improvements)
-- ============================================================================

-- Query feedback for learning
CREATE TABLE query_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    retrieved_chunks JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evaluation metrics tracking
CREATE TABLE evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name TEXT NOT NULL,
    framework VARCHAR(50),
    metrics JSONB NOT NULL,
    test_queries JSONB,
    results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- STEP 6: Insert Demo Documents
-- ============================================================================

-- Document 1: HR Policies and Procedures
INSERT INTO documents (id, title, content, file_path, file_type, metadata)
VALUES (
    'a1111111-1111-1111-1111-111111111111'::uuid,
    'HR Policies and Procedures',
    '# HR Policies and Procedures

## Time Off Benefits

Our company offers comprehensive time-off benefits including vacation, sick leave, and personal days. We believe that well-rested employees are more productive and engaged.

### Requesting Time Off

All time off requests must be submitted through the HR portal. Here are the guidelines:

**Vacation Requests:**
- Submit at least 2 weeks in advance
- Manager approval required
- Check team calendar for conflicts
- Longer vacations (5+ days) require 4 weeks notice

**Sick Leave:**
- Notify your manager as early as possible
- No advance approval needed
- Doctor''s note required for absences over 3 consecutive days

**Personal Days:**
- 3 personal days per year
- Can be used for any reason
- 48-hour advance notice preferred

### Holiday Schedule

HeroForge observes the following paid holidays:
- New Year''s Day
- Martin Luther King Jr. Day
- Presidents Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving (2 days)
- Winter Break (Dec 24-Jan 1)

### Leave of Absence

For extended leave (medical, family, sabbatical), contact HR directly to discuss options and eligibility requirements.

## Expense Reimbursement

Business expenses must be submitted within 30 days of incurrence. Use the expense portal and attach all receipts. Pre-approval is required for expenses over $500.',
    'demo-docs/hr_policies.txt',
    'txt',
    '{"category": "HR", "version": "1.0", "last_reviewed": "2025-01-15"}'::jsonb
);

-- Document 2: Employee Handbook
INSERT INTO documents (id, title, content, file_path, file_type, metadata)
VALUES (
    'b2222222-2222-2222-2222-222222222222'::uuid,
    'Employee Handbook - HeroForge Inc.',
    '# Employee Handbook - HeroForge Inc.

## Section 5: Time Off and Leave Policies

### 5.1 Vacation Policy

All full-time employees receive 15 days of paid vacation per year. Vacation accrues at a rate of 1.25 days per month and begins accruing from your first day of employment.

**Vacation Accrual by Tenure:**
- Years 0-2: 15 days per year (1.25 days/month)
- Years 3-5: 20 days per year (1.67 days/month)
- Years 6+: 25 days per year (2.08 days/month)

**Requesting Vacation:**
Submit vacation requests through the HR portal at least two weeks in advance. Requests are approved based on business needs and team coverage. During peak periods (Q4, product launches), vacation requests may be limited.

**Carryover Policy:**
Unused vacation days can be carried over to the next calendar year, up to a maximum of 5 days. Any days beyond this limit will be forfeited on January 1st. We encourage employees to use their vacation time for work-life balance.

### 5.2 Sick Leave

Employees receive 10 days of paid sick leave annually. Sick leave can be used for:
- Personal illness or injury
- Medical appointments
- Caring for immediate family members

### 5.3 Remote Work

HeroForge supports flexible work arrangements. Employees may work remotely up to 3 days per week with manager approval. Core collaboration hours are 10 AM - 3 PM local time.

## Section 6: Benefits Overview

See the Benefits Guide for complete details on health insurance, 401(k), and other benefits.',
    'demo-docs/employee_handbook.txt',
    'txt',
    '{"category": "HR", "version": "2.3", "effective_date": "2025-01-01"}'::jsonb
);

-- Document 3: Benefits Guide
INSERT INTO documents (id, title, content, file_path, file_type, metadata)
VALUES (
    'c3333333-3333-3333-3333-333333333333'::uuid,
    'Benefits Guide - HeroForge Inc.',
    '# Benefits Guide - HeroForge Inc.

## Annual Leave and Paid Time Off

Employees are entitled to paid annual leave which increases with tenure at the company. Our generous PTO policy reflects our commitment to employee wellbeing.

### PTO Allocation

| Years of Service | Annual PTO Days | Monthly Accrual |
|-----------------|-----------------|-----------------|
| 0-2 years       | 15 days         | 1.25 days       |
| 3-5 years       | 20 days         | 1.67 days       |
| 6+ years        | 25 days         | 2.08 days       |

### Carryover Rules

Unused vacation can be carried over to the next year, up to 5 days maximum. Plan your time off wisely to maximize this benefit. Days beyond the carryover limit expire on December 31st.

### Blackout Periods

During critical business periods, vacation requests may be restricted:
- Last two weeks of each quarter
- Product launch windows
- Annual planning (typically January)

## Health Insurance

HeroForge provides comprehensive health coverage:

**Medical Plans:**
- PPO Plan: Higher premiums, more flexibility
- HMO Plan: Lower premiums, network restrictions
- HDHP with HSA: Tax-advantaged savings option

**Dental and Vision:**
- Dental coverage included at no extra cost
- Vision plan with annual exam and frame allowance

## Retirement Benefits

**401(k) Plan:**
- Company matches 50% of contributions up to 6% of salary
- Immediate vesting
- Wide selection of investment options

## Professional Development

- $2,000 annual learning stipend
- Conference attendance supported
- Internal mentorship program',
    'demo-docs/benefits_guide.txt',
    'txt',
    '{"category": "HR", "version": "2025", "department": "Human Resources"}'::jsonb
);

-- Document 4: Remote Work Policy (from S4 workshop)
INSERT INTO documents (id, title, content, file_path, file_type, metadata)
VALUES (
    'd4444444-4444-4444-4444-444444444444'::uuid,
    'Remote Work Policy',
    'Employees may work remotely up to 3 days per week. Remote work requests must be approved by direct manager. Equipment: Company provides laptop and monitor for home office setup. Communication: All remote workers must be available during core hours 10am-3pm. Security: Use VPN for all company system access.',
    NULL,
    'txt',
    '{"category": "Policy", "uploaded_by": "doc-uploader agent", "word_count": 67}'::jsonb
);

-- Document 5: Company Handbook (from S4 workshop)
INSERT INTO documents (id, title, content, file_path, file_type, metadata)
VALUES (
    'e5555555-5555-5555-5555-555555555555'::uuid,
    'Company Handbook',
    'Welcome to our company! This handbook contains all policies and procedures. Section 1: Code of Conduct. Section 2: Benefits. Section 3: Time Off.',
    NULL,
    'txt',
    '{"category": "Handbook", "uploaded_by": "documind MCP"}'::jsonb
);

-- ============================================================================
-- STEP 7: Insert Document Chunks (as processed by S5 pipeline)
-- ============================================================================
-- Note: Embeddings are NULL here. In production, these would be generated by
-- running the pipeline: python src/agents/pipeline/orchestrate.py demo-docs/
-- After running the pipeline, embeddings will be populated with 1536-dim vectors.

-- Chunks for HR Policies document
INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'a1111111-1111-1111-1111-111111111111'::uuid,
    'HR Policies and Procedures - Time Off Benefits

Our company offers comprehensive time-off benefits including vacation, sick leave, and personal days. We believe that well-rested employees are more productive and engaged.

Requesting Time Off: All time off requests must be submitted through the HR portal. Vacation Requests: Submit at least 2 weeks in advance. Manager approval required. Check team calendar for conflicts. Longer vacations (5+ days) require 4 weeks notice.',
    0,
    78,
    '{"source": "hr_policies.txt", "section": "Time Off Benefits", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'a1111111-1111-1111-1111-111111111111'::uuid,
    'Sick Leave: Notify your manager as early as possible. No advance approval needed. Doctor''s note required for absences over 3 consecutive days.

Personal Days: 3 personal days per year. Can be used for any reason. 48-hour advance notice preferred.

Holiday Schedule: HeroForge observes the following paid holidays: New Year''s Day, Martin Luther King Jr. Day, Presidents Day, Memorial Day, Independence Day, Labor Day, Thanksgiving (2 days), Winter Break (Dec 24-Jan 1).',
    1,
    79,
    '{"source": "hr_policies.txt", "section": "Sick Leave and Holidays", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'a1111111-1111-1111-1111-111111111111'::uuid,
    'Leave of Absence: For extended leave (medical, family, sabbatical), contact HR directly to discuss options and eligibility requirements.

Expense Reimbursement: Business expenses must be submitted within 30 days of incurrence. Use the expense portal and attach all receipts. Pre-approval is required for expenses over $500.',
    2,
    52,
    '{"source": "hr_policies.txt", "section": "Leave and Expenses", "chunk_strategy": "semantic"}'::jsonb
);

-- Chunks for Employee Handbook
INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'b2222222-2222-2222-2222-222222222222'::uuid,
    'Employee Handbook - HeroForge Inc. Section 5: Time Off and Leave Policies

Vacation Policy: All full-time employees receive 15 days of paid vacation per year. Vacation accrues at a rate of 1.25 days per month and begins accruing from your first day of employment.

Vacation Accrual by Tenure: Years 0-2: 15 days per year (1.25 days/month). Years 3-5: 20 days per year (1.67 days/month). Years 6+: 25 days per year (2.08 days/month).',
    0,
    84,
    '{"source": "employee_handbook.txt", "section": "5.1 Vacation Policy", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'b2222222-2222-2222-2222-222222222222'::uuid,
    'Requesting Vacation: Submit vacation requests through the HR portal at least two weeks in advance. Requests are approved based on business needs and team coverage. During peak periods (Q4, product launches), vacation requests may be limited.

Carryover Policy: Unused vacation days can be carried over to the next calendar year, up to a maximum of 5 days. Any days beyond this limit will be forfeited on January 1st. We encourage employees to use their vacation time for work-life balance.',
    1,
    82,
    '{"source": "employee_handbook.txt", "section": "5.1 Vacation Policy - Carryover", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'b2222222-2222-2222-2222-222222222222'::uuid,
    'Sick Leave: Employees receive 10 days of paid sick leave annually. Sick leave can be used for: Personal illness or injury, Medical appointments, Caring for immediate family members.

Remote Work: HeroForge supports flexible work arrangements. Employees may work remotely up to 3 days per week with manager approval. Core collaboration hours are 10 AM - 3 PM local time.

Benefits Overview: See the Benefits Guide for complete details on health insurance, 401(k), and other benefits.',
    2,
    85,
    '{"source": "employee_handbook.txt", "section": "5.2-5.3 Sick Leave and Remote Work", "chunk_strategy": "semantic"}'::jsonb
);

-- Chunks for Benefits Guide
INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'c3333333-3333-3333-3333-333333333333'::uuid,
    'Benefits Guide - HeroForge Inc. Annual Leave and Paid Time Off

Employees are entitled to paid annual leave which increases with tenure at the company. Our generous PTO policy reflects our commitment to employee wellbeing.

PTO Allocation: Years 0-2: 15 days (1.25/month). Years 3-5: 20 days (1.67/month). Years 6+: 25 days (2.08/month).

Carryover Rules: Unused vacation can be carried over to the next year, up to 5 days maximum. Plan your time off wisely to maximize this benefit. Days beyond the carryover limit expire on December 31st.',
    0,
    95,
    '{"source": "benefits_guide.txt", "section": "PTO", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'c3333333-3333-3333-3333-333333333333'::uuid,
    'Blackout Periods: During critical business periods, vacation requests may be restricted: Last two weeks of each quarter, Product launch windows, Annual planning (typically January).

Health Insurance: HeroForge provides comprehensive health coverage. Medical Plans: PPO Plan with higher premiums and more flexibility, HMO Plan with lower premiums and network restrictions, HDHP with HSA for tax-advantaged savings. Dental and Vision: Dental coverage included at no extra cost. Vision plan with annual exam and frame allowance.',
    1,
    83,
    '{"source": "benefits_guide.txt", "section": "Health Insurance", "chunk_strategy": "semantic"}'::jsonb
);

INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'c3333333-3333-3333-3333-333333333333'::uuid,
    'Retirement Benefits - 401(k) Plan: Company matches 50% of contributions up to 6% of salary. Immediate vesting. Wide selection of investment options.

Professional Development: $2,000 annual learning stipend. Conference attendance supported. Internal mentorship program.',
    2,
    43,
    '{"source": "benefits_guide.txt", "section": "Retirement and Development", "chunk_strategy": "semantic"}'::jsonb
);

-- Chunks for Remote Work Policy
INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'd4444444-4444-4444-4444-444444444444'::uuid,
    'Remote Work Policy: Employees may work remotely up to 3 days per week. Remote work requests must be approved by direct manager. Equipment: Company provides laptop and monitor for home office setup. Communication: All remote workers must be available during core hours 10am-3pm. Security: Use VPN for all company system access.',
    0,
    57,
    '{"source": "S4 workshop", "section": "full document", "chunk_strategy": "single"}'::jsonb
);

-- Chunks for Company Handbook
INSERT INTO document_chunks (document_id, chunk_text, chunk_index, word_count, metadata)
VALUES (
    'e5555555-5555-5555-5555-555555555555'::uuid,
    'Welcome to our company! This handbook contains all policies and procedures. Section 1: Code of Conduct. Section 2: Benefits. Section 3: Time Off.',
    0,
    25,
    '{"source": "S4 workshop", "section": "full document", "chunk_strategy": "single"}'::jsonb
);

-- ============================================================================
-- STEP 8: Create Helpful Functions for S6 RAG
-- ============================================================================

-- Function to search documents by similarity (will work once embeddings are populated)
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    similarity_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    document_title TEXT,
    chunk_text TEXT,
    chunk_index INT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id AS chunk_id,
        dc.document_id,
        d.title AS document_title,
        dc.chunk_text,
        dc.chunk_index,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE dc.embedding IS NOT NULL
        AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get document with all its chunks
CREATE OR REPLACE FUNCTION get_document_with_chunks(doc_id UUID)
RETURNS TABLE (
    document_id UUID,
    title TEXT,
    content TEXT,
    file_type VARCHAR,
    chunk_id UUID,
    chunk_text TEXT,
    chunk_index INT
)
LANGUAGE SQL
AS $$
    SELECT
        d.id AS document_id,
        d.title,
        d.content,
        d.file_type,
        dc.id AS chunk_id,
        dc.chunk_text,
        dc.chunk_index
    FROM documents d
    LEFT JOIN document_chunks dc ON d.id = dc.document_id
    WHERE d.id = doc_id
    ORDER BY dc.chunk_index;
$$;

-- ============================================================================
-- STEP 9: Verification Queries
-- ============================================================================

-- Verify table creation and data insertion
DO $$
DECLARE
    doc_count INT;
    chunk_count INT;
BEGIN
    SELECT COUNT(*) INTO doc_count FROM documents;
    SELECT COUNT(*) INTO chunk_count FROM document_chunks;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'S6 Demo Setup Complete!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Documents created: %', doc_count;
    RAISE NOTICE 'Chunks created: %', chunk_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run the embeddings pipeline to populate vectors:';
    RAISE NOTICE '   python src/agents/pipeline/orchestrate.py demo-docs/';
    RAISE NOTICE '2. Or generate embeddings for existing chunks';
    RAISE NOTICE '============================================';
END $$;

-- Display summary
SELECT
    'documents' AS table_name,
    COUNT(*) AS row_count
FROM documents
UNION ALL
SELECT
    'document_chunks' AS table_name,
    COUNT(*) AS row_count
FROM document_chunks
UNION ALL
SELECT
    'conversations' AS table_name,
    COUNT(*) AS row_count
FROM conversations
UNION ALL
SELECT
    'messages' AS table_name,
    COUNT(*) AS row_count
FROM messages;
