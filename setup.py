"""
Setup script for SERP tracker.
Handles installation, cron job setup, and initial configuration.
"""

import os
import sys
import subprocess
from pathlib import Path
import platform


def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        sys.exit(1)
    print("✓ Python version OK")


def install_dependencies():
    """Install required packages."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    dirs = ['data', 'reports', 'logs']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print("✓ Directories created")


def initialize_database():
    """Initialize SQLite database."""
    print("\n🗄️  Initializing database...")
    from database import RankingDatabase
    db = RankingDatabase()
    print("✓ Database initialized")


def setup_cron_mac():
    """Setup launchd job for Mac."""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.serptracker.daily</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{current_dir}/tracker.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{current_dir}</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{current_dir}/logs/tracker.log</string>
    
    <key>StandardErrorPath</key>
    <string>{current_dir}/logs/tracker.error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""
    
    plist_path = Path.home() / "Library/LaunchAgents/com.serptracker.daily.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    # Load the job
    subprocess.run(["launchctl", "load", str(plist_path)])
    
    print(f"✓ Scheduled daily run at 3:00 AM")
    print(f"  Config: {plist_path}")


def setup_cron_linux():
    """Setup cron job for Linux."""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    cron_line = f"0 3 * * * cd {current_dir} && {python_path} tracker.py >> logs/tracker.log 2>&1\n"
    
    # Add to crontab
    try:
        # Get existing crontab
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing_cron = result.stdout if result.returncode == 0 else ""
        
        # Check if already exists
        if "serptracker" in existing_cron or str(current_dir) in existing_cron:
            print("ℹ️  Cron job already exists")
            return
        
        # Add new line
        new_cron = existing_cron + f"# SERP Tracker - Daily at 3 AM\n{cron_line}"
        
        # Write back
        process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
        process.communicate(new_cron.encode())
        
        print("✓ Scheduled daily run at 3:00 AM via cron")
        
    except Exception as e:
        print(f"❌ Failed to setup cron: {e}")
        print("\nManually add this to crontab:")
        print(cron_line)


def setup_systemd_timer():
    """Setup systemd timer for Linux (alternative to cron)."""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=SERP Position Tracker
After=network.target

[Service]
Type=oneshot
WorkingDirectory={current_dir}
ExecStart={python_path} {current_dir}/tracker.py
StandardOutput=append:{current_dir}/logs/tracker.log
StandardError=append:{current_dir}/logs/tracker.error.log

[Install]
WantedBy=multi-user.target
"""
    
    timer_content = """[Unit]
Description=Run SERP tracker daily at 3 AM

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
    
    print("\nSystemd service file:")
    print("Save to: ~/.config/systemd/user/serptracker.service")
    print(service_content)
    
    print("\nSystemd timer file:")
    print("Save to: ~/.config/systemd/user/serptracker.timer")
    print(timer_content)
    
    print("\nThen run:")
    print("  systemctl --user enable serptracker.timer")
    print("  systemctl --user start serptracker.timer")


def setup_scheduling():
    """Setup automated scheduling."""
    print("\n⏰ Setting up scheduled runs...")
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        setup_cron_mac()
    elif system == "Linux":
        print("\nChoose scheduling method:")
        print("1. Cron (traditional)")
        print("2. Systemd timer (modern)")
        choice = input("Enter choice (1/2): ").strip()
        
        if choice == "1":
            setup_cron_linux()
        elif choice == "2":
            setup_systemd_timer()
        else:
            print("Invalid choice")
    else:
        print(f"⚠️  Automatic scheduling not supported on {system}")
        print("You'll need to manually setup scheduling")


def test_installation():
    """Run a quick test."""
    print("\n🧪 Running test...")
    try:
        subprocess.check_call([sys.executable, "tracker.py", "--test"])
        print("✓ Test completed successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Test encountered issues (this may be normal if Google blocks requests)")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup SERP Tracker')
    parser.add_argument('--install-cron', action='store_true', 
                       help='Install cron job only')
    parser.add_argument('--skip-test', action='store_true',
                       help='Skip test run')
    
    args = parser.parse_args()
    
    print("="*60)
    print("SERP Tracker Setup")
    print("="*60)
    
    if args.install_cron:
        setup_scheduling()
        return
    
    # Full setup
    check_python_version()
    install_dependencies()
    create_directories()
    initialize_database()
    
    if not args.skip_test:
        test_installation()
    
    # Ask about scheduling
    setup_schedule = input("\n⏰ Setup automated daily tracking? (y/n): ").lower().strip()
    if setup_schedule == 'y':
        setup_scheduling()
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit config.yaml with your keywords")
    print("2. Run: python tracker.py --test")
    print("3. View report: python report.py")
    print("\nFull documentation in README.md")


if __name__ == "__main__":
    main()
