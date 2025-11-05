"""
Main SERP tracking orchestrator.
Runs through all configured keywords and tracks positions.
"""

import yaml
import time
import argparse
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from database import RankingDatabase
from scraper import create_scraper


class SERPTracker:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.db = RankingDatabase(self.config['database']['path'])
        self.scraper = create_scraper(self.config)
        
    def _load_config(self, config_path: str) -> dict:
        """Load YAML configuration."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def track_all(self, test_mode: bool = False):
        """Track all configured keywords for all clients."""
        
        print(f"\n{'='*60}")
        print(f"SERP Tracking Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        total_keywords = 0
        successful = 0
        failed = 0
        errors = []
        
        clients = self.config['clients']
        
        for client_id, client_data in clients.items():
            print(f"\n📊 Tracking: {client_data['name']}")
            print(f"   Domain: {client_data['domain']}")
            print(f"   Keywords: {len(client_data['keywords'])}\n")
            
            domain = client_data['domain']
            keywords = client_data['keywords']
            
            # In test mode, only check first keyword
            if test_mode:
                keywords = keywords[:1]
                print("   [TEST MODE - checking first keyword only]\n")
            
            for idx, keyword in enumerate(keywords, 1):
                total_keywords += 1
                
                print(f"   [{idx}/{len(keywords)}] {keyword}...", end=" ")
                
                try:
                    result = self.scraper.search_google(
                        keyword=keyword,
                        target_domain=domain,
                        num_results=self.config['scraping']['results_per_page']
                    )
                    
                    if result:
                        position, url, title, snippet = result
                        print(f"✓ Position {position}")
                        
                        self.db.save_ranking(
                            client_id=client_id,
                            domain=domain,
                            keyword=keyword,
                            position=position,
                            url=url,
                            title=title,
                            snippet=snippet
                        )
                        successful += 1
                    else:
                        print("✗ Not in top 100")
                        self.db.save_ranking(
                            client_id=client_id,
                            domain=domain,
                            keyword=keyword,
                            position=None
                        )
                        successful += 1
                    
                    # Respect rate limiting
                    if not test_mode:
                        delay = self.config['scraping']['delay_between_requests']
                        time.sleep(delay + random.uniform(0, 2))
                    
                except Exception as e:
                    print(f"✗ Error: {str(e)[:50]}")
                    failed += 1
                    errors.append(f"{keyword}: {str(e)}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the run
        self.db.log_tracking_run(
            total_keywords=total_keywords,
            successful=successful,
            failed=failed,
            duration=duration,
            errors=errors if errors else None
        )
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Total keywords: {total_keywords}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Duration: {duration:.1f}s")
        print(f"{'='*60}\n")
        
        # Check for alerts
        alerts = self.db.get_unacknowledged_alerts()
        if alerts:
            print(f"\n🚨 {len(alerts)} New Alerts:")
            for alert in alerts:
                self._print_alert(alert)
            print()
    
    def _print_alert(self, alert: Dict):
        """Pretty print an alert."""
        emoji_map = {
            'major_movement': '📈' if alert['change'] > 0 else '📉',
            'entered_top_10': '🎯',
            'exited_top_10': '⚠️',
            'entered_top_3': '🏆',
            'exited_top_3': '⚡',
            'new_entry': '🆕',
            'dropped_out': '❌'
        }
        
        emoji = emoji_map.get(alert['alert_type'], '📊')
        
        old_pos = alert['old_position'] if alert['old_position'] else 'N/A'
        new_pos = alert['new_position'] if alert['new_position'] else 'N/A'
        
        print(f"   {emoji} {alert['keyword']}")
        print(f"      {old_pos} → {new_pos} (change: {alert['change']:+d})")
    
    def track_client(self, client_id: str):
        """Track keywords for a specific client only."""
        if client_id not in self.config['clients']:
            print(f"Error: Client '{client_id}' not found in config")
            return
        
        # Temporarily filter config
        original_clients = self.config['clients']
        self.config['clients'] = {client_id: original_clients[client_id]}
        
        self.track_all()
        
        # Restore
        self.config['clients'] = original_clients
    
    def track_keyword(self, keyword: str):
        """Track a single keyword across all clients."""
        found = False
        
        for client_id, client_data in self.config['clients'].items():
            if keyword in client_data['keywords']:
                found = True
                domain = client_data['domain']
                
                print(f"\nTracking '{keyword}' for {client_data['name']}...")
                
                result = self.scraper.search_google(
                    keyword=keyword,
                    target_domain=domain,
                    num_results=self.config['scraping']['results_per_page']
                )
                
                if result:
                    position, url, title, snippet = result
                    print(f"✓ Position {position}")
                    print(f"  URL: {url}")
                    
                    self.db.save_ranking(
                        client_id=client_id,
                        domain=domain,
                        keyword=keyword,
                        position=position,
                        url=url,
                        title=title,
                        snippet=snippet
                    )
                else:
                    print("✗ Not in top 100")
                    self.db.save_ranking(
                        client_id=client_id,
                        domain=domain,
                        keyword=keyword,
                        position=None
                    )
        
        if not found:
            print(f"Keyword '{keyword}' not found in any client configuration")


import random


def main():
    parser = argparse.ArgumentParser(description='SERP Position Tracker')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode: only check first keyword per client')
    parser.add_argument('--client', type=str, 
                       help='Track specific client only')
    parser.add_argument('--keyword', type=str, 
                       help='Track specific keyword only')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    tracker = SERPTracker(config_path=args.config)
    
    if args.keyword:
        tracker.track_keyword(args.keyword)
    elif args.client:
        tracker.track_client(args.client)
    else:
        tracker.track_all(test_mode=args.test)


if __name__ == "__main__":
    main()
