-- Discovery Reports table for Product Discovery Service
-- Run this in Supabase SQL Editor to enable report persistence

CREATE TABLE IF NOT EXISTS "DiscoveryReports" (
  id TEXT PRIMARY KEY,
  user_email TEXT NOT NULL,
  category TEXT NOT NULL,
  keywords TEXT NOT NULL,
  marketplace TEXT NOT NULL,
  report_markdown TEXT,
  report_html TEXT,
  generated_at TEXT,
  model_used TEXT,
  sources_count INTEGER DEFAULT 0,
  asins_analyzed INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Service role (SUPABASE_SERVICE_ROLE_KEY) bypasses RLS by default
