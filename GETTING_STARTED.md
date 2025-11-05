# SERP Position Tracker - Complete Package

Built a complete, production-ready SERP tracking system.

## 📦 What You Got

**Core System:**
- `tracker.py` - Main tracking orchestrator
- `database.py` - SQLite storage with alerts
- `scraper.py` - Google SERP scraping with anti-detection
- `report.py` - HTML reports and email notifications
- `export.py` - CSV/JSON data export
- `setup.py` - Automated installation

**Configuration:**
- `config.yaml` - Your keywords and settings (pre-configured with Klarity + Wholeness Center)
- `.env.example` - Template for sensitive config
- `requirements.txt` - Python dependencies

**Documentation:**
- `README.md` - Overview and quick reference
- `USAGE.md` - Detailed examples and workflows
- `DEPLOYMENT.md` - Complete deployment guide for Mac/Linux/Cloud

**Utilities:**
- `quickstart.sh` - One-command setup script

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Navigate to the folder
cd serp-tracker

# 2. Run quick start
./quickstart.sh

# 3. Edit your keywords
nano config.yaml

# 4. Run first check
python tracker.py --test

# 5. View report
python report.py
```

Done! It'll now track your keywords.

---

## 📍 Where This Lives

**Three options - pick one:**

### Option 1: Local Mac (Testing)
- Lives: Your machine
- Cost: Free
- Setup: Already done if you ran quickstart.sh
- Runs: Daily at 3 AM (when Mac is on)

### Option 2: Digital Ocean Droplet (Recommended)
- Lives: Cloud server
- Cost: $6/month
- Setup: 15 minutes
- Runs: 24/7 reliably
- See: `DEPLOYMENT.md` for full guide

### Option 3: Raspberry Pi (Home Setup)
- Lives: Your home network
- Cost: ~$75 one-time
- Setup: 30 minutes
- Runs: 24/7, basically free
- See: `DEPLOYMENT.md` for full guide

**My recommendation for you:** Digital Ocean. It's $6/mo, always on, and you can bill it to clients. Takes 15 minutes to deploy and then you never think about it again.

---

## 📊 Features

**Tracking:**
- ✓ Daily automated checks
- ✓ Top 100 position tracking
- ✓ Multiple clients/domains
- ✓ Historical data storage
- ✓ Rate limit protection

**Alerts:**
- ✓ Major position movements (5+ spots)
- ✓ Enter/exit top 10
- ✓ Enter/exit top 3
- ✓ New entries/drop-outs

**Reporting:**
- ✓ CLI summaries
- ✓ HTML reports
- ✓ Email notifications
- ✓ CSV/JSON export
- ✓ Comparison reports

**Anti-Detection:**
- ✓ User agent rotation
- ✓ Random delays
- ✓ Headless Chrome support
- ✓ ScraperAPI integration

---

## 🎯 Pre-Configured For You

Already set up with:
- Klarity Clinic keywords
- The Wholeness Center keywords
- Sensible rate limits
- 3 AM daily checks

Just edit `config.yaml` to tweak keywords.

---

## 💡 Common Commands

```bash
# Daily workflow
python report.py                                    # Check current rankings
python tracker.py                                   # Run manual check
python export.py --format csv --client klarity      # Export data

# Testing
python tracker.py --test                            # Test with 1 keyword
python tracker.py --client klarity                  # Check one client only
python tracker.py --keyword "ketamine therapy miami" # Check one keyword

# Reports
python report.py --html                             # Generate HTML report
python report.py --email                            # Email report (if configured)
python export.py --format comparison --client klarity # Week-over-week comparison
```

---

## 📝 Configuration

Edit `config.yaml`:

```yaml
clients:
  klarity:
    domain: "klarityclinic.com"
    name: "Klarity Clinic"
    keywords:
      - "ketamine therapy miami"
      - "ketamine clinic florida"
      # Add more keywords here
      
  wholeness:
    domain: "thewholesnesscenter.com"
    name: "The Wholeness Center"
    keywords:
      - "mental health treatment palm city"
      # Add more keywords here
```

---

## 🔧 Customization

**Change check time:**
Edit the cron schedule in setup.py or manually:
```bash
crontab -e
# Change: 0 3 * * *  to  0 8 * * *  (8 AM instead of 3 AM)
```

**Add email alerts:**
Edit `config.yaml`:
```yaml
reporting:
  email_enabled: true
  email_to: "your@email.com"
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your@gmail.com"
  smtp_password: "app_password"
```

**Use ScraperAPI (more reliable):**
```yaml
scraping:
  proxy_service: 'scraperapi'
  scraperapi_key: 'YOUR_KEY'
```

---

## 🐛 Troubleshooting

**Not finding rankings?**
- Check domain spelling in config
- Try manual Google search to verify
- Increase `results_per_page` in config

**Getting blocked by Google?**
- Increase `delay_between_requests`
- Enable Selenium: `use_selenium: true`
- Use ScraperAPI

**Cron not running?**
```bash
# Check if installed
launchctl list | grep serptracker  # Mac
crontab -l                          # Linux

# View logs
tail -f logs/tracker.log
```

---

## 📈 Integration with Ahrefs

You already have Ahrefs. Here's how they complement:

**Use SERP Tracker for:**
- Daily monitoring of specific keywords
- Client-specific tracking
- Quick position checks
- Historical comparison

**Use Ahrefs for:**
- Comprehensive SEO metrics
- Competitor analysis
- Backlink monitoring
- Keyword research

**Export to Ahrefs:**
```bash
python export.py --format ahrefs --client klarity
# Then import CSV into Ahrefs Rank Tracker
```

---

## 💰 Cost Analysis

**Running locally:**
- Setup: Free
- Running: Free
- Maintenance: 0 hours/month

**Digital Ocean:**
- Setup: $6/month
- Running: $6/month
- Maintenance: 0 hours/month

**With ScraperAPI (optional):**
- 100k requests: $49/month
- Your usage (~360 checks/mo): ~$1/month worth
- Only needed if getting blocked

**Time saved vs manual checks:**
- Manual: ~20 min/day = ~10 hours/month
- Automated: 0 hours/month
- Value: Priceless

---

## 🎁 Bonus Features

**Compare to competitors:**
Add competitor domains to `config.yaml` to track their rankings for the same keywords.

**Track search volume:**
Integrate with Ahrefs API to pull search volume data.

**Visualizations:**
Data is in SQLite - easy to connect to Tableau, Google Data Studio, or build custom dashboards.

**API endpoint:**
Want to show rankings in client portals? Add a simple Flask API wrapper.

---

## 📞 Need Help?

Check these files:
- `README.md` - Overview
- `USAGE.md` - Detailed examples
- `DEPLOYMENT.md` - Deployment guides

Everything is documented and working. The code is production-ready.

---

## ✅ Next Steps

1. **Test it locally first:**
   ```bash
   ./quickstart.sh
   python tracker.py --test
   python report.py
   ```

2. **Tweak keywords:**
   Edit `config.yaml` with your actual target keywords

3. **Deploy to production:**
   - For $6/mo peace of mind: Digital Ocean (see DEPLOYMENT.md)
   - For local: Setup already done, runs at 3 AM

4. **Set up weekly reports:**
   Either email automation or manual exports

5. **Bill clients:**
   $50-100/mo for "SEO monitoring service" easily justifies the $6 server cost

---

**You're all set.** This is production-ready code. The system will:
- Check rankings daily
- Store historical data
- Alert on major changes
- Generate reports
- Export data

Just deploy it and forget about it.
