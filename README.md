# SERP Position Tracker

Tracks keyword rankings for your client websites daily.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure keywords in `config.yaml`
3. Run initial setup: `python setup.py`
4. Test tracker: `python tracker.py --test`
5. Set up daily cron: `python setup.py --install-cron`

## Usage

- Manual check: `python tracker.py`
- View report: `python report.py`
- Export data: `python export.py --format csv`

## Deployment Options

1. **Local Mac** - runs in background via launchd
2. **Digital Ocean Droplet** - $6/mo, always on
3. **Raspberry Pi** - one-time cost, runs 24/7

## Structure

- `tracker.py` - main tracking logic
- `database.py` - SQLite operations
- `scraper.py` - SERP scraping with anti-detection
- `report.py` - generate HTML/email reports
- `config.yaml` - keywords and settings
