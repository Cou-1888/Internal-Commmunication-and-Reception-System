<<<<<<< HEAD
import mysql.connector
from werkzeug.security import generate_password_hash

import os

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'c@to10%Z'),
        database=os.environ.get('DB_NAME', 'zaka_rdc_db')
    )

# Create database if it doesn't exist
def create_database():
    db_user = os.environ.get('DB_USER', 'root')
    db_pw = os.environ.get('DB_PASSWORD', 'c@to10%Z')
    
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="c@to10%Z"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS zaka_rdc_db")
    cursor.close()
    conn.close()

# Create tables if they don't exist
def create_tables():
    create_database()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop messages first (due to foreign key constraint)
    cursor.execute("DROP TABLE IF EXISTS messages")
    
    # Create staff table
    cursor.execute("DROP TABLE IF EXISTS staff")
    cursor.execute("""
        CREATE TABLE staff (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fullname VARCHAR(100) NOT NULL,
            department VARCHAR(50) NOT NULL,
            role ENUM('Receptionist', 'IT Admin', 'Staff') NOT NULL DEFAULT 'Staff'
        )
    """)

    # Create incoming_mails table
    cursor.execute("DROP TABLE IF EXISTS incoming_mails")
    cursor.execute("""
        CREATE TABLE incoming_mails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date_received DATETIME NOT NULL,
            sender VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            content TEXT,
            department VARCHAR(50) DEFAULT 'General',
            attachment VARCHAR(255),
            status ENUM('Read', 'Unread') DEFAULT 'Unread'
        )
    """)

    # Create outgoing_mails table
    cursor.execute("DROP TABLE IF EXISTS outgoing_mails")
    cursor.execute("""
        CREATE TABLE outgoing_mails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date_sent DATETIME NOT NULL,
            recipient VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            content TEXT,
            department VARCHAR(50) DEFAULT 'General',
            attachment VARCHAR(255),
            status ENUM('Draft', 'Sent', 'Delivered') DEFAULT 'Draft'
        )
    """)

    # Create call_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            caller VARCHAR(100) NOT NULL,
            duration VARCHAR(20) NOT NULL,
            purpose VARCHAR(255) NOT NULL
        )
    """)

    # Create forms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type ENUM('Free', 'Sold') NOT NULL,
            description TEXT,
            unlock_key VARCHAR(255),
            attachment VARCHAR(255)
        )
    """)

    # Create master_key table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_key (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_value VARCHAR(255) NOT NULL
        )
    """)

    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL DEFAULT 1,
            sender_name VARCHAR(100) NOT NULL,
            sender_department VARCHAR(50) NOT NULL,
            recipient_department VARCHAR(50) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            is_urgent TINYINT(1) DEFAULT 0,
            is_read TINYINT(1) DEFAULT 0,
            action_status VARCHAR(50) DEFAULT 'new',
            attachment VARCHAR(255),
            parent_message_id INT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES staff(id),
            FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL
        )
    """)



    # Incoming mails
    cursor.execute("INSERT IGNORE INTO incoming_mails (date_received, sender, subject, content, status) VALUES ('2023-10-01 10:00:00', 'John Doe', 'Land Inquiry', 'Details about land inquiry.', 'Unread')")
    cursor.execute("INSERT IGNORE INTO incoming_mails (date_received, sender, subject, content, status) VALUES ('2023-10-02 11:00:00', 'Jane Smith', 'Permit Request', 'Request for building permit.', 'Read')")

    # Outgoing mails
    cursor.execute("INSERT IGNORE INTO outgoing_mails (date_sent, recipient, subject, content, status) VALUES ('2023-10-01 10:00:00', 'City Council', 'Approval Response', 'Response details.', 'Sent')")
    cursor.execute("INSERT IGNORE INTO outgoing_mails (date_sent, recipient, subject, content, status) VALUES ('2023-10-02 11:00:00', 'Applicant XYZ', 'Document Dispatch', 'Dispatch details.', 'Sent')")

    # Call records
    cursor.execute("INSERT IGNORE INTO call_records (date, caller, duration, purpose) VALUES ('2023-10-01', 'Resident A', '5 min', 'Complaint')")
    cursor.execute("INSERT IGNORE INTO call_records (date, caller, duration, purpose) VALUES ('2023-10-02', 'Business B', '10 min', 'Inquiry')")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database and tables created successfully with sample data.")

if __name__ == "__main__":
    create_tables()
=======
import mysql.connector
from werkzeug.security import generate_password_hash

import os

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'c@to10%Z'),
        database=os.environ.get('DB_NAME', 'zaka_rdc_db')
    )

# Create database if it doesn't exist
def create_database():
    db_user = os.environ.get('DB_USER', 'root')
    db_pw = os.environ.get('DB_PASSWORD', 'c@to10%Z')
    
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="c@to10%Z"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS zaka_rdc_db")
    cursor.close()
    conn.close()

# Create tables if they don't exist
def create_tables():
    create_database()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop messages first (due to foreign key constraint)
    cursor.execute("DROP TABLE IF EXISTS messages")
    
    # Create staff table
    cursor.execute("DROP TABLE IF EXISTS staff")
    cursor.execute("""
        CREATE TABLE staff (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fullname VARCHAR(100) NOT NULL,
            department VARCHAR(50) NOT NULL,
            role ENUM('Receptionist', 'IT Admin', 'Staff') NOT NULL DEFAULT 'Staff'
        )
    """)

    # Create incoming_mails table
    cursor.execute("DROP TABLE IF EXISTS incoming_mails")
    cursor.execute("""
        CREATE TABLE incoming_mails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date_received DATETIME NOT NULL,
            sender VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            content TEXT,
            department VARCHAR(50) DEFAULT 'General',
            attachment VARCHAR(255),
            status ENUM('Read', 'Unread') DEFAULT 'Unread'
        )
    """)

    # Create outgoing_mails table
    cursor.execute("DROP TABLE IF EXISTS outgoing_mails")
    cursor.execute("""
        CREATE TABLE outgoing_mails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date_sent DATETIME NOT NULL,
            recipient VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            content TEXT,
            department VARCHAR(50) DEFAULT 'General',
            attachment VARCHAR(255),
            status ENUM('Draft', 'Sent', 'Delivered') DEFAULT 'Draft'
        )
    """)

    # Create call_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            caller VARCHAR(100) NOT NULL,
            duration VARCHAR(20) NOT NULL,
            purpose VARCHAR(255) NOT NULL
        )
    """)

    # Create forms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type ENUM('Free', 'Sold') NOT NULL,
            description TEXT,
            unlock_key VARCHAR(255),
            attachment VARCHAR(255)
        )
    """)

    # Create master_key table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_key (
            id INT AUTO_INCREMENT PRIMARY KEY,
            key_value VARCHAR(255) NOT NULL
        )
    """)

    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL DEFAULT 1,
            sender_name VARCHAR(100) NOT NULL,
            sender_department VARCHAR(50) NOT NULL,
            recipient_department VARCHAR(50) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            is_urgent TINYINT(1) DEFAULT 0,
            is_read TINYINT(1) DEFAULT 0,
            action_status VARCHAR(50) DEFAULT 'new',
            attachment VARCHAR(255),
            parent_message_id INT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES staff(id),
            FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL
        )
    """)



    # Incoming mails
    cursor.execute("INSERT IGNORE INTO incoming_mails (date_received, sender, subject, content, status) VALUES ('2023-10-01 10:00:00', 'John Doe', 'Land Inquiry', 'Details about land inquiry.', 'Unread')")
    cursor.execute("INSERT IGNORE INTO incoming_mails (date_received, sender, subject, content, status) VALUES ('2023-10-02 11:00:00', 'Jane Smith', 'Permit Request', 'Request for building permit.', 'Read')")

    # Outgoing mails
    cursor.execute("INSERT IGNORE INTO outgoing_mails (date_sent, recipient, subject, content, status) VALUES ('2023-10-01 10:00:00', 'City Council', 'Approval Response', 'Response details.', 'Sent')")
    cursor.execute("INSERT IGNORE INTO outgoing_mails (date_sent, recipient, subject, content, status) VALUES ('2023-10-02 11:00:00', 'Applicant XYZ', 'Document Dispatch', 'Dispatch details.', 'Sent')")

    # Call records
    cursor.execute("INSERT IGNORE INTO call_records (date, caller, duration, purpose) VALUES ('2023-10-01', 'Resident A', '5 min', 'Complaint')")
    cursor.execute("INSERT IGNORE INTO call_records (date, caller, duration, purpose) VALUES ('2023-10-02', 'Business B', '10 min', 'Inquiry')")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database and tables created successfully with sample data.")

if __name__ == "__main__":
    create_tables()
>>>>>>> 2cbdefb (Prepare for Render deployment)
