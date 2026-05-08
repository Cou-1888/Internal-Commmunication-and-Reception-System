from werkzeug.security import generate_password_hash
import mysql.connector

# Connect to your Zaka DB
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="c@to10%Z", # Put your actual MySQL password here
    database="zaka_rdc_db"
)
cursor = db.cursor()

# 1. Clear the old staff table to avoid confusion
cursor.execute("DELETE FROM staff")

# 2. Create a fresh Admin with a HASHED password
hashed_pw = generate_password_hash('admin123')
sql = "INSERT INTO staff (fullname, username, password, department, role) VALUES (%s, %s, %s, %s, %s)"
values = ('System Admin', 'admin', hashed_pw, 'IT', 'IT Admin')

cursor.execute(sql, values)
db.commit()

print("Success! You can now login with: admin / admin123")
db.close()
