#!/usr/bin/env python3
"""
Extract fiscal impact categories from bills based on keyword analysis.
"""

import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# Fiscal category patterns
CATEGORIES = {
    'New Tax/Fee': {
        'patterns': [
            r'\btax\b', r'\blevy\b', r'\bfee\b', r'\bsurcharge\b', r'\bexcise\b',
            r'impose.*tax', r'new.*tax', r'additional.*tax'
        ],
        'exclude': [r'tax relief', r'tax credit', r'tax exempt', r'tax cut', r'repeal.*tax']
    },
    'New Spending': {
        'patterns': [
            r'\bfund\b', r'\bappropriat', r'\bgrant\b', r'\bsubsid',
            r'million', r'billion', r'\bspending\b'
        ],
        'exclude': [r'reduce.*spending', r'cut.*spending']
    },
    'New Debt': {
        'patterns': [
            r'\bbond\b', r'\bdebt\b', r'\bborrow'
        ],
        'exclude': []
    },
    'Tax Relief': {
        'patterns': [
            r'tax relief', r'tax credit', r'tax exempt', r'tax deduct',
            r'repeal.*tax', r'reduce.*tax', r'tax cut'
        ],
        'exclude': []
    },
    'Cost Savings': {
        'patterns': [
            r'reduce cost', r'cost sav', r'streamline', r'deregulat',
            r'eliminate.*fee', r'reduce.*fee'
        ],
        'exclude': []
    }
}

# Magnitude indicators
HIGH_MAGNITUDE = [r'billion', r'\$\d{3,}.*million', r'major', r'comprehensive', r'statewide']
MEDIUM_MAGNITUDE = [r'million', r'\$\d{1,2}.*million', r'significant']


def categorize_bill(bill: dict) -> dict | None:
    """Categorize a bill's fiscal impact."""
    text = ' '.join([
        bill.get('title', ''),
        bill.get('ai_summary', ''),
        bill.get('description', ''),
        ' '.join(bill.get('concerns', []))
    ]).lower()

    for category, config in CATEGORIES.items():
        # Check exclusions first
        excluded = False
        for pattern in config['exclude']:
            if re.search(pattern, text):
                excluded = True
                break

        if excluded:
            continue

        # Check for matches
        for pattern in config['patterns']:
            if re.search(pattern, text):
                # Determine magnitude
                magnitude = 'Low'
                for high_pattern in HIGH_MAGNITUDE:
                    if re.search(high_pattern, text):
                        magnitude = 'High'
                        break
                if magnitude != 'High':
                    for med_pattern in MEDIUM_MAGNITUDE:
                        if re.search(med_pattern, text):
                            magnitude = 'Medium'
                            break

                return {
                    'category': category,
                    'magnitude': magnitude
                }

    return None


def extract_fiscal_impact():
    """Extract fiscal impact data from all bills."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Categorize bills
    fiscal_bills = []
    category_counts = {cat: 0 for cat in CATEGORIES}
    magnitude_counts = {'High': 0, 'Medium': 0, 'Low': 0}

    for bill in bills:
        result = categorize_bill(bill)
        if result:
            fiscal_bills.append({
                'bill_id': bill.get('bill_id'),
                'bill_number': bill.get('bill_number'),
                'title': bill.get('title'),
                'category': result['category'],
                'magnitude': result['magnitude'],
                'threat_level': bill.get('threat_level'),
                'ai_summary': bill.get('ai_summary', '')[:200]
            })
            category_counts[result['category']] += 1
            magnitude_counts[result['magnitude']] += 1

    # Sort by magnitude (High first) then by category
    magnitude_order = {'High': 0, 'Medium': 1, 'Low': 2}
    fiscal_bills.sort(key=lambda x: (magnitude_order.get(x['magnitude'], 3), x['category']))

    # Prepare output
    output = {
        'summary': {
            'total_bills': len(bills),
            'fiscal_bills': len(fiscal_bills),
            'percentage': round(len(fiscal_bills) / len(bills) * 100, 1) if bills else 0
        },
        'by_category': category_counts,
        'by_magnitude': magnitude_counts,
        'categories': [
            {'name': 'New Tax/Fee', 'color': '#dc2626', 'icon': 'tax'},
            {'name': 'New Spending', 'color': '#ea580c', 'icon': 'spending'},
            {'name': 'New Debt', 'color': '#ca8a04', 'icon': 'debt'},
            {'name': 'Tax Relief', 'color': '#16a34a', 'icon': 'relief'},
            {'name': 'Cost Savings', 'color': '#059669', 'icon': 'savings'}
        ],
        'high_impact_bills': [b for b in fiscal_bills if b['magnitude'] == 'High'][:50],
        'bills': fiscal_bills
    }

    # Save output
    output_file = DATA_DIR / "fiscal_impact.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"Fiscal Impact Analysis Complete")
    print("=" * 32)
    print(f"Total bills analyzed: {len(bills)}")
    print(f"Bills with fiscal impact: {len(fiscal_bills)}")
    print(f"\nBy Category:")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    print(f"\nBy Magnitude:")
    for mag, count in magnitude_counts.items():
        print(f"  {mag}: {count}")
    print(f"\nHigh impact bills: {len(output['high_impact_bills'])}")
    print(f"Output: {output_file}")

    return 0


if __name__ == "__main__":
    exit(extract_fiscal_impact())
