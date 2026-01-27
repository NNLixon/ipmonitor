## 24.04.3 LTS Server (Noble Numbat)

## Update OS & Install necesary dependencies 
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget nmap build-essential

## Create New User for ipmonitor service
```bash
sudo useradd -m -s /bin/bash ipmonitor
sudo usermod -aG sudo ipmonitor
sudo passwd ipmonitor

## Switch to ipmonitor user
```bash
sudo -u ipmonitor -i
cd /home/ipmonitor
