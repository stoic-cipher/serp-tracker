# Usage Guide

## Daily Workflow

### Check Rankings
```bash
python report.py
```

Output:
```
📊 Klarity Clinic (klarityclinic.com)
────────────────────────────────────────────
Overview:
  Total Keywords: 6
  Ranking: 4
  Top 10: 2
  Top 3: 1
  Average Position: 12.5

🏆 Top 3:
  #2 - ketamine therapy miami

🎯 Top 10 (4-10):
  #8 - ketamine clinic florida

📈 Ranking (11-100):
  #15 - ketamine treatment depression miami
  #23 - miami ketamine clinic

❌ Not Ranking (>100):
  ketamine infusion therapy south florida
  best ketamine therapy florida
```

### Run Manual Check
```bash
# Check all keywords
python tracker.py

# Test mode (first keyword only)
python tracker.py --test

# Specific client
python tracker.py --client klarity

# Single keyword
python tracker.py --keyword "ketamine therapy miami"
```

### Export Data
```bash
# CSV export
python export.py --format csv --client klarity

# Last 90 days
python export.py --format csv --days 90

# Comparison report (week over week)
python export.py --format comparison --client klarity

# For importing to Ahrefs
python export.py --format ahrefs --client wholeness
```

### Generate Reports
```bash
# HTML report
python report.py --html

# Custom output path
python report.py --html --output ~/Desktop/serp_report.html

# Email report (if configured)
python report.py --email
```

---

## Common Tasks

### Adding New Keywords

Edit `config.yaml`:
```yaml
clients:
  klarity:
    keywords:
      - "ketamine therapy miami"
      - "ketamine clinic florida"
      - "NEW KEYWORD HERE"  # <-- Add here
```

Then run a check:
```bash
python tracker.py
```

### Adding New Client

Edit `config.yaml`:
```yaml
clients:
  # ... existing clients ...
  
  newclient:
    domain: "newclient.com"
    name: "New Client Name"
    keywords:
      - "keyword one"
      - "keyword two"
```

### View Historical Data

```python
# Open Python shell
python3

from database import RankingDatabase
db = RankingDatabase()

# Get 30-day history for a keyword
history = db.get_ranking_history('klarity', 'ketamine therapy miami', days=30)

for date, position in history:
    print(f"{date}: #{position if position else 'Not ranking'}")
```

### Check Alerts

Alerts fire automatically when:
- Position moves up/down 5+ spots
- Enter/exit top 10
- Enter/exit top 3
- New entry into rankings
- Drops out of top 100

View alerts:
```python
from database import RankingDatabase
db = RankingDatabase()

alerts = db.get_unacknowledged_alerts()
for alert in alerts:
    print(f"{alert['keyword']}: {alert['alert_type']}")
    
# Mark as read
db.acknowledge_alerts()
```

---

## Advanced Usage

### Using ScraperAPI

For better reliability (bypasses Google blocks):

1. Sign up at scraperapi.com (~$49/mo for 100k requests)
2. Edit `config.yaml`:
```yaml
scraping:
  proxy_service: 'scraperapi'
  scraperapi_key: 'YOUR_KEY_HERE'
```

### Using Selenium (Headless Chrome)

More reliable but slower:

1. Install Chrome/Chromium
2. Edit `config.yaml`:
```yaml
scraping:
  use_selenium: true
```

### Custom Schedules

**Run every 6 hours:**
```bash
# Edit crontab
crontab -e

# Add:
0 */6 * * * cd /path/to/serp-tracker && python tracker.py
```

**Run at specific times:**
```bash
# 8 AM and 8 PM
0 8,20 * * * cd /path/to/serp-tracker && python tracker.py
```

### Email Alerts

Configure in `config.yaml`:
```yaml
reporting:
  email_enabled: true
  email_to: "you@email.com"
  email_from: "tracker@yourdomain.com"
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your@gmail.com"
  smtp_password: "app_password"  # Use app password, not regular password
  
  alert_on_drop: 5  # Alert if drops 5+ positions
  alert_on_exit_top_10: true
```

**Gmail App Password:**
1. Go to myaccount.google.com
2. Security → 2-Step Verification → App passwords
3. Generate new app password
4. Use that in config

### Monitoring Multiple Domains

Track competitors:
```yaml
clients:
  klarity:
    domain: "klarityclinic.com"
    keywords: [...]
  
  competitor1:
    domain: "competitorsite.com"
    name: "Competitor X"
    keywords: [...]  # Same keywords
```

Then compare:
```bash
python report.py
```

### Rate Limiting

Adjust delays between requests:
```yaml
scraping:
  delay_between_requests: 5  # seconds
  # Increase if getting blocked
```

### Database Queries

Direct SQL access:
```bash
sqlite3 data/rankings.db

# Example queries:
.mode column
.headers on

-- Average position per keyword
SELECT keyword, AVG(position) as avg_pos
FROM rankings
WHERE client_id = 'klarity'
GROUP BY keyword;

-- Rankings over time
SELECT check_date, keyword, position
FROM rankings
WHERE client_id = 'klarity'
ORDER BY check_date DESC
LIMIT 50;

-- Exit
.quit
```

---

## Troubleshooting

### "No results found"

**Possible causes:**
- Google is blocking requests (rate limiting)
- Domain not actually ranking
- Wrong domain format in config

**Solutions:**
1. Use ScraperAPI
2. Enable Selenium
3. Increase delay between requests
4. Check domain spelling

### "Connection timeout"

**Solutions:**
1. Check internet connection
2. Increase timeout in scraper.py
3. Use proxy service

### Cron not running

**Check:**
```bash
# macOS
launchctl list | grep serptracker

# Linux
crontab -l
systemctl status serptracker.timer
```

**Debug:**
```bash
# Check logs
tail -f logs/tracker.log
tail -f logs/tracker.error.log
```

### Database locked

If multiple processes accessing DB:
```bash
# Kill any running tracker processes
ps aux | grep tracker.py
kill <PID>

# Or just wait - SQLite has built-in retry logic
```

---

## Performance Tips

### Optimization

1. **Use ScraperAPI** - fastest, most reliable
2. **Limit results** - check top 50 instead of 100
3. **Batch by client** - run one client per day
4. **Selenium only when needed** - slower but more reliable

### Cost vs Speed

| Method | Speed | Reliability | Cost |
|--------|-------|-------------|------|
| Requests | Fast | 70% | Free |
| Selenium | Slow | 85% | Free |
| ScraperAPI | Fast | 95% | $49/mo |

For 12 keywords (6 per client), checking daily:
- Requests: Free, occasional failures
- ScraperAPI: ~360 requests/mo (~$1 worth)

---

## Client Reporting

### Monthly Report

```bash
# Generate HTML report
python report.py --html --output reports/monthly_$(date +%Y%m).html

# Export data
python export.py --format comparison --client klarity --output reports/klarity_monthly.csv

# Email report
python report.py --email
```

### Weekly Summary

Create a script `weekly_report.sh`:
```bash
#!/bin/bash
cd /path/to/serp-tracker

# Generate reports for both clients
python report.py --html --output reports/weekly_$(date +%Y%m%d).html

# Send email
python report.py --email

echo "Weekly report generated"
```

Run weekly:
```bash
chmod +x weekly_report.sh

# Add to crontab (every Monday at 9 AM)
0 9 * * 1 /path/to/serp-tracker/weekly_report.sh
```

---

## Integration with Ahrefs

Since you have Ahrefs, compare data:

1. **Export your tracker data:**
```bash
python export.py --format ahrefs --client klarity
```

2. **In Ahrefs:**
- Rank Tracker → Import positions
- Upload the CSV
- Compare against their data

3. **Use both:**
- Ahrefs: Comprehensive SEO metrics
- SERP Tracker: Your specific checks, daily monitoring

---

## Tips

1. **Start small** - test with 2-3 keywords first
2. **Monitor logs** - check weekly for errors
3. **Compare sources** - verify against manual Google searches occasionally
4. **Adjust delays** - if getting blocked, increase delays
5. **Use test mode** - `--test` flag for quick checks
6. **Backup database** - copy `data/rankings.db` monthly
