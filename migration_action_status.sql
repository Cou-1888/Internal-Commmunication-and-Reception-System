-- Migration: Add action_status column to messages table for view/reply tracking
-- Run: mysql -u root -p zaka_rdc_db < migration_action_status.sql

ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS action_status VARCHAR(50) DEFAULT 'new' AFTER is_read;

-- Set existing messages to 'new' if null
UPDATE messages 
SET action_status = 'new' 
WHERE action_status IS NULL OR action_status = '';

SELECT 
    'Migration complete! Added action_status column.',
    CONCAT('Total messages: ', (SELECT COUNT(*) FROM messages)),
    CONCAT('New status: ', (SELECT COUNT(*) FROM messages WHERE action_status = 'new'))
AS status;
