"""
Database operations for SERP tracking.
Stores historical ranking data, tracks changes, identifies trends.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json


class RankingDatabase:
    def __init__(self, db_path: str = "data/rankings.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Rankings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                keyword TEXT NOT NULL,
                position INTEGER,
                url TEXT,
                title TEXT,
                snippet TEXT,
                check_date TIMESTAMP NOT NULL,
                search_volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, keyword, check_date)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rankings_lookup 
            ON rankings(client_id, keyword, check_date)
        """)
        
        # Alerts table for significant changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                old_position INTEGER,
                new_position INTEGER,
                change INTEGER,
                alert_date TIMESTAMP NOT NULL,
                acknowledged BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Metadata table for tracking runs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracking_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TIMESTAMP NOT NULL,
                total_keywords INTEGER,
                successful_checks INTEGER,
                failed_checks INTEGER,
                duration_seconds REAL,
                error_log TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_ranking(
        self,
        client_id: str,
        domain: str,
        keyword: str,
        position: Optional[int],
        url: Optional[str] = None,
        title: Optional[str] = None,
        snippet: Optional[str] = None,
        search_volume: Optional[int] = None
    ) -> bool:
        """Save a ranking check result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        check_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO rankings 
                (client_id, domain, keyword, position, url, title, snippet, 
                 check_date, search_volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, domain, keyword, position, url, title, snippet, 
                  check_date, search_volume))
            
            conn.commit()
            
            # Check if this warrants an alert
            self._check_for_alerts(cursor, client_id, keyword, position, check_date)
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error saving ranking: {e}")
            return False
        finally:
            conn.close()
    
    def _check_for_alerts(
        self,
        cursor: sqlite3.Cursor,
        client_id: str,
        keyword: str,
        new_position: Optional[int],
        check_date: str
    ):
        """Check if ranking change warrants an alert."""
        # Get previous position
        cursor.execute("""
            SELECT position FROM rankings
            WHERE client_id = ? AND keyword = ? AND check_date < ?
            ORDER BY check_date DESC LIMIT 1
        """, (client_id, keyword, check_date))
        
        result = cursor.fetchone()
        if not result:
            return  # First time tracking this keyword
        
        old_position = result[0]
        
        # No alert if both are None (not ranking)
        if old_position is None and new_position is None:
            return
        
        # Calculate change
        if old_position is None:
            change = -new_position if new_position else 0
            alert_type = "new_entry"
        elif new_position is None:
            change = old_position
            alert_type = "dropped_out"
        else:
            change = old_position - new_position  # Positive = moved up
            
            # Determine alert type
            if abs(change) >= 5:
                alert_type = "major_movement"
            elif old_position <= 10 and new_position > 10:
                alert_type = "exited_top_10"
            elif old_position > 10 and new_position <= 10:
                alert_type = "entered_top_10"
            elif old_position <= 3 and new_position > 3:
                alert_type = "exited_top_3"
            elif old_position > 3 and new_position <= 3:
                alert_type = "entered_top_3"
            else:
                return  # No significant change
        
        # Insert alert
        cursor.execute("""
            INSERT INTO alerts 
            (client_id, keyword, alert_type, old_position, new_position, change, alert_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_id, keyword, alert_type, old_position, new_position, 
              change, datetime.now()))
    
    def get_current_rankings(self, client_id: str) -> List[Dict]:
        """Get most recent rankings for a client."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT keyword, position, url, check_date
            FROM rankings
            WHERE client_id = ? AND check_date = (
                SELECT MAX(check_date) FROM rankings WHERE client_id = ?
            )
            ORDER BY position ASC NULLS LAST
        """, (client_id, client_id))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'keyword': row[0],
                'position': row[1],
                'url': row[2],
                'check_date': row[3]
            })
        
        conn.close()
        return results
    
    def get_ranking_history(
        self,
        client_id: str,
        keyword: str,
        days: int = 30
    ) -> List[Tuple[str, Optional[int]]]:
        """Get ranking history for a specific keyword."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT check_date, position
            FROM rankings
            WHERE client_id = ? AND keyword = ?
            AND check_date >= date('now', '-{} days')
            ORDER BY check_date DESC
        """.format(days), (client_id, keyword))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get all unacknowledged alerts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT client_id, keyword, alert_type, old_position, 
                   new_position, change, alert_date
            FROM alerts
            WHERE acknowledged = 0
            ORDER BY alert_date DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'client_id': row[0],
                'keyword': row[1],
                'alert_type': row[2],
                'old_position': row[3],
                'new_position': row[4],
                'change': row[5],
                'alert_date': row[6]
            })
        
        conn.close()
        return alerts
    
    def acknowledge_alerts(self):
        """Mark all alerts as acknowledged."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE acknowledged = 0")
        conn.commit()
        conn.close()
    
    def log_tracking_run(
        self,
        total_keywords: int,
        successful: int,
        failed: int,
        duration: float,
        errors: List[str] = None
    ):
        """Log a tracking run for diagnostics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        error_log = json.dumps(errors) if errors else None
        
        cursor.execute("""
            INSERT INTO tracking_runs 
            (run_date, total_keywords, successful_checks, failed_checks, 
             duration_seconds, error_log)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now(), total_keywords, successful, failed, duration, error_log))
        
        conn.commit()
        conn.close()
    
    def get_stats(self, client_id: str) -> Dict:
        """Get overall statistics for a client."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current rankings
        cursor.execute("""
            SELECT 
                COUNT(*) as total_keywords,
                COUNT(CASE WHEN position IS NOT NULL THEN 1 END) as ranking_keywords,
                COUNT(CASE WHEN position <= 10 THEN 1 END) as top_10,
                COUNT(CASE WHEN position <= 3 THEN 1 END) as top_3,
                AVG(CASE WHEN position IS NOT NULL THEN position END) as avg_position
            FROM rankings
            WHERE client_id = ? AND check_date = (
                SELECT MAX(check_date) FROM rankings WHERE client_id = ?
            )
        """, (client_id, client_id))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_keywords': stats[0],
            'ranking_keywords': stats[1],
            'top_10': stats[2],
            'top_3': stats[3],
            'avg_position': round(stats[4], 1) if stats[4] else None
        }


# Convenience function
def get_db(db_path: str = "data/rankings.db") -> RankingDatabase:
    """Get database instance."""
    return RankingDatabase(db_path)
