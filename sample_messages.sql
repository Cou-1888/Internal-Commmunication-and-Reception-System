-- Fixed sample messages with THREADS for testing chat history
-- Run: mysql -u root -p zaka_rdc_db < sample_messages.sql

-- Ensure staff exists
INSERT IGNORE INTO staff (id, fullname, username, department, role) VALUES 
(1, 'System Admin', 'admin', 'IT', 'IT Admin'),
(2, 'Finance Team', 'finance', 'Finance', 'Staff'),
(3, 'CEO Office', 'ceo', 'CEO', 'CEO');

-- Thread 1: Budget discussion (IT <-> Finance)
INSERT INTO messages (sender_id, sender_name, sender_department, recipient_department, subject, message, is_urgent, parent_message_id, created_at) VALUES
-- Root
(2, 'Finance Team', 'Finance', 'IT', 'Budget approval needed', 'IT budget Q2 approved. Please allocate resources accordingly.', 1, NULL, NOW()),
-- Reply 1 (IT responds)
(1, 'System Admin', 'IT', 'Finance', 'Re: Budget approval needed', 'Thanks Finance. Will start procurement tomorrow. Any specific vendors?', 0, 1, NOW()),
-- Reply 2 (Finance replies)
(2, 'Finance Team', 'Finance', 'IT', 'Re: Budget approval needed', 'Use approved vendors list. Urgent - need by end of week.', 1, 2, NOW()),

-- Thread 2: Server maintenance (IT internal + CEO)
(1, 'System Admin', 'IT', 'CEO', 'URGENT: Server maintenance tonight', 'Server reboot at 22:00. All backups complete?', 1, NULL, NOW()),
(3, 'CEO Office', 'CEO', 'IT', 'Re: URGENT: Server maintenance tonight', 'Approved. Ensure no downtime during business hours tomorrow.', 0, 4, NOW()),

-- Thread 3: Non-urgent report (no replies)
(1, 'System Admin', 'IT', 'IT', 'Weekly report review', 'Weekly stats attached. Feedback by Friday please.', 0, NULL, NOW());

SELECT 'Sample THREADS inserted! Test: Visit /messages2 → View Thread (no 500, full history with replies)' as status;
