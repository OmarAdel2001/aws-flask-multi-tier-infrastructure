#!/bin/bash
# Send output to log files for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "================ STARTING SYSTEM SETUP ================"

# Force apt to use IPv4 only (prevents stalling on IPv6 mirrors in IPv4 VPC)
echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

# Update package lists
apt-get update -y

# Install dependencies
apt-get install -y --no-install-recommends python3-pip python3-venv curl

# Create App directories
mkdir -p /var/www/webapp/templates

# Setup python virtual environment
python3 -m venv /var/www/webapp/venv
source /var/www/webapp/venv/bin/activate

# Upgrade pip and install AWS CLI inside virtualenv
pip install --upgrade pip
pip install awscli

# Pull application files from S3 deployment bucket using virtualenv's awscli
echo "Downloading application assets from S3 bucket ${app_bucket_name}..."
/var/www/webapp/venv/bin/aws s3 cp s3://${app_bucket_name}/requirements.txt /var/www/webapp/requirements.txt
/var/www/webapp/venv/bin/aws s3 cp s3://${app_bucket_name}/app.py /var/www/webapp/app.py
/var/www/webapp/venv/bin/aws s3 cp s3://${app_bucket_name}/index.html /var/www/webapp/templates/index.html

# Install pip requirements
pip install -r /var/www/webapp/requirements.txt

# Deactivate venv
deactivate

# Setup Systemd Service
cat << 'EOF' > /etc/systemd/system/webapp.service
[Unit]
Description=Gunicorn instance to serve flask application
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/webapp
Environment="PATH=/var/www/webapp/venv/bin"
Environment="DB_PRIMARY_HOST=${db_primary_host}"
Environment="DB_REPLICA_HOST=${db_replica_host}"
Environment="DB_NAME=${db_name}"
Environment="DB_USER=${db_username}"
Environment="DB_PASSWORD=${db_password}"
ExecStart=/var/www/webapp/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, start and enable webapp service
systemctl daemon-reload
systemctl start webapp
systemctl enable webapp

echo "================ SYSTEM SETUP COMPLETE ================"
