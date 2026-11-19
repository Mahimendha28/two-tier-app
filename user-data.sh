#!/bin/bash
# User data for the Auto Scaling launch template (Ubuntu)
# Replace the placeholders below before using it.

apt-get update -y
apt-get install -y nginx git python3-pip python3-venv

# Download the application code
git clone https://github.com/Mahimendha28/two-tier-app.git /opt/app
cd /opt/app
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Run Flask (Gunicorn) as a systemd service
cat > /etc/systemd/system/app.service <<EOF
[Unit]
Description=Flask app
After=network.target

[Service]
WorkingDirectory=/opt/app
Environment=DB_HOST=YOUR_RDS_ENDPOINT
Environment=DB_USER=admin
Environment=DB_PASSWORD=YOUR_PASSWORD
Environment=DB_NAME=appdb
ExecStart=/opt/app/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now app

# Nginx reverse proxy: port 80 -> Gunicorn on port 5000
cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

systemctl restart nginx