#!/usr/bin/env python3
"""Quick sponsor fetch - processes all bills efficiently."""

import json
import re
import sys
import time
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = Path(__file__).parent.parent / "_data"
BIENNIUM = "2025-26"


def get_sponsors(bill_number: str) -> tuple[str, list[str]]:
    """Fetch sponsors for a bill."""
    url = 'https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetSponsors'
    params = {'biennium': BIENNIUM, 'billId': bill_number}
    try:
        resp = requests.get(url, params=params, timeout=10)
        names = re.findall(r'<LongName>([^<]+)</LongName>', resp.text)
        return bill_number, [name.strip() for name in names if name.strip()]
    except:
        return bill_number, []


def main():
    bills_file = DATA_DIR / "bills.json"
    with open(bills_file, 'r') as f:
        bills = json.load(f)

    print(f"Fetching sponsors for {len(bills)} bills...")

    # Create a map of bill_number -> bill for quick lookup
    bill_map = {b['bill_number']: b for b in bills}
    bill_numbers = list(bill_map.keys())

    updated = 0

    # Process in parallel with 5 workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_sponsors, bn): bn for bn in bill_numbers}

        for i, future in enumerate(as_completed(futures)):
            if i % 200 == 0:
                print(f"  Processed {i}/{len(bills)}...")

            bill_number, sponsors = future.result()
            if sponsors and bill_number in bill_map:
                bill_map[bill_number]['sponsors'] = sponsors
                updated += 1

    # Update bills list with sponsor data
    bills = list(bill_map.values())

    with open(bills_file, 'w') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {updated} bills with sponsors")

    # Now update legislator counts
    print("\nUpdating legislator bill counts...")

    legislators_file = DATA_DIR / "legislators.json"
    with open(legislators_file, 'r') as f:
        legislators = json.load(f)

    # Reset counts
    for leg in legislators:
        leg['bills_count'] = 0
        leg['harmful_bills_count'] = 0
        leg['critical_bills'] = 0
        leg['high_bills'] = 0
        leg['bills_sponsored'] = []

    # Build name lookup (by last name)
    leg_by_lastname = {}
    for leg in legislators:
        last_name = leg.get('last_name') or ''
        if last_name:
            leg_by_lastname[last_name.lower()] = leg

    # Count bills per legislator
    for bill in bills:
        sponsors = bill.get('sponsors', [])
        threat_level = bill.get('threat_level', 'low')
        bill_number = bill.get('bill_number', '')

        for sponsor in sponsors:
            # Extract last name from "Representative Orcutt" or "Senator Smith"
            parts = sponsor.split()
            if len(parts) >= 2:
                last_name = parts[-1].lower()
                leg = leg_by_lastname.get(last_name)

                if leg:
                    leg['bills_count'] = leg.get('bills_count', 0) + 1
                    leg['bills_sponsored'].append(bill_number)

                    if threat_level in ['critical', 'high']:
                        leg['harmful_bills_count'] = leg.get('harmful_bills_count', 0) + 1
                        if threat_level == 'critical':
                            leg['critical_bills'] = leg.get('critical_bills', 0) + 1
                        else:
                            leg['high_bills'] = leg.get('high_bills', 0) + 1

    with open(legislators_file, 'w') as f:
        json.dump(legislators, f, indent=2, ensure_ascii=False)

    with_bills = sum(1 for leg in legislators if leg.get('bills_count', 0) > 0)
    print(f"Updated {with_bills} legislators with bill counts")


if __name__ == '__main__':
    main()
