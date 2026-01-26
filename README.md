# ipmonitor
Simple script to monitor IP status with Dashboard &amp; Discord Webhook notification
#####################################
#24.04.3 LTS (Noble Numbat)
############################

sudo apt update && sudo apt upgrade -y
sudo apt install -y nmap python3 python3-pip python3-venv git curl wget build-essential

sudo useradd -m -s /bin/bash ipmonitor
sudo usermod -aG sudo ipmonitor
sudo passwd ipmonitor

# As ipmonitor user
sudo -u ipmonitor -i
cd /home/ipmonitor

# Create project directory
mkdir ip-monitor
cd ip-monitor


# Check ping permissions
ls -la /bin/ping
ls -la /usr/bin/ping

# Make sure ipmonitor can use ping
sudo setcap cap_net_raw+ep /bin/ping 2>/dev/null || true

sudo setcap cap_net_raw+ep /usr/bin/ping 2>/dev/null || true


mkdir data
mkdir -p app/{utils,monitor,api,static}

# Create __init__.py files
touch app/__init__.py
touch app/utils/__init__.py
touch app/monitor/__init__.py
touch app/api/__init__.py


# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip3 install --upgrade pip
pip3 install -r requirements.txt

###############################################################################################################

sudo nano /etc/systemd/system/ipmonitor.service

[Unit]
Description=IP Monitor Dashboard Service
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ipmonitor
Group=ipmonitor
WorkingDirectory=/home/ipmonitor/ip-monitor
Environment="PATH=/home/ipmonitor/ip-monitor/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/home/ipmonitor/ip-monitor"
Environment="HOME=/home/ipmonitor"
Environment="USER=ipmonitor"
Environment="LOGNAME=ipmonitor"

# Use full path to python and main.py
ExecStart=/home/ipmonitor/ip-monitor/venv/bin/python /home/ipmonitor/ip-monitor/main.py

# Standard service settings
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ipmonitor

# Set proper capabilities for ping
AmbientCapabilities=CAP_NET_RAW
CapabilityBoundingSet=CAP_NET_RAW

# Security settings (less restrictive for ping to work)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/home/ipmonitor/ip-monitor/data
ProtectHome=read-only

# Allow network access
PrivateNetwork=false

[Install]
WantedBy=multi-user.target



# Enable systemd service
sudo systemctl daemon-reload
sudo systemctl enable ipmonitor.service
sudo systemctl start ipmonitor.service

# Check status
sudo systemctl status ipmonitor.service

# View logs
sudo journalctl -u ipmonitor.service -f



# Check service status
sudo systemctl status ipmonitor

# View logs
sudo journalctl -u ipmonitor -f

# Restart service
sudo systemctl restart ipmonitor

# Stop service
sudo systemctl stop ipmonitor

# Check disk space for logs
df -h /home/ipmonitor

# Check memory usage
free -h

# Check if service is accessible
curl -I http://localhost:8000



#######################################################################################################################################################################



sudo nano /etc/logrotate.d/ipmonitor

/home/ipmonitor/ip-monitor/data/logs/monitor.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 ipmonitor ipmonitor
    sharedscripts
    copytruncate
    dateext
    dateformat .%Y-%m-%d
    
    postrotate
        pkill -USR1 -f "python.*main.py" 2>/dev/null || true
    endscript
}



# Check current log file
ls -la /home/ipmonitor/ip-monitor/data/logs/

# Check log file permissions
stat /home/ipmonitor/ip-monitor/data/logs/monitor.log

# View current log
tail -f /home/ipmonitor/ip-monitor/data/logs/monitor.log



##############################################Test Logrotate Configuration#####################################
# Test logrotate configuration (dry run)
sudo logrotate -d /etc/logrotate.d/ipmonitor

# Force logrotate to run now (for testing)
sudo logrotate -vf /etc/logrotate.d/ipmonitor

# Check what happened
ls -la /home/ipmonitor/ip-monitor/data/logs/

# Check if rotated files exist
ls -la /home/ipmonitor/ip-monitor/data/logs/*.gz 2>/dev/null || echo "No rotated logs yet"



##############################################Create a Test Log Entry#####################################
# Add a test log entry
sudo -u ipmonitor bash -c 'cd /home/ipmonitor/ip-monitor && source venv/bin/activate && python -c "from loguru import logger; logger.info(\"Test log entry for rotation\")"'

# Check the log
tail -5 /home/ipmonitor/ip-monitor/data/logs/monitor.log



##############################################Manual Rotation Test#####################################
# Backup current log
sudo cp /home/ipmonitor/ip-monitor/data/logs/monitor.log /home/ipmonitor/ip-monitor/data/logs/monitor.log.bak

# Create a large log file to trigger rotation
sudo dd if=/dev/zero of=/home/ipmonitor/ip-monitor/data/logs/monitor.log bs=1M count=10

# Run logrotate manually
sudo logrotate -vf /etc/logrotate.d/ipmonitor

# Check results
ls -lh /home/ipmonitor/ip-monitor/data/logs/







