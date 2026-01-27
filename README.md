# 🌐 IP Monitor Dashboard - Real-Time Network Device Monitoring Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-orange.svg)](https://ubuntu.com/)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com/NNLixon/ipmonitor)
[![GitHub stars](https://img.shields.io/github/stars/NNLixon/ipmonitor?style=social)](https://github.com/NNLixon/ipmonitor/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NNLixon/ipmonitor?style=social)](https://github.com/NNLixon/ipmonitor/network/members)

> **A lightweight, open-source, real-time IP monitoring dashboard** for tracking network device availability, uptime monitoring, and automated ping checks. Perfect for system administrators, network engineers, and DevOps professionals managing server infrastructure and network devices.

[🚀 Quick Start](#-quick-installation) | [📖 Documentation](#-directory-structure) | [💡 Features](#-features) | [🤝 Contributing](#-contributing) | [📝 License](#-license)

---

## 🎯 Overview

**IP Monitor Dashboard** is a Python-based network monitoring solution that provides real-time visibility into your network infrastructure. Monitor servers, routers, switches, IoT devices, and any IP-enabled equipment with automatic ping checks, web-based dashboard, and systemd integration for 24/7 operation.

### Perfect For:
- 🏢 **Network Administrators** - Monitor enterprise network infrastructure
- 💻 **System Administrators** - Track server uptime and availability
- 🔧 **DevOps Engineers** - Infrastructure monitoring and alerting
- 🏠 **Home Lab Enthusiasts** - Monitor personal network devices
- 🏭 **IoT Projects** - Track IoT device connectivity

### Key Benefits:
- ✅ **Zero Cost** - Completely free and open-source
- ✅ **Easy Setup** - Install in under 10 minutes
- ✅ **Low Resource Usage** - Runs on minimal hardware (512MB RAM)
- ✅ **Production Ready** - Systemd service with auto-restart
- ✅ **Real-time Updates** - WebSocket-based live monitoring
- ✅ **Secure by Design** - Dedicated user with limited capabilities

---

## 📊 Features

### Core Monitoring Capabilities
- 🎯 **Real-Time IP Monitoring** - Continuous availability checks via ICMP ping
- 📡 **Network Device Tracking** - Monitor servers, routers, switches, IoT devices
- ⚡ **Fast Response Time** - Instant detection of device status changes
- 📊 **Web Dashboard** - Clean, intuitive browser-based interface
- 🔄 **Auto-Refresh** - WebSocket support for live updates
- 📝 **Logging System** - Comprehensive event logging with rotation
- 🔔 **Alert Notifications** - Discord webhook integration for alerts
- 🌐 **Subnet Scanner** - Discover devices on your network
- 👥 **Device Grouping** - Organize devices into logical groups
- 📈 **Uptime Statistics** - Track availability metrics over time

### Technical Features
- ⚙️ **Systemd Integration** - Run as a system service with auto-start
- 🔒 **Security Hardened** - Limited capabilities, isolated user, protected filesystem
- 🐍 **Python 3.8+** - Modern Python with async support
- 🔧 **Configurable Intervals** - Customize ping frequency per device
- 💾 **Persistent Storage** - JSON-based data storage
- 🔌 **REST API** - RESTful endpoints for automation
- 🚀 **Lightweight** - Minimal dependencies and resource usage
- 📦 **Easy Deployment** - Virtual environment with all dependencies included

---

## 🖥️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Operating System** | Ubuntu 20.04 LTS | Ubuntu 24.04.3 LTS (Noble Numbat) |
| **RAM** | 512 MB | 1 GB |
| **Storage** | 200 MB | 500 MB |
| **Python** | 3.8 | 3.10+ |
| **Network** | Internet connection | Stable network connection |
| **CPU** | 1 Core | 2+ Cores |

### Supported Platforms:
- ✅ Ubuntu 24.04 LTS (Noble Numbat) - **Primary**
- ✅ Ubuntu 22.04 LTS (Jammy Jellyfish)
- ✅ Ubuntu 20.04 LTS (Focal Fossa)
- ✅ Debian 11+ (Bullseye)
- ⚠️ Other Linux distributions (may require adjustments)

---

## 🚀 Quick Installation

### Prerequisites
Ensure your system is up-to-date:

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 1: Install System Dependencies

Install required packages for Python, networking tools, and development:

```bash
sudo apt install -y nmap python3 python3-pip python3-venv git curl wget build-essential
```

**What's installed:**
- `nmap` - Network scanning utility
- `python3` - Python runtime
- `python3-pip` - Python package manager
- `python3-venv` - Virtual environment support
- `git` - Version control
- `curl` & `wget` - Download utilities
- `build-essential` - Compilation tools

### Step 2: Create Dedicated System User

For security best practices, create an isolated user:

```bash
# Create user with home directory
sudo useradd -m -s /bin/bash ipmonitor

# Add to sudo group (for service management)
sudo usermod -aG sudo ipmonitor

# Set secure password
sudo passwd ipmonitor
```

> 🔐 **Security Tip:** Use a strong password with uppercase, lowercase, numbers, and special characters.

### Step 3: Switch to ipmonitor User

```bash
sudo -u ipmonitor -i
```

### Step 4: Configure Ping Permissions

Grant ping capabilities without requiring root:

```bash
# Set capabilities for ping binary
sudo setcap cap_net_raw+ep /bin/ping 2>/dev/null || true
sudo setcap cap_net_raw+ep /usr/bin/ping 2>/dev/null || true
```

### Step 5: Clone Repository & Setup Application

```bash
# Navigate to user home directory
cd /home/ipmonitor

# Clone the repository
git clone https://github.com/NNLixon/ipmonitor.git

# Enter project directory
cd ipmonitor

# Copy environment template
cp .env.example .env

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### Step 6: Configure Application (Optional)

Edit the `.env` file to customize settings:

```bash
nano .env
```

**Available configurations:**
- Server port (default: 8000)
- Ping interval (default: 60 seconds)
- Discord webhook URL (for notifications)
- Log levels and retention

---

## 🔧 Systemd Service Setup

### Create Systemd Service File

Create a system service for automatic startup and management:

```bash
sudo nano /etc/systemd/system/ipmonitor.service
```

### Service Configuration

Copy and paste this production-ready configuration:

```ini
[Unit]
Description=IP Monitor Dashboard - Network Device Monitoring Service
Documentation=https://github.com/NNLixon/ipmonitor
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ipmonitor
Group=ipmonitor
WorkingDirectory=/home/ipmonitor/ipmonitor

# Environment variables
Environment="PATH=/home/ipmonitor/ipmonitor/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/home/ipmonitor/ipmonitor"
Environment="HOME=/home/ipmonitor"
Environment="USER=ipmonitor"
Environment="LOGNAME=ipmonitor"

# Service execution
ExecStart=/home/ipmonitor/ipmonitor/venv/bin/python /home/ipmonitor/ipmonitor/main.py

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ipmonitor

# Security settings
AmbientCapabilities=CAP_NET_RAW
CapabilityBoundingSet=CAP_NET_RAW
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/home/ipmonitor/ipmonitor/data
ProtectHome=read-only
PrivateNetwork=false

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ipmonitor.service

# Start the service immediately
sudo systemctl start ipmonitor.service

# Verify service is running
sudo systemctl status ipmonitor.service
```

---

## 📈 Service Management Commands

### Essential Commands

| Action | Command | Description |
|--------|---------|-------------|
| **Check Status** | `sudo systemctl status ipmonitor.service` | View service status and recent logs |
| **View Live Logs** | `sudo journalctl -u ipmonitor.service -f` | Stream real-time logs |
| **View Recent Logs** | `sudo journalctl -u ipmonitor.service -n 100` | Show last 100 log entries |
| **Restart Service** | `sudo systemctl restart ipmonitor.service` | Restart the service |
| **Stop Service** | `sudo systemctl stop ipmonitor.service` | Stop the service |
| **Start Service** | `sudo systemctl start ipmonitor.service` | Start the service |
| **Disable Auto-Start** | `sudo systemctl disable ipmonitor.service` | Prevent automatic startup |
| **Enable Auto-Start** | `sudo systemctl enable ipmonitor.service` | Enable automatic startup |

### Advanced Logging

```bash
# View logs from today
sudo journalctl -u ipmonitor.service --since today

# View logs from last hour
sudo journalctl -u ipmonitor.service --since "1 hour ago"

# View logs with specific priority
sudo journalctl -u ipmonitor.service -p err

# Export logs to file
sudo journalctl -u ipmonitor.service > /tmp/ipmonitor-logs.txt
```

---

## 🌐 Access the Dashboard

### Local Access

Once the service is running, access the web dashboard:

**URL:** `http://localhost:8000`

### Remote Access

Access from other devices on your network:

**URL:** `http://your-server-ip:8000`

Replace `your-server-ip` with your server's IP address.

### Find Your Server IP

```bash
# Display all network interfaces
ip addr show

# Or use hostname command
hostname -I
```

### Test Dashboard Accessibility

```bash
# Test local access
curl -I http://localhost:8000

# Test remote access (from another machine)
curl -I http://YOUR_SERVER_IP:8000
```

### Firewall Configuration

If you can't access the dashboard remotely, configure your firewall:

```bash
# Allow port 8000 through UFW firewall
sudo ufw allow 8000/tcp

# Check firewall status
sudo ufw status

# Enable firewall if not already enabled
sudo ufw enable
```

---

## 📁 Directory Structure

Understanding the project layout:

```
ipmonitor/                            # Root project directory
├── 📄 README.md                      # Documentation (this file)
├── 📄 LICENSE                        # MIT License
├── 📄 main.py                        # Main application entry point
├── 📄 monitor.py                     # Standalone monitor script
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # Environment variables template
├── 📁 data/                          # Data storage directory (auto-created)
│   ├── 📄 config.json                # Application configuration
│   ├── 📄 hosts.json                 # Host definitions and settings
│   ├── 📄 states.json                # Current monitoring states
│   ├── 📄 groups.json                # Device grouping information
│   └── 📁 logs/                      # Log files directory
│       └── 📄 monitor.log            # Application logs with rotation
│
├── 📁 app/                           # Main application package
    ├── 📄 __init__.py                # Package initialization
    ├── 📄 config.py                  # Configuration management
    ├── 📄 models.py                  # Pydantic data models
    │
    ├── 📁 monitor/                   # Core monitoring logic
    │   ├── 📄 __init__.py
    │   ├── 📄 ping_service.py        # ICMP ping operations
    │   ├── 📄 state_manager.py       # State persistence and management
    │   └── 📄 notification_service.py # Alert notifications (Discord)
    │
    ├── 📁 api/                       # Web API layer
    │   ├── 📄 __init__.py
    │   ├── 📄 routes.py              # REST API endpoints
    │   └── 📄 websocket.py           # WebSocket real-time handlers
    │
    ├── 📁 utils/                     # Utility modules
    │   ├── 📄 __init__.py
    │   └── 📄 network_scanner.py     # Subnet scanning utilities
    │
    └── 📁 static/                    # Web dashboard static files
        ├── 📄 index.html             # Dashboard user interface
        ├── 📄 icon.ico               # Favicon
```

---

## 🔍 Monitoring & Troubleshooting

### System Resource Checks

Monitor system resources to ensure optimal performance:

```bash
# Check disk space usage
df -h /home/ipmonitor

# Check memory usage
free -h

# Check CPU usage
top -bn1 | grep "Cpu(s)"

# Check process status
ps aux | grep ipmonitor

# Check network connections
netstat -tlnp | grep 8000
```

### Service Diagnostics

```bash
# Check if virtual environment exists
ls -la /home/ipmonitor/ipmonitor/venv/

# Verify Python dependencies
/home/ipmonitor/ipmonitor/venv/bin/python -c "import flask; print('Flask version:', flask.__version__)"

# Check file permissions
ls -la /home/ipmonitor/ipmonitor/data/

# Verify ping capabilities
getcap /bin/ping
getcap /usr/bin/ping
```

### Application Logs

```bash
# View application logs
tail -f /home/ipmonitor/ipmonitor/data/logs/monitor.log

# View systemd service logs
sudo journalctl -u ipmonitor.service -f

# Search for errors in logs
sudo journalctl -u ipmonitor.service | grep -i error

# View logs with timestamps
sudo journalctl -u ipmonitor.service -o short-precise
```

---

## 🔧 Log Rotation Setup

Prevent log files from consuming excessive disk space:

### Create Log Rotation Configuration

```bash
sudo nano /etc/logrotate.d/ipmonitor
```

### Logrotate Configuration

```bash
/home/ipmonitor/ipmonitor/data/logs/monitor.log {
    daily                              # Rotate logs daily
    rotate 30                          # Keep 30 days of logs
    compress                           # Compress old logs
    delaycompress                      # Compress after 2nd rotation
    missingok                          # Don't error if log missing
    notifempty                         # Don't rotate empty logs
    create 640 ipmonitor ipmonitor     # Create new log with permissions
    sharedscripts
    copytruncate                       # Truncate original file
    dateext                            # Add date extension
    dateformat .%Y-%m-%d               # Date format: .2024-01-27
    su ipmonitor ipmonitor             # Run as ipmonitor user
    
    postrotate
        # Signal application to reopen log files
        pkill -USR1 -f "python.*main.py" 2>/dev/null || true
    endscript
}
```

### Test Log Rotation

```bash
# Test configuration (dry run)
sudo logrotate -d /etc/logrotate.d/ipmonitor

# Force rotation (for testing)
sudo logrotate -vf /etc/logrotate.d/ipmonitor

# Verify rotation worked
ls -la /home/ipmonitor/ipmonitor/data/logs/

# Check log file permissions
stat /home/ipmonitor/ipmonitor/data/logs/monitor.log
```

---

## 🔒 Security Best Practices

### Built-in Security Features

- ✅ **Dedicated User Account** - Service runs as `ipmonitor` user (not root)
- ✅ **Limited System Capabilities** - Only `CAP_NET_RAW` for ping operations
- ✅ **Filesystem Protection** - Read-only system files with `ProtectSystem=full`
- ✅ **Home Directory Protection** - `ProtectHome=read-only`
- ✅ **Privilege Escalation Prevention** - `NoNewPrivileges=true`
- ✅ **Private Temporary Files** - Isolated `/tmp` with `PrivateTmp=true`
- ✅ **Restricted Write Access** - Only `/home/ipmonitor/ipmonitor/data` is writable

### Additional Security Recommendations

1. **Firewall Configuration**
   ```bash
   # Only allow local access
   sudo ufw deny 8000/tcp
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   ```

2. **Secure Password Management**
   - Use strong passwords for the `ipmonitor` user
   - Consider SSH key-based authentication
   - Disable password authentication for SSH

3. **Regular Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Python dependencies
   source /home/ipmonitor/ipmonitor/venv/bin/activate
   pip3 install --upgrade -r requirements.txt
   ```

4. **Monitor Access Logs**
   ```bash
   # Check who's accessing the dashboard
   sudo journalctl -u ipmonitor.service | grep "GET /"
   ```

5. **Enable HTTPS** (Recommended for production)
   - Use a reverse proxy (Nginx or Apache)
   - Configure SSL/TLS certificates
   - Use Let's Encrypt for free certificates

---

## 🆘 Common Issues & Solutions

### Issue: Ping Permission Denied

**Symptoms:** Service fails with "Operation not permitted" errors

**Solution:**
```bash
# Set ping capabilities
sudo setcap cap_net_raw+ep /bin/ping
sudo setcap cap_net_raw+ep /usr/bin/ping

# Verify capabilities
getcap /bin/ping
getcap /usr/bin/ping

# Restart service
sudo systemctl restart ipmonitor.service
```

### Issue: Service Won't Start

**Symptoms:** `systemctl status` shows failed state

**Solution:**
```bash
# Check detailed logs
sudo journalctl -u ipmonitor.service -n 50 --no-pager

# Verify Python environment
/home/ipmonitor/ipmonitor/venv/bin/python --version

# Check file permissions
ls -la /home/ipmonitor/ipmonitor/

# Verify dependencies
cd /home/ipmonitor/ipmonitor
source venv/bin/activate
pip list
```

### Issue: Dashboard Not Accessible

**Symptoms:** Cannot connect to `http://server-ip:8000`

**Solution:**
```bash
# Check if service is running
sudo systemctl status ipmonitor.service

# Check if port is listening
sudo netstat -tlnp | grep 8000

# Check firewall rules
sudo ufw status verbose

# Allow port through firewall
sudo ufw allow 8000/tcp

# Test local connectivity
curl -I http://localhost:8000
```

### Issue: Python Import Errors

**Symptoms:** "ModuleNotFoundError" or import-related errors

**Solution:**
```bash
# Reinstall dependencies
cd /home/ipmonitor/ipmonitor
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Verify installations
pip list | grep -i flask
pip list | grep -i pydantic

# Restart service
sudo systemctl restart ipmonitor.service
```

### Issue: Port 8000 Already in Use

**Symptoms:** "Address already in use" error

**Solution:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process (replace PID)
sudo kill -9 <PID>

# Or change port in configuration
nano /home/ipmonitor/ipmonitor/.env
# Change PORT=8000 to PORT=8001

# Restart service
sudo systemctl restart ipmonitor.service
```

### Issue: High Memory Usage

**Symptoms:** System running slow, out of memory errors

**Solution:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Reduce monitoring frequency in .env
nano /home/ipmonitor/ipmonitor/.env
# Increase PING_INTERVAL value

# Restart service
sudo systemctl restart ipmonitor.service

# Consider log rotation
sudo logrotate -f /etc/logrotate.d/ipmonitor
```

---

## 🎯 Usage Guide

### Adding Devices to Monitor

1. **Access the Dashboard** at `http://your-server-ip:8000`
2. Click **"Add Device"** button
3. Enter device details:
   - **Name:** Friendly device name (e.g., "Main Router")
   - **IP Address:** Device IP (e.g., "192.168.1.1")
   - **Interval:** Ping frequency in seconds (default: 60)
   - **Group:** Optional group name for organization

### Organizing Devices with Groups

Create logical groups to organize devices:
- **Critical Infrastructure** - Core routers, switches
- **Servers** - Application and database servers
- **Workstations** - Desktop computers
- **IoT Devices** - Smart home devices
- **Network Equipment** - Switches, access points

### Using the Network Scanner

Discover devices on your network automatically:

1. Click **"Scan Network"** in the dashboard
2. Enter subnet range (e.g., `192.168.1.0/24`)
3. Select discovered devices to add
4. Assign names and groups

### Setting Up Discord Notifications

1. Create a Discord webhook:
   - Open Discord server settings
   - Go to Integrations → Webhooks
   - Create webhook and copy URL

2. Configure in `.env` file:
   ```bash
   nano /home/ipmonitor/ipmonitor/.env
   ```
   
3. Add webhook URL:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
   ```

4. Restart service:
   ```bash
   sudo systemctl restart ipmonitor.service
   ```

### API Usage

Access programmatically via REST API:

```bash
# Get all monitored devices
curl http://localhost:8000/api/hosts

# Get specific device status
curl http://localhost:8000/api/hosts/192.168.1.1

# Add new device
curl -X POST http://localhost:8000/api/hosts \
  -H "Content-Type: application/json" \
  -d '{"name":"New Device","ip":"192.168.1.100","interval":60}'

# Delete device
curl -X DELETE http://localhost:8000/api/hosts/192.168.1.100
```

---

## 🚀 Advanced Configuration

### Custom Ping Intervals

Set different ping frequencies for different devices:

- **Critical devices:** 30 seconds (fast detection)
- **Standard devices:** 60 seconds (balanced)
- **Low-priority devices:** 300 seconds (reduced overhead)

### Performance Tuning

For monitoring 100+ devices:

```bash
# Edit .env file
nano /home/ipmonitor/ipmonitor/.env
```

```
# Increase worker threads
WORKERS=4

# Adjust concurrent ping limit
MAX_CONCURRENT_PINGS=50

# Set timeout values
PING_TIMEOUT=3
```

### Database Backup

Backup your monitoring data:

```bash
# Create backup script
cat > /home/ipmonitor/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ipmonitor/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/ipmonitor_$DATE.tar.gz /home/ipmonitor/ipmonitor/data/
find $BACKUP_DIR -name "ipmonitor_*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/ipmonitor/backup.sh

# Schedule with cron
crontab -e
# Add: 0 2 * * * /home/ipmonitor/backup.sh
```

---

## 🤝 Contributing

I welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs** - Open issues for bugs you find
- 💡 **Suggest Features** - Share ideas for improvements
- 📝 **Improve Documentation** - Help make docs clearer
- 🔧 **Submit Code** - Fix bugs or add features
- ⭐ **Star the Project** - Show your support

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/ipmonitor.git
cd ipmonitor

# Create development branch
git checkout -b feature/your-feature-name

# Install development dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Make your changes and test
python main.py

# Run tests (if available)
pytest

# Commit changes
git add .
git commit -m "Add: your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request with detailed description

### Code Style

- Follow PEP 8 guidelines for Python code
- Add docstrings to functions and classes
- Include type hints where appropriate
- Write meaningful commit messages

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for full details.

### MIT License Summary

✅ **Commercial use** - Use in commercial projects  
✅ **Modification** - Modify the source code  
✅ **Distribution** - Distribute copies  
✅ **Private use** - Use privately  
⚠️ **Liability** - No warranty provided  
⚠️ **Attribution** - Must include copyright notice

---

## 💬 Support & Community

### Get Help

- 📖 **Documentation:** Read this README thoroughly
- 🐛 **Bug Reports:** [Open an issue](https://github.com/NNLixon/ipmonitor/issues/new?template=bug_report.md)
- 💡 **Feature Requests:** [Suggest a feature](https://github.com/NNLixon/ipmonitor/issues/new?template=feature_request.md)
- 💬 **Discussions:** [Join discussions](https://github.com/NNLixon/ipmonitor/discussions)
- ⭐ **Star the Project:** Show your support by starring the repository

### Project Links

- 🏠 **Homepage:** [https://github.com/NNLixon/ipmonitor](https://github.com/NNLixon/ipmonitor)
- 📚 **Documentation:** [Wiki](https://github.com/NNLixon/ipmonitor/wiki)
- 🐛 **Issue Tracker:** [GitHub Issues](https://github.com/NNLixon/ipmonitor/issues)
- 📝 **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- 🔒 **Security:** [SECURITY.md](SECURITY.md)

### Maintainer

**NNLixon**  
GitHub: [@NNLixon](https://github.com/NNLixon)

---

## 🏆 Acknowledgments

Special thanks to:
- All contributors who help improve this project
- The Python community for excellent libraries
- Ubuntu/Debian teams for the robust platform
- Everyone who stars and shares this project

---

## 📊 Project Stats

![GitHub repo size](https://img.shields.io/github/repo-size/NNLixon/ipmonitor)
![GitHub code size](https://img.shields.io/github/languages/code-size/NNLixon/ipmonitor)
![GitHub issues](https://img.shields.io/github/issues/NNLixon/ipmonitor)
![GitHub pull requests](https://img.shields.io/github/issues-pr/NNLixon/ipmonitor)
![GitHub last commit](https://img.shields.io/github/last-commit/NNLixon/ipmonitor)
![GitHub contributors](https://img.shields.io/github/contributors/NNLixon/ipmonitor)

---

## 🔑 Keywords

`network-monitoring` `ip-monitor` `ping-monitor` `uptime-monitoring` `server-monitoring` `network-tools` `devops` `sysadmin` `python` `flask` `websocket` `systemd` `ubuntu` `linux` `iot-monitoring` `infrastructure-monitoring` `real-time-monitoring` `dashboard` `open-source` `self-hosted`

---

<div align="center">

**[⬆ Back to Top](#-ip-monitor-dashboard---real-time-network-device-monitoring-tool)**

Made with ❤️ by [NNLixon](https://github.com/NNLixon)

If this project helped you, please consider giving it a ⭐!

</div>
