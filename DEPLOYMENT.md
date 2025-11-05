# Deployment Guide

Three deployment options for running SERP tracker 24/7.

## Option 1: Local Mac (Easiest)

**Cost:** $0 (uses your existing machine)  
**Uptime:** When your Mac is on  
**Best for:** Testing, personal use

### Setup

```bash
cd serp-tracker
python setup.py
```

This installs a launchd agent that runs daily at 3 AM.

**Files created:**
- `~/Library/LaunchAgents/com.serptracker.daily.plist`

**Manual control:**
```bash
# Check status
launchctl list | grep serptracker

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.serptracker.daily.plist

# Load (start)
launchctl load ~/Library/LaunchAgents/com.serptracker.daily.plist

# Run now (for testing)
python tracker.py
```

**Logs:**
- `logs/tracker.log`
- `logs/tracker.error.log`

---

## Option 2: Digital Ocean Droplet (Recommended)

**Cost:** $6/month  
**Uptime:** 24/7  
**Best for:** Production use, client work

### Initial Setup

1. **Create Droplet**
   - Go to digitalocean.com
   - Create → Droplets
   - Choose: Ubuntu 24.04 LTS
   - Plan: Basic ($6/mo)
   - Region: Closest to you
   - Authentication: SSH key (recommended)

2. **Connect to server**
```bash
ssh root@YOUR_DROPLET_IP
```

3. **Install dependencies**
```bash
# Update system
apt update && apt upgrade -y

# Install Python 3 and pip
apt install python3 python3-pip python3-venv git -y

# Install Chrome for Selenium (if using)
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt update
apt install google-chrome-stable -y
```

4. **Setup project**
```bash
# Create directory
mkdir -p /opt/serp-tracker
cd /opt/serp-tracker

# Clone or copy your files
# Option A: If using git
git clone YOUR_REPO_URL .

# Option B: Copy from local machine
# On your local machine:
scp -r ~/path/to/serp-tracker root@YOUR_DROPLET_IP:/opt/

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configure**
```bash
# Edit config with your keywords
nano config.yaml

# Test run
python tracker.py --test
```

6. **Setup cron**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 3 AM UTC):
0 3 * * * cd /opt/serp-tracker && /opt/serp-tracker/venv/bin/python tracker.py >> logs/tracker.log 2>&1
```

7. **Optional: Setup systemd (alternative to cron)**
```bash
# Create service file
cat > /etc/systemd/system/serptracker.service <<EOF
[Unit]
Description=SERP Position Tracker
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/serp-tracker
ExecStart=/opt/serp-tracker/venv/bin/python /opt/serp-tracker/tracker.py
StandardOutput=append:/opt/serp-tracker/logs/tracker.log
StandardError=append:/opt/serp-tracker/logs/tracker.error.log

[Install]
WantedBy=multi-user.target
EOF

# Create timer file
cat > /etc/systemd/system/serptracker.timer <<EOF
[Unit]
Description=Run SERP tracker daily at 3 AM

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
systemctl enable serptracker.timer
systemctl start serptracker.timer

# Check status
systemctl status serptracker.timer
```

### Monitoring

```bash
# View logs
tail -f /opt/serp-tracker/logs/tracker.log

# Check last run
systemctl list-timers serptracker

# Manual run
cd /opt/serp-tracker && source venv/bin/activate && python tracker.py
```

### Accessing Reports

**Option A: Download via SCP**
```bash
# From your local machine
scp root@YOUR_DROPLET_IP:/opt/serp-tracker/reports/*.html ./
```

**Option B: Setup simple web server**
```bash
# On droplet
apt install nginx -y

# Create symlink
ln -s /opt/serp-tracker/reports /var/www/html/reports

# Access via: http://YOUR_DROPLET_IP/reports/
```

**Option C: Email reports**
Edit `config.yaml`:
```yaml
reporting:
  email_enabled: true
  email_to: "your@email.com"
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your@gmail.com"
  smtp_password: "your_app_password"
```

---

## Option 3: Raspberry Pi (One-time cost)

**Cost:** ~$75 one-time (Pi 4 kit)  
**Uptime:** 24/7  
**Power:** ~$5/year electricity  
**Best for:** Set and forget

### Hardware Needed
- Raspberry Pi 4 (2GB+ RAM)
- MicroSD card (32GB+)
- Power supply
- Case (optional)

### Setup

1. **Install Raspberry Pi OS**
   - Use Raspberry Pi Imager
   - Choose "Raspberry Pi OS Lite (64-bit)"
   - Configure WiFi and SSH in imager

2. **Connect and update**
```bash
ssh pi@raspberrypi.local
sudo apt update && sudo apt upgrade -y
```

3. **Install dependencies**
```bash
sudo apt install python3 python3-pip python3-venv git -y

# Optional: Install Chrome (for Selenium)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
```

4. **Setup project**
```bash
mkdir ~/serp-tracker
cd ~/serp-tracker

# Copy files or clone repo
# Then:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configure and test**
```bash
nano config.yaml
python tracker.py --test
```

6. **Setup cron**
```bash
crontab -e

# Add:
0 3 * * * cd /home/pi/serp-tracker && /home/pi/serp-tracker/venv/bin/python tracker.py >> logs/tracker.log 2>&1
```

7. **Access reports**

Setup Samba for easy file access from your Mac:
```bash
sudo apt install samba -y

sudo nano /etc/samba/smb.conf
# Add at end:
[tracker]
path = /home/pi/serp-tracker/reports
writeable = yes
guest ok = yes
force user = pi

sudo systemctl restart smbd

# Access from Mac: smb://raspberrypi.local/tracker
```

---

## Option 4: AWS Lambda (Advanced)

For high-scale or want completely serverless, but complex setup.

**Cost:** Basically free (<$1/mo)  
**Complexity:** High  
**Best for:** Multiple clients, enterprise

Not recommended unless you need scale - Droplet is simpler.

---

## Comparison Table

| Option | Cost | Setup Time | Uptime | Best For |
|--------|------|------------|--------|----------|
| Local Mac | Free | 5 min | When Mac on | Testing |
| Digital Ocean | $6/mo | 15 min | 24/7 | Production |
| Raspberry Pi | $75 once | 30 min | 24/7 | Home setup |
| AWS Lambda | <$1/mo | 2+ hours | 24/7 | Enterprise |

---

## Recommended: Digital Ocean

For your use case (2 clients, professional work), I'd go with Digital Ocean:

1. **Always on** - clients expect reliability
2. **Remote access** - check from anywhere
3. **Easy scaling** - add more clients anytime
4. **Professional** - not dependent on your personal machine
5. **Cheap** - $6/mo is billable to clients

Setup takes 15 minutes, then forget about it.

---

## Quick Start (Digital Ocean)

```bash
# 1. Create droplet at digitalocean.com

# 2. SSH in
ssh root@YOUR_IP

# 3. One-command setup
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/setup.sh | bash

# 4. Configure
nano /opt/serp-tracker/config.yaml

# 5. Test
cd /opt/serp-tracker && python tracker.py --test

# 6. Done! Runs daily at 3 AM automatically
```

That's it. Check back weekly, export reports monthly.
