/**
 * SECURITY WARNING:
 * - SUPABASE_ANON_KEY is safe to expose (it's designed for client-side use with RLS)
 * - NEVER put SUPABASE_SERVICE_ROLE_KEY here (it bypasses RLS)
 * - N8N webhook URLs should be proxied through backend, not exposed here
 */
const SUPABASE_URL = 'YOUR_SUPABASE_URL_HERE';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY_HERE';
const PAYPAL_PAYMENT_URL = 'https://www.paypal.com/ncp/payment/2Z7UB3AXAUQYG';
// N8N webhook URL removed - use backend proxy /api/proxy/* instead
const N8N_PAYMENT_WEBHOOK_URL = '';

// Initialize Supabase client if library is loaded
let supabaseClient = null;
if (typeof supabase !== 'undefined') {
    supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
} else {
    console.warn('Supabase library not loaded');
}
