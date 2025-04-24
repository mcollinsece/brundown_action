import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import json

class BurndownGenerator:
    def __init__(self):
        self.repo = os.getenv("GITHUB_REPOSITORY")
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.charts_dir = "charts"
        
        # Create charts directory if it doesn't exist
        os.makedirs(self.charts_dir, exist_ok=True)

    def fetch_issues(self):
        """Fetch all issues from GitHub"""
        issues = []
        page = 1
        
        while True:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            params = {
                "state": "all",
                "per_page": 100,
                "page": page,
                "sort": "created",
                "direction": "asc"
            }
            
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                break
                
            issues.extend([issue for issue in data if "pull_request" not in issue])
            page += 1
            
        return issues

    def generate_counts(self, issues, start_date, end_date):
        """Generate daily counts of open and closed issues"""
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)

        open_count = []
        closed_count = []

        for day in date_range:
            day_end = day.replace(hour=23, minute=59, second=59)
            open_issues = 0
            closed_issues = 0
            
            for issue in issues:
                created = parse(issue["created_at"])
                closed = parse(issue["closed_at"]) if issue["closed_at"] else None
                
                if created <= day_end:
                    if closed is None or closed > day_end:
                        open_issues += 1
                    else:
                        closed_issues += 1
                        
            open_count.append(open_issues)
            closed_count.append(closed_issues)
            
        return date_range, open_count, closed_count

    def create_chart(self, date_range, open_count, closed_count, filename, title):
        """Create and save a burndown chart"""
        plt.figure(figsize=(12, 6))
        plt.plot(date_range, open_count, label="Open Issues", color="red", marker='o')
        plt.plot(date_range, closed_count, label="Closed Issues", color="green", marker='o')
        
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Number of Issues")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        
        # Format dates on x-axis
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.charts_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()

    def generate_charts(self):
        """Generate multiple burndown charts for different time periods"""
        issues = self.fetch_issues()
        end_date = datetime.now()
        
        # Generate charts for different time periods
        periods = {
            "7d": (end_date - timedelta(days=7), "Last 7 Days", "burndown-7d.png"),
            "30d": (end_date - timedelta(days=30), "Last 30 Days", "burndown-30d.png"),
            "90d": (end_date - timedelta(days=90), "Last 90 Days", "burndown-90d.png"),
            "1y": (end_date - relativedelta(years=1), "Last Year", "burndown-1y.png"),
        }
        
        for period, (start_date, title, filename) in periods.items():
            date_range, open_count, closed_count = self.generate_counts(issues, start_date, end_date)
            self.create_chart(date_range, open_count, closed_count, filename, title)

if __name__ == "__main__":
    generator = BurndownGenerator()
    generator.generate_charts() 