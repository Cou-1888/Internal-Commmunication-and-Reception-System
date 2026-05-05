#!/bin/bash

# Deployment script for Reception System on Ubuntu 20.04 VPS
# Run this in the project directory on the VPS

set -e  # Exit on any error

echo "=== Reception System Deployment Script ==="
echo "This script will set up the Reception System on Ubuntu 20.04"
echo ""

# Function to check if command succeeded
check_command() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed. Exiting."
        exit 1
    fi
}

# Update system packages
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y
check_command "System update"

# Install required packages
echo "2. Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx git ufw
check_command "Package installation"

# Secure MySQL installation
echo "3. Securing MySQL installation..."
sudo mysql_secure_installation
check_command "MySQL secure installation"

# Create database and user
echo "4. Setting up MySQL database..."
MYSQL_ROOT_PASSWORD="CHANGE_THIS_SECURE_PASSWORD"
MYSQL_USER="reception_user"
MYSQL_PASSWORD="CHANGE_THIS_USER_PASSWORD"
MYSQL_DB="zaka_rdc_db"

sudo mysql -u root -p$MYSQL_ROOT_PASSWORD <<EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DB;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DB.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
check_command "Database setup"

# Create project directory
echo "5. Creating project directory..."
sudo mkdir -p /var/www/html/reception-system
sudo chown -R $USER:$USER /var/www/html/reception-system
check_command "Directory creation"

# Copy project files (assuming they're uploaded to /tmp/reception-system)
echo "6. Copying project files..."
# Note: Upload your project files to /tmp/reception-system first
cp -r /tmp/reception-system/* /var/www/html/reception-system/
check_command "File copy"

# Set up virtual environment
echo "7. Setting up Python virtual environment..."
cd /var/www/html/reception-system
python3 -m venv venv
source venv/bin/activate
check_command "Virtual environment setup"

# Install Python dependencies
echo "8. Installing Python dependencies..."
pip install -r requirements.txt
check_command "Python dependencies installation"

# Set up environment variables
echo "9. Setting up environment variables..."
cat > .env <<EOF
DB_HOST=localhost
DB_USER=$MYSQL_USER
DB_PASSWORD=$MYSQL_PASSWORD
DB_NAME=$MYSQL_DB
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_KEY_IN_PRODUCTION
EOF
check_command "Environment variables setup"

# Set up database
echo "10. Setting up database tables..."
export DB_HOST=localhost
export DB_USER=$MYSQL_USER
export DB_PASSWORD=$MYSQL_PASSWORD
export DB_NAME=$MYSQL_DB
python3 setup_db.py
check_command "Database table setup"

# Create admin user
echo "11. Creating admin user..."
python3 create_admin.py
check_command "Admin user creation"

# Install Gunicorn
echo "12. Installing Gunicorn..."
pip install gunicorn
check_command "Gunicorn installation"

# Create systemd service
echo "13. Creating systemd service..."
sudo tee /etc/systemd/system/reception-system.service > /dev/null <<EOF
[Unit]
Description=Reception System Flask App
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=/var/www/html/reception-system
Environment="PATH=/var/www/html/reception-system/venv/bin"
EnvironmentFile=/var/www/html/reception-system/.env
ExecStart=/var/www/html/reception-system/venv/bin/gunicorn --workers 3 --bind unix:reception-system.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
check_command "Systemd service creation"

# Start and enable service
echo "14. Starting and enabling service..."
sudo systemctl daemon-reload
sudo systemctl start reception-system
sudo systemctl enable reception-system
check_command "Service start/enable"

# Configure Nginx
echo "15. Configuring Nginx..."
sudo tee /etc/nginx/sites-available/reception-system > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static {
        alias /var/www/html/reception-system/static;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/html/reception-system/reception-system.sock;
    }
}
EOF
check_command "Nginx configuration"

# Enable site
echo "16. Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/reception-system /etc/nginx/sites-enabled
sudo nginx -t
check_command "Nginx test"
sudo systemctl restart nginx
check_command "Nginx restart"

# Configure firewall
echo "17. Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
check_command "Firewall configuration"

# Final checks
echo "18. Running final checks..."
sudo systemctl status reception-system --no-pager
sudo systemctl status nginx --no-pager
curl -I http://localhost
check_command "Final checks"

echo ""
echo "=== Deployment Complete! ==="
echo "Your Reception System is now running at http://your-server-ip"
echo ""
echo "Important security steps to complete:"
echo "1. Change the default passwords in this script and .env file"
echo "2. Set a secure SECRET_KEY in .env"
echo "3. If using a domain, update server_name in Nginx config"
echo "4. Consider setting up SSL with Let's Encrypt"
echo "5. Regularly update your system and dependencies"
echo ""
echo "Admin login: admin / admin123 (change this immediately!)"
