-- Message System Migration: Add is_read column for unread counting + urgent beep
-- Run: mysql -u root -p zaka_rdc_db < database_migration.sql

ALTER TABLE messages 
ADD COLUMN is_read TINYINT(1) DEFAULT 0 AFTER is_urgent;

-- Migrate existing replies as read (safe default)
UPDATE messages 
SET is_read = 1 
WHERE parent_message_id IS NOT NULL;

-- Mark older messages as read (optional - comment out if you want all existing as unread)
-- UPDATE messages SET is_read = 1 WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);

SELECT 
    'Migration complete! Added is_read column.'
    'Existing replies marked as read.',
    CONCAT('Unread urgent for IT: ', (SELECT COUNT(*) FROM messages WHERE recipient_department = 'IT' AND is_urgent = 1 AND is_read = 0)),
    CONCAT('Total unread for IT: ', (SELECT COUNT(*) FROM messages WHERE recipient_department = 'IT' AND is_read = 0)) 
AS status;

