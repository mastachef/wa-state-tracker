#!/usr/bin/env python3
"""
Analyze bill flooding patterns in the WA State Legislature.
Exposes how legislators abuse session rules by introducing massive numbers of bills
at once, making public scrutiny practically impossible.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"


def analyze_flooding():
    """Analyze bill introduction patterns to expose flooding tactics."""
    print("=" * 60)
    print("WA Bill Tracker - Legislative Flooding Analysis")
    print("=" * 60)

    bills_file = DATA_DIR / "bills.json"
    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    print(f"\nAnalyzing {len(bills)} bills for flooding patterns...\n")

    # Track bills by date
    by_date = defaultdict(lambda: {'total': 0, 'harmful': 0, 'bills': []})
    by_month = defaultdict(lambda: {'total': 0, 'harmful': 0})
    by_year = defaultdict(lambda: {'total': 0, 'harmful': 0})

    harmful_levels = {'critical', 'high'}

    for bill in bills:
        # Try different date fields
        date_str = (
            bill.get('introduced_date') or
            bill.get('last_action_date') or
            ''
        )

        if not date_str or date_str == '':
            continue

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            date_key = date_str
            month_key = date.strftime('%Y-%m')
            year_key = str(date.year)

            is_harmful = bill.get('threat_level') in harmful_levels

            by_date[date_key]['total'] += 1
            by_date[date_key]['bills'].append(bill.get('bill_number'))
            if is_harmful:
                by_date[date_key]['harmful'] += 1

            by_month[month_key]['total'] += 1
            if is_harmful:
                by_month[month_key]['harmful'] += 1

            by_year[year_key]['total'] += 1
            if is_harmful:
                by_year[year_key]['harmful'] += 1

        except ValueError:
            continue

    # Find worst flooding days (threshold: 50+ bills)
    FLOOD_THRESHOLD = 50
    flood_days = []
    for date_str, data in sorted(by_date.items(), key=lambda x: -x[1]['total']):
        if data['total'] >= FLOOD_THRESHOLD:
            flood_days.append({
                'date': date_str,
                'total': data['total'],
                'harmful': data['harmful'],
                'sample_bills': data['bills'][:10]
            })

    # Calculate statistics
    total_bills = len(bills)
    flood_day_bills = sum(d['total'] for d in flood_days)
    flood_percentage = round(flood_day_bills / total_bills * 100, 1) if total_bills else 0

    # Find the worst single day
    worst_day = flood_days[0] if flood_days else None

    # Build daily timeline for chart
    daily_data = []
    for date_str in sorted(by_date.keys()):
        data = by_date[date_str]
        daily_data.append({
            'date': date_str,
            'total': data['total'],
            'harmful': data['harmful'],
            'is_flood': data['total'] >= FLOOD_THRESHOLD
        })

    # Build monthly data
    monthly_data = []
    for month_str in sorted(by_month.keys()):
        data = by_month[month_str]
        monthly_data.append({
            'month': month_str,
            'total': data['total'],
            'harmful': data['harmful']
        })

    # Prepare output
    output = {
        'analysis_date': datetime.now().isoformat(),
        'total_bills': total_bills,
        'flood_threshold': FLOOD_THRESHOLD,
        'summary': {
            'flood_days_count': len(flood_days),
            'bills_on_flood_days': flood_day_bills,
            'flood_percentage': flood_percentage,
            'worst_single_day': worst_day['date'] if worst_day else None,
            'worst_day_count': worst_day['total'] if worst_day else 0,
            'average_per_day': round(total_bills / len(by_date), 1) if by_date else 0
        },
        'flood_days': flood_days[:20],  # Top 20 worst days
        'daily_data': daily_data,
        'monthly_data': monthly_data,
        'by_year': dict(by_year)
    }

    # Save output
    output_file = DATA_DIR / "flooding.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    # Print report
    print("LEGISLATIVE FLOODING ANALYSIS")
    print("-" * 40)
    print(f"Total bills analyzed: {total_bills}")
    print(f"Days with 50+ bills (flood days): {len(flood_days)}")
    print(f"Bills introduced on flood days: {flood_day_bills}")
    print(f"Percentage of all bills: {flood_percentage}%")
    print()

    if worst_day:
        print("WORST FLOODING DAY:")
        print(f"  Date: {worst_day['date']}")
        print(f"  Bills introduced: {worst_day['total']}")
        print(f"  Harmful bills: {worst_day['harmful']}")
        print()

    print("TOP 10 FLOODING DAYS:")
    print("-" * 40)
    for i, day in enumerate(flood_days[:10], 1):
        print(f"  {i}. {day['date']}: {day['total']} bills ({day['harmful']} harmful)")

    print()
    print("MONTHLY BREAKDOWN:")
    print("-" * 40)
    for month in sorted(monthly_data, key=lambda x: -x['total'])[:12]:
        print(f"  {month['month']}: {month['total']} bills ({month['harmful']} harmful)")

    print()
    print("=" * 60)
    print("THIS IS LEGISLATIVE ABUSE")
    print("=" * 60)
    print(f"When {flood_percentage}% of all bills are dumped on just")
    print(f"{len(flood_days)} days, citizens cannot possibly review them.")
    print("This is a deliberate tactic to avoid public scrutiny.")
    print("=" * 60)

    print(f"\nSaved to {output_file}")
    return 0


if __name__ == "__main__":
    exit(analyze_flooding())
