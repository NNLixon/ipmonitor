# 🌐 IP Monitor Dashboard

**A lightweight, real-time IP monitoring dashboard** that tracks network device availability using simple ping operations. Built for Ubuntu 24.04.3 LTS (Noble Numbat).

![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📊 Features

- ✅ **Real-time monitoring** of IP addresses/network devices
- ✅ **Web-based dashboard** with intuitive interface
- ✅ **Automated ping checks** with configurable intervals
- ✅ **Systemd service integration** for automatic startup
- ✅ **Logging & alerting** capabilities
- ✅ **Lightweight & resource-efficient**
- ✅ **Secure execution** with dedicated system user

## 🖥️ System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Ubuntu 24.04.3 LTS (Noble Numbat) |
| **RAM** | 512 MB minimum (1 GB recommended) |
| **Storage** | 200 MB free space |
| **Python** | 3.8 or higher |
| **Network** | Internet connectivity for dependencies |

## 🚀 Quick Installation

### Step 1: Update System & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install -y nmap python3 python3-pip python3-venv git curl wget build-essential
```

### Step 2: Create Dedicated User

```bash
sudo useradd -m -s /bin/bash ipmonitor
```

```bash
sudo usermod -aG sudo ipmonitor
```

```bash
sudo passwd ipmonitor
```

> **Note:** Set a secure password when prompted

### Step 3: Switch to ipmonitor User

```bash
sudo -u ipmonitor -i
```

### Step 4: Configure Ping Permissions

```bash
sudo setcap cap_net_raw+ep /bin/ping 2>/dev/null || true
```

```bash
sudo setcap cap_net_raw+ep /usr/bin/ping 2>/dev/null || true
```

### Step 5: Clone Repository & Setup

```bash
cd /home/ipmonitor && git clone https://github.com/NNLixon/ipmonitor.git
```

```bash
cd ipmonitor && cp env.example .env
```

```bash
python3 -m venv venv && source venv/bin/activate
```

```bash
pip3 install --upgrade pip && pip3 install -r requirements.txt
```

## 🔧 Systemd Service Setup

### Create Service File

```bash
sudo nano /etc/systemd/system/ipmonitor.service
```

Copy and paste the following content:

```ini
[Unit]
Description=IP Monitor Dashboard Service
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ipmonitor
Group=ipmonitor
WorkingDirectory=/home/ipmonitor/ipmonitor
Environment="PATH=/home/ipmonitor/ipmonitor/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/home/ipmonitor/ipmonitor"
Environment="HOME=/home/ipmonitor"
Environment="USER=ipmonitor"
Environment="LOGNAME=ipmonitor"
ExecStart=/home/ipmonitor/ipmonitor/venv/bin/python /home/ipmonitor/ipmonitor/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ipmonitor
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

### Enable & Start Service

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable ipmonitor.service
```

```bash
sudo systemctl start ipmonitor.service
```

## 📈 Service Management Commands

| Action | Command |
|--------|---------|
| **Check Status** | `sudo systemctl status ipmonitor.service` |
| **View Logs** | `sudo journalctl -u ipmonitor.service -f` |
| **Restart Service** | `sudo systemctl restart ipmonitor.service` |
| **Stop Service** | `sudo systemctl stop ipmonitor.service` |
| **Reload Service** | `sudo systemctl reload ipmonitor.service` |

## 🌐 Access the Dashboard

Once running, access the dashboard at:

**URL:** http://your-server-ip:8000

Test accessibility:

```bash
curl -I http://localhost:8000
```

## 🔍 Monitoring & Troubleshooting

### Check System Resources

```bash
# Disk space
df -h /home/ipmonitor
```

```bash
# Memory usage
free -h
```

```bash
# Process status
ps aux | grep ipmonitor
```

### Verify Service Components

```bash
# Check if virtual environment exists
ls -la /home/ipmonitor/ipmonitor/venv/
```

```bash
# Check requirements installation
/home/ipmonitor/ipmonitor/venv/bin/python -c "import flask; print('Flask version:', flask.__version__)"
```

## 📁 Directory Structure

```
ipmonitor/                            # Root project directory
├── 📄 README.md                      # Main README documentation
├── 📄 main.py                        # Main application entry point
├── 📄 monitor.py                     # Standalone monitor script
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # Environment variables template
├── 📄 pyproject.toml                 # Python project configuration
│
├── 📁 data/                          # Data storage directory
│   ├── 📄 config.json                # Application configuration
│   ├── 📄 hosts.json                 # Host definitions
│   ├── 📄 states.json                # Host monitoring states
│   ├── 📄 groups.json                # Host groups
│   └── 📁 logs/                      # Log files
│       └── 📄 monitor.log            # Application logs
│
├── 📁 app/                           # Application package
    ├── 📄 __init__.py                # Package initialization
    ├── 📄 config.py                  # Configuration management
    ├── 📄 models.py                  # Pydantic data models
    │
    ├── 📁 monitor/                   # Core monitoring logic
    │   ├── 📄 __init__.py
    │   ├── 📄 ping_service.py        # Ping operations
    │   ├── 📄 state_manager.py       # State persistence
    │   └── 📄 notification_service.py # Discord notifications
    │
    ├── 📁 api/                       # Web API layer
    │   ├── 📄 __init__.py
    │   ├── 📄 routes.py              # REST API endpoints
    │   └── 📄 websocket.py           # WebSocket handlers
    │
    ├── 📁 utils/                     # Utility modules
    │   ├── 📄 __init__.py
    │   └── 📄 network_scanner.py     # Subnet scanning
    │
    └── 📁 static/                    # Web dashboard files
        ├── 📄 index.html             # Dashboard UI
        └── 📄 icon.ico               # Favicon
```

## 🔒 Security Notes

- ✅ **Dedicated user** (`ipmonitor`) for service isolation
- ✅ **Limited capabilities** (only `CAP_NET_RAW` for ping)
- ✅ **Restricted filesystem access** with `ProtectSystem`
- ✅ **No passwordless sudo** - requires manual password setup
- ✅ **Private temporary files** with `PrivateTmp`

## 🆘 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Ping permission denied** | Run: `sudo setcap cap_net_raw+ep /bin/ping` |
| **Service won't start** | Check logs: `sudo journalctl -u ipmonitor -n 50` |
| **Dashboard not accessible** | Verify firewall: `sudo ufw status` |
| **Python import errors** | Reinstall requirements: `pip3 install -r requirements.txt` |
| **Port 8000 in use** | Change port in `main.py` or stop conflicting service |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💬 Support

If you find this project helpful, please give it a star ⭐

**Maintained by:** NNLixon  
**Report Issues:** [GitHub Issues](https://github.com/NNLixon/ipmonitor/issues)
