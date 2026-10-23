-- Starter schema notes for Multi-Vendor Commerce REST API Platform — Capstone; adapt before use.
-- Use synthetic IDs, explicit constraints, and transactions for related writes.
CREATE TABLE api_records (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT,
  name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 200),
  state TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add foreign keys, tenant ownership, unique constraints and indexes from your design.
-- Do not store passwords in plaintext or put secrets in source-controlled files.
