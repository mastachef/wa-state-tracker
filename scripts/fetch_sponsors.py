#!/usr/bin/env python3
"""
Fetch bill sponsors from the WA State Legislature web services.

This script updates bills.json with sponsor information from the official
Washington State Legislature API.

Usage:
    python scripts/fetch_sponsors.py
"""

import json
import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

DATA_DIR = Path(__file__).parent.parent / "_data"
BIENNIUM = "2025-26"
REQUEST_DELAY = 0.2  # Be nice to the API


def get_sponsors(bill_number: str) -> list[str]:
    """Fetch sponsors for a bill from WA Legislature API."""
    # Parse bill number (e.g., "HB 1234" -> billId=1234)
    parts = bill_number.split()
    if len(parts) != 2:
        return []

    bill_id = parts[1]

    url = "https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetSponsors"
    params = {
        "biennium": BIENNIUM,
        "billId": bill_number.replace(" ", " ")  # Keep format like "HB 1234"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Parse XML response
        content = response.text

        # Extract sponsor names from XML
        # Format: <LongName>Representative Abbarno</LongName>
        sponsors = []
        import re
        # Use LongName for better readability
        names = re.findall(r'<LongName>([^<]+)</LongName>', content)
        sponsors = [name.strip() for name in names if name.strip()]

        return sponsors
    except Exception as e:
        # Silently fail for individual bills
        return []


def update_bills_with_sponsors():
    """Update bills.json with sponsor information."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("Error: bills.json not found")
        return 1

    with open(bills_file, 'r') as f:
        bills = json.load(f)

    print(f"Updating sponsors for {len(bills)} bills...")

    updated = 0
    for i, bill in enumerate(bills):
        bill_number = bill.get('bill_number', '')

        if i % 100 == 0:
            print(f"  Processing bill {i+1}/{len(bills)}...")

        sponsors = get_sponsors(bill_number)

        if sponsors:
            bill['sponsors'] = sponsors
            updated += 1

        time.sleep(REQUEST_DELAY)

    # Save updated bills
    with open(bills_file, 'w') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {updated} bills with sponsor information")
    return 0


def update_legislator_bill_counts():
    """Update legislators.json with bill counts based on sponsorship."""
    bills_file = DATA_DIR / "bills.json"
    legislators_file = DATA_DIR / "legislators.json"

    if not bills_file.exists() or not legislators_file.exists():
        print("Error: Required data files not found")
        return 1

    with open(bills_file, 'r') as f:
        bills = json.load(f)

    with open(legislators_file, 'r') as f:
        legislators = json.load(f)

    # Build a map of legislator names to their data
    # Need to handle various name formats
    leg_map = {}
    for leg in legislators:
        name = leg.get('name', '')
        # Store by full name
        leg_map[name.lower()] = leg
        # Also store by last name for matching "Rep. LastName" format
        last_name = leg.get('last_name', '').lower()
        if last_name:
            leg_map[last_name] = leg

    # Count bills per legislator
    for bill in bills:
        sponsors = bill.get('sponsors', [])
        threat_level = bill.get('threat_level', 'low')

        for sponsor in sponsors:
            # Try to match sponsor to legislator
            # Sponsors might be "Rep. John Smith" or "Sen. Jane Doe"
            sponsor_clean = sponsor.lower()

            # Remove title prefix
            for prefix in ['rep. ', 'sen. ', 'representative ', 'senator ']:
                if sponsor_clean.startswith(prefix):
                    sponsor_clean = sponsor_clean[len(prefix):]
                    break

            # Try full name match first
            matched_leg = leg_map.get(sponsor_clean)

            # Try last name match if no full match
            if not matched_leg:
                # Get last word as last name
                parts = sponsor_clean.split()
                if parts:
                    last_name = parts[-1]
                    matched_leg = leg_map.get(last_name)

            if matched_leg:
                # Increment bill count
                matched_leg['bills_count'] = matched_leg.get('bills_count', 0) + 1

                # Track harmful bills
                if threat_level in ['critical', 'high']:
                    matched_leg['harmful_bills_count'] = matched_leg.get('harmful_bills_count', 0) + 1
                    if threat_level == 'critical':
                        matched_leg['critical_bills'] = matched_leg.get('critical_bills', 0) + 1
                    else:
                        matched_leg['high_bills'] = matched_leg.get('high_bills', 0) + 1

    # Save updated legislators
    with open(legislators_file, 'w') as f:
        json.dump(legislators, f, indent=2, ensure_ascii=False)

    # Count how many have bills
    with_bills = sum(1 for leg in legislators if leg.get('bills_count', 0) > 0)
    print(f"Updated {with_bills} legislators with bill sponsorship data")

    return 0


if __name__ == '__main__':
    print("=" * 60)
    print("WA Bill Tracker - Sponsor Fetch")
    print("=" * 60 + "\n")

    # First fetch sponsors for all bills
    result = update_bills_with_sponsors()
    if result != 0:
        sys.exit(result)

    print("\n" + "=" * 60)
    print("Updating legislator bill counts...")
    print("=" * 60 + "\n")

    # Then update legislator counts
    result = update_legislator_bill_counts()
    sys.exit(result)
