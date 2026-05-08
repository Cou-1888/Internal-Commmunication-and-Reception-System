from datetime import datetime, timedelta
import mysql.connector
import os

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='c@to10%Z',
        database='zaka_rdc_db'
    )

# Clear old data (optional - comment out if keep existing)
conn = get_db()
cursor = conn.cursor()

tables = ['incoming_mails', 'outgoing_mails', 'call_records', 'messages']
for table in tables:
    cursor.execute(f'DELETE FROM {table}')
conn.commit()

# Sample incoming_mails (last 7 days)
yesterday = datetime.now() - timedelta(days=1)
day_before = datetime.now() - timedelta(days=2)
cursor.execute("""
INSERT INTO incoming_mails (subject, sender, department, date_received, status) VALUES 
(%s, %s, %s, %s, %s),
(%s, %s, %s, %s, %s)
""", [
    ('Budget Approval', 'Finance Dept', 'Finance', yesterday, 'Pending'),
    ('Project Update', 'CEO', 'CEO', day_before, 'Processed')
])
conn.commit()

# Outgoing_mails
cursor.execute("""
INSERT INTO outgoing_mails (subject, recipient, department, date_sent, status) VALUES 
(%s, %s, %s, %s, %s)
""", [
    ('Response to Budget', 'Finance', 'IT', yesterday, 'Sent')
])

# Call_records - FIXED columns to match schema (no caller_name/phone)
cursor.execute("""
INSERT INTO call_records (caller, duration, purpose, date) VALUES 
(%s, %s, %s, %s),
(%s, %s, %s, %s)
""", [
    ('John Doe', '5 min', 'Inquiry', yesterday.date()),
    ('Jane Smith', '3 min', 'Complaint', day_before.date())
])
conn.commit()

# Messages - FIXED: Ensure staff exists first (uses existing names)
cursor.execute("INSERT IGNORE INTO staff (id, fullname, username, department, role) VALUES (1, 'System Admin', 'admin', 'IT', 'IT Admin')")
cursor.execute("""
INSERT INTO messages (sender_id, sender_name, sender_department, recipient_department, subject, message, is_urgent, created_at) VALUES 
(1, %s, %s, %s, %s, %s, %s, %s)
""", ('System Admin', 'IT', 'Finance', 'URGENT Server Maintenance', 'Maintenance tonight', 1, datetime.now()))

conn.commit()
cursor.close()
conn.close()

print('Sample data inserted safely for reports trends! sender_id error fixed. Check last 7 days data.')
