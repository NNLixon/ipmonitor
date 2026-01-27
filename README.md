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
<button onclick="navigator.clipboard.writeText('sudo apt update && sudo apt upgrade -y')">📋 Copy</button>

```bash
sudo apt install -y nmap python3 python3-pip python3-venv git curl wget build-essential
```
<button onclick="navigator.clipboard.writeText('sudo apt install -y nmap python3 python3-pip python3-venv git curl wget build-essential')">📋 Copy</button>

### Step 2: Create Dedicated User
```bash
sudo useradd -m -s /bin/bash ipmonitor
```
<button onclick="navigator.clipboard.writeText('sudo useradd -m -s /bin/bash ipmonitor')">📋 Copy</button>

```bash
sudo usermod -aG sudo ipmonitor
```
<button onclick="navigator.clipboard.writeText('sudo usermod -aG sudo ipmonitor')">📋 Copy</button>

```bash
sudo passwd ipmonitor
```
<button onclick="navigator.clipboard.writeText('sudo passwd ipmonitor')">📋 Copy</button>
*Set a secure password when prompted*

### Step 3: Switch to ipmonitor User
```bash
sudo -u ipmonitor -i
```
<button onclick="navigator.clipboard.writeText('sudo -u ipmonitor -i')">📋 Copy</button>

### Step 4: Configure Ping Permissions
```bash
sudo setcap cap_net_raw+ep /bin/ping 2>/dev/null || true
```
<button onclick="navigator.clipboard.writeText('sudo setcap cap_net_raw+ep /bin/ping 2>/dev/null || true')">📋 Copy</button>

```bash
sudo setcap cap_net_raw+ep /usr/bin/ping 2>/dev/null || true
```
<button onclick="navigator.clipboard.writeText('sudo setcap cap_net_raw+ep /usr/bin/ping 2>/dev/null || true')">📋 Copy</button>

### Step 5: Clone Repository & Setup
```bash
cd /home/ipmonitor && git clone https://github.com/NNLixon/ipmonitor.git
```
<button onclick="navigator.clipboard.writeText('cd /home/ipmonitor && git clone https://github.com/NNLixon/ipmonitor.git')">📋 Copy</button>

```bash
cd ipmonitor && python3 -m venv venv
```
<button onclick="navigator.clipboard.writeText('cd ipmonitor && python3 -m venv venv')">📋 Copy</button>

```bash
source venv/bin/activate
```
<button onclick="navigator.clipboard.writeText('source venv/bin/activate')">📋 Copy</button>

```bash
pip3 install --upgrade pip && pip3 install -r requirements.txt
```
<button onclick="navigator.clipboard.writeText('pip3 install --upgrade pip && pip3 install -r requirements.txt')">📋 Copy</button>

## 🔧 Systemd Service Setup

### Create Service File
```bash
sudo nano /etc/systemd/system/ipmonitor.service
```
<button onclick="navigator.clipboard.writeText('sudo nano /etc/systemd/system/ipmonitor.service')">📋 Copy</button>

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
<button onclick="navigator.clipboard.writeText('sudo systemctl daemon-reload')">📋 Copy</button>

```bash
sudo systemctl enable ipmonitor.service
```
<button onclick="navigator.clipboard.writeText('sudo systemctl enable ipmonitor.service')">📋 Copy</button>

```bash
sudo systemctl start ipmonitor.service
```
<button onclick="navigator.clipboard.writeText('sudo systemctl start ipmonitor.service')">📋 Copy</button>

## 📈 Service Management Commands

| Action | Command | Copy |
|--------|---------|------|
| Check Status | `sudo systemctl status ipmonitor.service` | <button onclick="navigator.clipboard.writeText('sudo systemctl status ipmonitor.service')">📋</button> |
| View Logs | `sudo journalctl -u ipmonitor.service -f` | <button onclick="navigator.clipboard.writeText('sudo journalctl -u ipmonitor.service -f')">📋</button> |
| Restart Service | `sudo systemctl restart ipmonitor.service` | <button onclick="navigator.clipboard.writeText('sudo systemctl restart ipmonitor.service')">📋</button> |
| Stop Service | `sudo systemctl stop ipmonitor.service` | <button onclick="navigator.clipboard.writeText('sudo systemctl stop ipmonitor.service')">📋</button> |
| Reload Service | `sudo systemctl reload ipmonitor.service` | <button onclick="navigator.clipboard.writeText('sudo systemctl reload ipmonitor.service')">📋</button> |

## 🌐 Access the Dashboard

Once running, access the dashboard at:

**URL:** [http://your-server-ip:8000](http://localhost:8000)

Test accessibility:
```bash
curl -I http://localhost:8000
```
<button onclick="navigator.clipboard.writeText('curl -I http://localhost:8000')">📋 Copy</button>

## 🔍 Monitoring & Troubleshooting

### Check System Resources
```bash
# Disk space
df -h /home/ipmonitor
```
<button onclick="navigator.clipboard.writeText('df -h /home/ipmonitor')">📋 Copy</button>

```bash
# Memory usage
free -h
```
<button onclick="navigator.clipboard.writeText('free -h')">📋 Copy</button>

```bash
# Process status
ps aux | grep ipmonitor
```
<button onclick="navigator.clipboard.writeText('ps aux | grep ipmonitor')">📋 Copy</button>

### Verify Service Components
```bash
# Check if virtual environment exists
ls -la /home/ipmonitor/ipmonitor/venv/
```
<button onclick="navigator.clipboard.writeText('ls -la /home/ipmonitor/ipmonitor/venv/')">📋 Copy</button>

```bash
# Check requirements installation
/home/ipmonitor/ipmonitor/venv/bin/python -c "import flask; print('Flask version:', flask.__version__)"
```
<button onclick="navigator.clipboard.writeText('/home/ipmonitor/ipmonitor/venv/bin/python -c \"import flask; print(\'Flask version:\', flask.__version__)\"')">📋 Copy</button>

## 📁 Directory Structure
```
/home/ipmonitor/
└── ipmonitor/
    ├── venv/                    # Python virtual environment
    ├── data/                    # Application data and logs
    ├── main.py                  # Main application file
    ├── requirements.txt         # Python dependencies
    └── README.md                # This file
```

## 🔐 Security Notes

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

## ⭐ Support

If you find this project helpful, please give it a star! ⭐

---

**Maintained by:** [NNLixon](https://github.com/NNLixon)  
**Report Issues:** [GitHub Issues](https://github.com/NNLixon/ipmonitor/issues)

<script>
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    // Optional: Show a small notification
    const buttons = document.querySelectorAll('button');
    buttons.forEach(btn => {
      if (btn.textContent.includes('📋')) {
        btn.addEventListener('click', function() {
          const originalText = this.textContent;
          this.textContent = '✅ Copied!';
          setTimeout(() => {
            this.textContent = originalText;
          }, 2000);
        });
      }
    });
  });
}

// Add event listeners to all copy buttons
document.addEventListener('DOMContentLoaded', function() {
  const buttons = document.querySelectorAll('button');
  buttons.forEach(button => {
    button.addEventListener('click', function() {
      const originalText = this.textContent;
      this.textContent = '✅ Copied!';
      setTimeout(() => {
        this.textContent = originalText;
      }, 2000);
    });
  });
});
</script>
