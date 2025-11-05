"""
Generate reports from tracking data.
Supports HTML reports, email notifications, and CLI summaries.
"""

import yaml
from datetime import datetime, timedelta
from pathlib import Path
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import RankingDatabase


class ReportGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.db = RankingDatabase(self.config['database']['path'])
    
    def generate_cli_report(self, client_id: str = None):
        """Generate a CLI summary report."""
        
        print(f"\n{'='*80}")
        print(f"SERP Tracking Report - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")
        
        clients = self.config['clients']
        
        if client_id:
            if client_id not in clients:
                print(f"Error: Client '{client_id}' not found")
                return
            clients = {client_id: clients[client_id]}
        
        for cid, client_data in clients.items():
            self._print_client_summary(cid, client_data)
    
    def _print_client_summary(self, client_id: str, client_data: dict):
        """Print summary for one client."""
        
        print(f"\n📊 {client_data['name']} ({client_data['domain']})")
        print(f"{'-'*80}\n")
        
        # Get stats
        stats = self.db.get_stats(client_id)
        
        print(f"Overview:")
        print(f"  Total Keywords: {stats['total_keywords']}")
        print(f"  Ranking: {stats['ranking_keywords']}")
        print(f"  Top 10: {stats['top_10']}")
        print(f"  Top 3: {stats['top_3']}")
        if stats['avg_position']:
            print(f"  Average Position: {stats['avg_position']}")
        print()
        
        # Get current rankings
        rankings = self.db.get_current_rankings(client_id)
        
        if not rankings:
            print("  No ranking data available yet.\n")
            return
        
        # Group by position
        top_3 = [r for r in rankings if r['position'] and r['position'] <= 3]
        top_10 = [r for r in rankings if r['position'] and 3 < r['position'] <= 10]
        top_100 = [r for r in rankings if r['position'] and r['position'] > 10]
        not_ranking = [r for r in rankings if r['position'] is None]
        
        if top_3:
            print("  🏆 Top 3:")
            for r in top_3:
                print(f"    #{r['position']} - {r['keyword']}")
            print()
        
        if top_10:
            print("  🎯 Top 10 (4-10):")
            for r in top_10:
                print(f"    #{r['position']} - {r['keyword']}")
            print()
        
        if top_100:
            print("  📈 Ranking (11-100):")
            for r in top_100:
                print(f"    #{r['position']} - {r['keyword']}")
            print()
        
        if not_ranking:
            print("  ❌ Not Ranking (>100):")
            for r in not_ranking:
                print(f"    {r['keyword']}")
            print()
    
    def generate_html_report(self, output_path: str = None) -> str:
        """Generate a comprehensive HTML report."""
        
        if not output_path:
            output_path = f"reports/serp_report_{datetime.now().strftime('%Y%m%d')}.html"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Gather data for all clients
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'clients': []
        }
        
        for client_id, client_data in self.config['clients'].items():
            stats = self.db.get_stats(client_id)
            rankings = self.db.get_current_rankings(client_id)
            
            client_report = {
                'id': client_id,
                'name': client_data['name'],
                'domain': client_data['domain'],
                'stats': stats,
                'rankings': rankings
            }
            
            report_data['clients'].append(client_report)
        
        # Get recent alerts
        alerts = self.db.get_unacknowledged_alerts()
        report_data['alerts'] = alerts
        
        # Render HTML
        html = self._render_html_template(report_data)
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"\n✓ HTML report generated: {output_path}\n")
        return output_path
    
    def _render_html_template(self, data: dict) -> str:
        """Render HTML report from template."""
        
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SERP Tracking Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .alerts {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .alerts h2 { color: #856404; margin-bottom: 15px; }
        .alert-item { 
            padding: 10px; 
            margin: 10px 0;
            background: white;
            border-radius: 5px;
        }
        .client-section {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .client-header {
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .client-header h2 { color: #667eea; }
        .client-header .domain { color: #999; font-size: 14px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card .label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .rankings-table {
            width: 100%;
            border-collapse: collapse;
        }
        .rankings-table th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }
        .rankings-table td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        .position {
            font-weight: bold;
            color: #667eea;
        }
        .position.top-3 { color: #28a745; }
        .position.top-10 { color: #17a2b8; }
        .position.not-ranking { color: #dc3545; }
        .footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 SERP Tracking Report</h1>
            <p>Generated: {{ data.generated_at }}</p>
        </div>
        
        {% if data.alerts %}
        <div class="alerts">
            <h2>🚨 Recent Alerts</h2>
            {% for alert in data.alerts %}
            <div class="alert-item">
                <strong>{{ alert.keyword }}</strong> - {{ alert.alert_type }}
                <br>
                Position: {{ alert.old_position or 'N/A' }} → {{ alert.new_position or 'N/A' }}
                (Change: {{ alert.change|abs }} positions)
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% for client in data.clients %}
        <div class="client-section">
            <div class="client-header">
                <h2>{{ client.name }}</h2>
                <div class="domain">{{ client.domain }}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">{{ client.stats.total_keywords }}</div>
                    <div class="label">Total Keywords</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ client.stats.ranking_keywords }}</div>
                    <div class="label">Ranking</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ client.stats.top_10 }}</div>
                    <div class="label">Top 10</div>
                </div>
                <div class="stat-card">
                    <div class="number">{{ client.stats.top_3 }}</div>
                    <div class="label">Top 3</div>
                </div>
                {% if client.stats.avg_position %}
                <div class="stat-card">
                    <div class="number">{{ client.stats.avg_position }}</div>
                    <div class="label">Avg Position</div>
                </div>
                {% endif %}
            </div>
            
            {% if client.rankings %}
            <table class="rankings-table">
                <thead>
                    <tr>
                        <th>Position</th>
                        <th>Keyword</th>
                        <th>URL</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ranking in client.rankings %}
                    <tr>
                        <td>
                            {% if ranking.position %}
                                {% if ranking.position <= 3 %}
                                <span class="position top-3">#{{ ranking.position }}</span>
                                {% elif ranking.position <= 10 %}
                                <span class="position top-10">#{{ ranking.position }}</span>
                                {% else %}
                                <span class="position">#{{ ranking.position }}</span>
                                {% endif %}
                            {% else %}
                                <span class="position not-ranking">Not Ranking</span>
                            {% endif %}
                        </td>
                        <td>{{ ranking.keyword }}</td>
                        <td style="font-size: 12px; color: #666;">
                            {{ ranking.url or 'N/A' }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No ranking data available yet.</p>
            {% endif %}
        </div>
        {% endfor %}
        
        <div class="footer">
            Generated by SERP Tracker
        </div>
    </div>
</body>
</html>
        """
        
        template_obj = Template(template)
        return template_obj.render(data=data)
    
    def send_email_report(self):
        """Send email report if configured."""
        
        if not self.config['reporting']['email_enabled']:
            print("Email reporting not enabled in config")
            return
        
        # Generate HTML report
        html_path = self.generate_html_report()
        
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"SERP Tracking Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.config['reporting']['email_from']
        msg['To'] = self.config['reporting']['email_to']
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(
                self.config['reporting']['smtp_host'],
                self.config['reporting']['smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.config['reporting']['smtp_user'],
                    self.config['reporting']['smtp_password']
                )
                server.send_message(msg)
            
            print(f"✓ Email report sent to {self.config['reporting']['email_to']}")
        
        except Exception as e:
            print(f"✗ Failed to send email: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SERP tracking reports')
    parser.add_argument('--client', type=str, help='Report for specific client')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--email', action='store_true', help='Send email report')
    parser.add_argument('--output', type=str, help='Output path for HTML report')
    
    args = parser.parse_args()
    
    reporter = ReportGenerator()
    
    if args.email:
        reporter.send_email_report()
    elif args.html:
        reporter.generate_html_report(output_path=args.output)
    else:
        reporter.generate_cli_report(client_id=args.client)


if __name__ == "__main__":
    main()
