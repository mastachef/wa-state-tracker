#!/usr/bin/env python3
"""
Generate timeline data for bill activity chart.
Creates a JSON file with daily bill activity counts.
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"


def generate_timeline():
    """Generate daily activity counts from bill data."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Count bills by last_action_date
    activity_by_date = defaultdict(lambda: {
        'total': 0,
        'critical': 0,
        'high': 0,
        'moderate': 0,
        'low': 0,
        'beneficial': 0
    })

    for bill in bills:
        date = bill.get('last_action_date', '')
        if not date:
            continue

        activity_by_date[date]['total'] += 1
        threat = bill.get('threat_level', 'moderate')
        if threat in activity_by_date[date]:
            activity_by_date[date][threat] += 1

    # Get date range
    dates = sorted(activity_by_date.keys())
    if not dates:
        print("No dates found")
        return 1

    start_date = datetime.strptime(dates[0], '%Y-%m-%d')
    end_date = datetime.strptime(dates[-1], '%Y-%m-%d')

    # Fill in missing dates with zeros
    timeline = []
    current = start_date
    cumulative = {
        'total': 0,
        'critical': 0,
        'high': 0,
        'moderate': 0,
        'low': 0,
        'beneficial': 0
    }

    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        day_data = activity_by_date.get(date_str, {
            'total': 0, 'critical': 0, 'high': 0,
            'moderate': 0, 'low': 0, 'beneficial': 0
        })

        # Update cumulative totals
        for key in cumulative:
            cumulative[key] += day_data.get(key, 0)

        timeline.append({
            'date': date_str,
            'activity': day_data['total'],
            'cumulative': cumulative['total'],
            'critical': day_data['critical'],
            'high': day_data['high'],
            'moderate': day_data['moderate'],
            'low': day_data['low'],
            'beneficial': day_data['beneficial'],
            'cumulative_threats': cumulative['critical'] + cumulative['high']
        })

        current += timedelta(days=1)

    # Save timeline data
    timeline_file = DATA_DIR / "timeline.json"
    with open(timeline_file, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, indent=2)

    print(f"Generated timeline with {len(timeline)} days")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    return 0


if __name__ == "__main__":
    exit(generate_timeline())
