import re

with open("discovery_service/main.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Imports and variable declarations
text = re.sub(r'# Payment state persistence.*?_load_payment_state\(\)', 'from . import payment_store', text, flags=re.DOTALL)

# 2. 
text = re.sub(r'full_report_unlocked = \(not is_pro_report\) or \(report_id in paid_orders\)', 'full_report_unlocked = (not is_pro_report) or payment_store.is_order_paid(report_id)', text)

# 3.
text = re.sub(r'if request\.user_email not in paid_reports:', 'if not payment_store.is_email_paid(request.user_email):', text)

# 4.
text = re.sub(r'if session_id in verified_sessions:', 'if payment_store.is_session_verified(session_id):', text)
text = re.sub(r'"source":\s*"memory"', '"source": "supabase"', text)

# 5.
text = re.sub(r'verified_sessions\.add\(session_id\)\s*_persist_payment_state\(\)', 'payment_store.add_verified_session(session_id)', text)

# 6.
text = re.sub(r'if req\.session_id not in verified_sessions:', 'if not payment_store.is_session_verified(req.session_id):', text)

# 7.
text = re.sub(r'verified_sessions\.add\(req\.session_id\)\s*_persist_payment_state\(\)', 'payment_store.add_verified_session(req.session_id)', text)

# 8.
text = re.sub(r'already_paid = req\.report_id in paid_orders\s*paid_orders\.add\(req\.report_id\)\s*_persist_payment_state\(\)', 'already_paid = payment_store.is_order_paid(req.report_id)\n    if not already_paid:\n        payment_store.add_paid_order(req.report_id)', text)

# 9.
text = re.sub(r'verified_sessions\.add\(req\.session_id\)\s*if req\.customer_email:\s*paid_reports\.add\(req\.customer_email\)\s*if req\.order_id:\s*paid_orders\.add\(req\.order_id\)\s*if req\.customer_email:\s*paid_order_to_email\[req\.order_id\] = req\.customer_email\s*_persist_payment_state\(\)', 'payment_store.add_verified_session(req.session_id)\n    if req.customer_email:\n        payment_store.add_paid_email(req.customer_email)\n    if req.order_id:\n        payment_store.add_paid_order(req.order_id, req.customer_email)', text)

# 10.
text = re.sub(r'paid_reports\.add\(email\)', 'payment_store.add_paid_email(email)', text)
text = re.sub(r'paid_orders\.add\(order_id\)\s*if email:\s*paid_order_to_email\[order_id\] = email', 'payment_store.add_paid_order(order_id, email)', text)
text = re.sub(r'verified_sessions\.add\(checkout_id\)\s*_persist_payment_state\(\)', 'payment_store.add_verified_session(checkout_id)', text)

with open("discovery_service/main.py", "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

print("Flexible patch applied successfully")
