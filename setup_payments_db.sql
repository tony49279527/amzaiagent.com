-- ==========================================
-- Setup PaymentState Table
-- Run this in your Supabase SQL Editor
-- ==========================================
-- Tracks ephemeral payment verifications to ensure multi-instance 
-- consistency on Google Cloud Run. 

CREATE TABLE IF NOT EXISTS public."PaymentState" (
    key text primary key,
    value jsonb not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Note: Adjust RLS policies if you plan to access this from the frontend. 
-- Since it's server-side access only via Service Role Key, RLS can be left default or explicit:
ALTER TABLE public."PaymentState" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all for service-role only" ON public."PaymentState" FOR ALL USING (auth.role() = 'service_role');
