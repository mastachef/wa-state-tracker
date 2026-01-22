#!/usr/bin/env python3
"""
Fetch campaign finance data from WA Public Disclosure Commission (PDC).
Uses the data.wa.gov Socrata API - FREE, no key required for basic use.
"""

import json
import requests
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import time

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# Socrata API endpoints on data.wa.gov
CONTRIBUTIONS_URL = "https://data.wa.gov/resource/kv7h-kjye.json"
EXPENDITURES_URL = "https://data.wa.gov/resource/tijg-9zyp.json"

# Current election cycles to focus on
ELECTION_YEARS = [2024, 2022, 2020]


def fetch_json(url: str, params: dict = None) -> list:
    """Fetch JSON from Socrata API."""
    if params is None:
        params = {}

    # Add default limit
    if '$limit' not in params:
        params['$limit'] = 10000

    print(f"  Fetching: {url}")
    print(f"  Params: {params}")

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        print(f"  Got {len(data)} records")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return []


def normalize_name(name: str) -> str:
    """Normalize a name for matching."""
    if not name:
        return ""
    # Remove common suffixes and normalize
    name = name.upper().strip()
    for suffix in [' JR', ' SR', ' III', ' II', ' IV']:
        name = name.replace(suffix, '')
    return name


def match_legislator(filer_name: str, legislators: dict) -> str | None:
    """Try to match a filer name to a legislator."""
    if not filer_name:
        return None

    filer_norm = normalize_name(filer_name)

    # Direct match
    if filer_norm in legislators:
        return filer_norm

    # Try matching last name + first initial
    for leg_name in legislators.keys():
        leg_parts = leg_name.split()
        if len(leg_parts) >= 2:
            # Last name match
            if leg_parts[-1] in filer_norm:
                # First name/initial match
                if leg_parts[0][0] in filer_norm.split()[0] if filer_norm.split() else False:
                    return leg_name

    # Try fuzzy match on last name
    filer_parts = filer_norm.split()
    for leg_name in legislators.keys():
        leg_parts = leg_name.split()
        # Check if last names match
        if filer_parts and leg_parts:
            if filer_parts[-1] == leg_parts[-1] or leg_parts[-1] in filer_norm:
                return leg_name

    return None


def fetch_campaign_finance():
    """Fetch campaign finance data for WA legislators."""
    print("=" * 60)
    print("WA Bill Tracker - Campaign Finance Data")
    print("=" * 60)

    # Load legislators
    leg_file = DATA_DIR / "legislators.json"
    if not leg_file.exists():
        print("No legislators.json found. Run fetch_legislators.py first.")
        return 1

    with open(leg_file, 'r', encoding='utf-8') as f:
        legislators_list = json.load(f)

    # Build lookup dict
    legislators = {}
    for leg in legislators_list:
        name = leg.get('name', '')
        if name:
            norm_name = normalize_name(name)
            legislators[norm_name] = leg
            leg['contributions'] = []
            leg['total_raised'] = 0
            leg['top_donors'] = []
            leg['donor_categories'] = defaultdict(float)

    print(f"\nLoaded {len(legislators)} legislators")

    # Fetch contributions for state legislative candidates
    print("\n" + "=" * 40)
    print("Fetching Contribution Data")
    print("=" * 40)

    all_contributions = []

    for year in ELECTION_YEARS:
        print(f"\nElection Year: {year}")

        # Query for state legislative contributions
        # jurisdiction_type=Legislative covers state reps and senators
        params = {
            '$limit': 50000,
            'type': 'Candidate',
            'jurisdiction_type': 'Legislative',
            'election_year': str(year),
            '$select': 'id,filer_name,contributor_name,contributor_city,contributor_employer_name,amount,receipt_date,contributor_category,office,party,legislative_district',
            '$order': 'amount DESC'
        }

        contributions = fetch_json(CONTRIBUTIONS_URL, params)
        all_contributions.extend(contributions)

        time.sleep(1)  # Rate limit courtesy

    print(f"\nTotal contributions fetched: {len(all_contributions)}")

    # Process contributions
    print("\nProcessing contributions...")
    matched_count = 0
    unmatched_filers = set()

    for contrib in all_contributions:
        filer_name = contrib.get('filer_name', '')
        leg_name = match_legislator(filer_name, legislators)

        if leg_name and leg_name in legislators:
            leg = legislators[leg_name]
            amount = float(contrib.get('amount', 0) or 0)

            leg['total_raised'] += amount
            leg['contributions'].append({
                'donor': contrib.get('contributor_name', 'Unknown'),
                'employer': contrib.get('contributor_employer_name', ''),
                'amount': amount,
                'date': contrib.get('receipt_date', ''),
                'category': contrib.get('contributor_category', '')
            })

            # Track by category
            category = contrib.get('contributor_category', 'Other') or 'Other'
            leg['donor_categories'][category] += amount

            matched_count += 1
        else:
            if filer_name:
                unmatched_filers.add(filer_name)

    print(f"Matched {matched_count} contributions to legislators")
    print(f"Unmatched filers: {len(unmatched_filers)}")

    # Calculate top donors for each legislator
    print("\nCalculating top donors...")
    for leg in legislators.values():
        # Aggregate by donor name
        donor_totals = defaultdict(lambda: {'total': 0, 'employer': '', 'count': 0})
        for contrib in leg['contributions']:
            donor = contrib['donor']
            donor_totals[donor]['total'] += contrib['amount']
            donor_totals[donor]['employer'] = contrib.get('employer', '')
            donor_totals[donor]['count'] += 1

        # Sort and get top 20
        sorted_donors = sorted(donor_totals.items(), key=lambda x: -x[1]['total'])
        leg['top_donors'] = [
            {
                'name': donor,
                'total': round(info['total'], 2),
                'employer': info['employer'],
                'count': info['count']
            }
            for donor, info in sorted_donors[:20]
        ]

        # Convert categories to list
        leg['donor_categories'] = [
            {'category': cat, 'total': round(amount, 2)}
            for cat, amount in sorted(leg['donor_categories'].items(), key=lambda x: -x[1])
        ][:10]

        # Keep only summary of contributions (not full list)
        leg['contribution_count'] = len(leg['contributions'])
        del leg['contributions']

    # Update legislators file
    legislators_list = list(legislators.values())
    legislators_list.sort(key=lambda x: -x.get('total_raised', 0))

    # Also create a separate finance summary file
    finance_summary = {
        'updated': datetime.now().isoformat(),
        'election_years': ELECTION_YEARS,
        'total_contributions': len(all_contributions),
        'matched_contributions': matched_count,
        'top_fundraisers': [
            {
                'name': leg['name'],
                'chamber': leg.get('chamber', ''),
                'party': leg.get('party', ''),
                'district': leg.get('district', ''),
                'total_raised': round(leg.get('total_raised', 0), 2),
                'top_donors': leg.get('top_donors', [])[:5]
            }
            for leg in legislators_list[:50]
            if leg.get('total_raised', 0) > 0
        ]
    }

    # Save finance summary
    finance_file = DATA_DIR / "campaign_finance.json"
    with open(finance_file, 'w', encoding='utf-8') as f:
        json.dump(finance_summary, f, indent=2)
    print(f"\nSaved finance summary to {finance_file}")

    # Update legislators file with finance data
    with open(leg_file, 'w', encoding='utf-8') as f:
        json.dump(legislators_list, f, indent=2)
    print(f"Updated {leg_file} with finance data")

    # Print top fundraisers
    print("\n" + "=" * 60)
    print("TOP 20 FUNDRAISERS")
    print("=" * 60)
    for i, leg in enumerate(legislators_list[:20], 1):
        total = leg.get('total_raised', 0)
        if total > 0:
            party = leg.get('party', '?')
            chamber = 'H' if leg.get('chamber') == 'House' else 'S'
            print(f"{i:2}. {leg['name'][:30]:30} ({party}-{chamber}) ${total:>12,.2f}")

    return 0


if __name__ == "__main__":
    exit(fetch_campaign_finance())
