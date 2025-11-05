"""
Export ranking data to various formats.
"""

import csv
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from database import RankingDatabase


class DataExporter:
    def __init__(self, db_path: str = "data/rankings.db"):
        self.db = RankingDatabase(db_path)
    
    def export_to_csv(self, client_id: str = None, output_path: str = None, days: int = 30):
        """Export rankings to CSV."""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d')
            client_suffix = f"_{client_id}" if client_id else "_all"
            output_path = f"exports/rankings{client_suffix}_{timestamp}.csv"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Query data
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        
        query = """
            SELECT 
                client_id,
                domain,
                keyword,
                position,
                url,
                title,
                check_date
            FROM rankings
            WHERE check_date >= date('now', '-{} days')
        """.format(days)
        
        if client_id:
            query += f" AND client_id = '{client_id}'"
        
        query += " ORDER BY client_id, check_date DESC, position ASC NULLS LAST"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Export
        df.to_csv(output_path, index=False)
        print(f"✓ Exported to {output_path}")
        print(f"  Rows: {len(df)}")
        
        return output_path
    
    def export_to_json(self, client_id: str = None, output_path: str = None, days: int = 30):
        """Export rankings to JSON."""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d')
            client_suffix = f"_{client_id}" if client_id else "_all"
            output_path = f"exports/rankings{client_suffix}_{timestamp}.json"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Query data
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                client_id,
                domain,
                keyword,
                position,
                url,
                title,
                snippet,
                check_date
            FROM rankings
            WHERE check_date >= date('now', '-{} days')
        """.format(days)
        
        if client_id:
            query += f" AND client_id = '{client_id}'"
        
        query += " ORDER BY client_id, check_date DESC"
        
        cursor.execute(query)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'client_id': row[0],
                'domain': row[1],
                'keyword': row[2],
                'position': row[3],
                'url': row[4],
                'title': row[5],
                'snippet': row[6],
                'check_date': row[7]
            })
        
        conn.close()
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Exported to {output_path}")
        print(f"  Records: {len(results)}")
        
        return output_path
    
    def export_comparison_report(self, client_id: str, output_path: str = None):
        """Export a comparison report showing changes over time."""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d')
            output_path = f"exports/comparison_{client_id}_{timestamp}.csv"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        
        # Get current and 7-day-ago positions
        query = """
            WITH current_positions AS (
                SELECT keyword, position, check_date
                FROM rankings
                WHERE client_id = ? 
                AND check_date = (SELECT MAX(check_date) FROM rankings WHERE client_id = ?)
            ),
            old_positions AS (
                SELECT keyword, position, check_date
                FROM rankings
                WHERE client_id = ?
                AND check_date = (
                    SELECT MAX(check_date) 
                    FROM rankings 
                    WHERE client_id = ? 
                    AND check_date <= date('now', '-7 days')
                )
            )
            SELECT 
                c.keyword,
                c.position as current_position,
                o.position as previous_position,
                (o.position - c.position) as change,
                c.check_date as current_date,
                o.check_date as previous_date
            FROM current_positions c
            LEFT JOIN old_positions o ON c.keyword = o.keyword
            ORDER BY 
                CASE 
                    WHEN c.position IS NULL THEN 999
                    ELSE c.position
                END
        """
        
        df = pd.read_sql_query(query, conn, params=(client_id, client_id, client_id, client_id))
        conn.close()
        
        # Add change description
        def describe_change(row):
            if pd.isna(row['previous_position']):
                return 'New'
            elif pd.isna(row['current_position']):
                return 'Dropped out'
            elif row['change'] > 0:
                return f'↑ {int(row["change"])}'
            elif row['change'] < 0:
                return f'↓ {abs(int(row["change"]))}'
            else:
                return '–'
        
        df['change_description'] = df.apply(describe_change, axis=1)
        
        df.to_csv(output_path, index=False)
        print(f"✓ Comparison report exported to {output_path}")
        
        return output_path
    
    def export_for_ahrefs_import(self, client_id: str, output_path: str = None):
        """Export in format suitable for importing into Ahrefs or other tools."""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d')
            output_path = f"exports/ahrefs_import_{client_id}_{timestamp}.csv"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Get latest rankings
        rankings = self.db.get_current_rankings(client_id)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Position', 'URL'])
            
            for r in rankings:
                writer.writerow([
                    r['keyword'],
                    r['position'] if r['position'] else 'Not ranking',
                    r['url'] if r['url'] else ''
                ])
        
        print(f"✓ Ahrefs format exported to {output_path}")
        
        return output_path


def main():
    parser = argparse.ArgumentParser(description='Export SERP tracking data')
    parser.add_argument('--format', choices=['csv', 'json', 'comparison', 'ahrefs'], 
                       default='csv', help='Export format')
    parser.add_argument('--client', type=str, help='Client ID to export')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--days', type=int, default=30, 
                       help='Number of days of history to export')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    if args.format == 'csv':
        exporter.export_to_csv(
            client_id=args.client,
            output_path=args.output,
            days=args.days
        )
    elif args.format == 'json':
        exporter.export_to_json(
            client_id=args.client,
            output_path=args.output,
            days=args.days
        )
    elif args.format == 'comparison':
        if not args.client:
            print("Error: --client required for comparison report")
            return
        exporter.export_comparison_report(
            client_id=args.client,
            output_path=args.output
        )
    elif args.format == 'ahrefs':
        if not args.client:
            print("Error: --client required for Ahrefs export")
            return
        exporter.export_for_ahrefs_import(
            client_id=args.client,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
