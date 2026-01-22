#!/usr/bin/env python3
"""
Fetch Washington State legislator data from official sources.
Combines WA Legislature Web Services with bill sponsorship data.
"""

import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# WA Legislature Web Services
WA_LEG_BASE = "https://wslwebservices.leg.wa.gov"
BIENNIUM = "2025-26"


def fetch_xml(url: str) -> ET.Element:
    """Fetch XML from URL and return root element."""
    print(f"  Fetching: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return ET.fromstring(response.content)


def get_photo_url(first_name: str, last_name: str, chamber: str) -> str:
    """Generate photo URL for legislator.

    WA Legislature photos follow pattern:
    https://leg.wa.gov/house/representatives/PublishingImages/[LastName].jpg
    https://leg.wa.gov/senate/senators/PublishingImages/[LastName].jpg

    Falls back to UI Avatars service for placeholder.
    """
    # Generate initials-based placeholder that always works
    initials = f"{first_name[0] if first_name else 'X'}{last_name[0] if last_name else 'X'}"
    placeholder = f"https://ui-avatars.com/api/?name={first_name}+{last_name}&background=1e4470&color=fff&size=200"
    return placeholder


def parse_sponsor(elem) -> dict:
    """Parse a sponsor XML element into a dict."""
    # Handle namespaces in the XML
    ns = {'': 'http://WSLWebServices.leg.wa.gov/'}

    def get_text(tag):
        # Try with namespace first, then without
        el = elem.find(tag, ns) if ns else elem.find(tag)
        if el is None:
            el = elem.find(tag)
        if el is None:
            # Try lowercase
            el = elem.find(tag.lower())
        return el.text if el is not None else ""

    first_name = get_text('FirstName')
    last_name = get_text('LastName')
    agency = get_text('Agency')

    return {
        'id': get_text('Id'),
        'name': get_text('Name') or get_text('LongName'),
        'first_name': first_name,
        'last_name': last_name,
        'party': get_text('Party'),
        'district': get_text('District'),
        'email': get_text('Email'),
        'phone': get_text('Phone'),
        'agency': agency,
        'photo_url': get_photo_url(first_name, last_name, agency),
    }


def fetch_legislators():
    """Fetch all current WA State legislators."""
    print("=" * 60)
    print("WA Bill Tracker - Fetching Legislator Data")
    print("=" * 60)

    legislators = {}

    # Fetch House members
    print("\nFetching House members...")
    try:
        house_url = f"{WA_LEG_BASE}/SponsorService.asmx/GetHouseSponsors?biennium={BIENNIUM}"
        root = fetch_xml(house_url)

        for member in root.iter():
            if 'Member' in member.tag or 'Sponsor' in member.tag:
                data = parse_sponsor(member)
                if data.get('name'):
                    data['chamber'] = 'House'
                    data['title'] = 'Representative'
                    legislators[data['name']] = data

        print(f"  Found {len([l for l in legislators.values() if l['chamber'] == 'House'])} House members")
    except Exception as e:
        print(f"  Error fetching House: {e}")

    # Fetch Senate members
    print("\nFetching Senate members...")
    try:
        senate_url = f"{WA_LEG_BASE}/SponsorService.asmx/GetSenateSponsors?biennium={BIENNIUM}"
        root = fetch_xml(senate_url)

        for member in root.iter():
            if 'Member' in member.tag or 'Sponsor' in member.tag:
                data = parse_sponsor(member)
                if data.get('name'):
                    data['chamber'] = 'Senate'
                    data['title'] = 'Senator'
                    legislators[data['name']] = data

        print(f"  Found {len([l for l in legislators.values() if l['chamber'] == 'Senate'])} Senate members")
    except Exception as e:
        print(f"  Error fetching Senate: {e}")

    # If web services failed, try parsing from bills
    if len(legislators) == 0:
        print("\nWeb services unavailable, extracting from bill data...")
        legislators = extract_sponsors_from_bills()
    else:
        # Enrich with bill sponsorship data
        print("\nEnriching with bill sponsorship data...")
        legislators = enrich_with_bills(legislators)

    # Convert to list and sort
    leg_list = list(legislators.values())
    leg_list.sort(key=lambda x: (x.get('chamber', ''), x.get('last_name', '') or x.get('name', '')))

    # Save to file
    output_file = DATA_DIR / "legislators.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(leg_list, f, indent=2)

    print(f"\nSaved {len(leg_list)} legislators to {output_file}")

    # Print summary
    house_count = len([l for l in leg_list if l.get('chamber') == 'House'])
    senate_count = len([l for l in leg_list if l.get('chamber') == 'Senate'])
    dem_count = len([l for l in leg_list if l.get('party') == 'D'])
    rep_count = len([l for l in leg_list if l.get('party') == 'R'])

    print(f"\nSummary:")
    print(f"  House: {house_count}")
    print(f"  Senate: {senate_count}")
    print(f"  Democrats: {dem_count}")
    print(f"  Republicans: {rep_count}")

    return 0


def extract_sponsors_from_bills() -> dict:
    """Extract sponsor information from bills.json."""
    bills_file = DATA_DIR / "bills.json"
    if not bills_file.exists():
        print("No bills.json found")
        return {}

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    legislators = {}

    for bill in bills:
        sponsors = bill.get('sponsors', [])
        if isinstance(sponsors, str):
            sponsors = [sponsors]

        chamber = bill.get('chamber', '')

        for sponsor in sponsors:
            if isinstance(sponsor, dict):
                name = sponsor.get('name', '')
            else:
                name = sponsor

            if name and name not in legislators:
                # Try to parse name
                parts = name.split()
                first_name = parts[0] if parts else ''
                last_name = parts[-1] if len(parts) > 1 else ''

                legislators[name] = {
                    'name': name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'chamber': chamber,
                    'title': 'Representative' if chamber == 'House' else 'Senator' if chamber == 'Senate' else '',
                    'party': '',
                    'district': '',
                    'email': '',
                    'phone': '',
                    'bills_sponsored': [],
                    'bills_count': 0,
                    'harmful_bills_count': 0,
                    'threat_score_total': 0
                }

    return legislators


def enrich_with_bills(legislators: dict) -> dict:
    """Add bill sponsorship stats to legislators."""
    bills_file = DATA_DIR / "bills.json"
    if not bills_file.exists():
        return legislators

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Initialize stats for all legislators
    for leg in legislators.values():
        leg['bills_sponsored'] = []
        leg['bills_count'] = 0
        leg['harmful_bills_count'] = 0
        leg['threat_score_total'] = 0
        leg['critical_bills'] = 0
        leg['high_bills'] = 0

    # Track sponsorships
    harmful_levels = {'critical', 'high'}

    for bill in bills:
        sponsors = bill.get('sponsors', [])
        if isinstance(sponsors, str):
            sponsors = [sponsors]

        bill_number = bill.get('bill_number', '')
        threat_level = bill.get('threat_level', 'moderate')
        threat_score = bill.get('threat_score', 0)

        for sponsor in sponsors:
            if isinstance(sponsor, dict):
                name = sponsor.get('name', '')
            else:
                name = sponsor

            # Try to match legislator
            matched = None
            if name in legislators:
                matched = legislators[name]
            else:
                # Try partial match
                for leg_name, leg in legislators.items():
                    if name.lower() in leg_name.lower() or leg_name.lower() in name.lower():
                        matched = leg
                        break

            if matched:
                matched['bills_sponsored'].append(bill_number)
                matched['bills_count'] += 1
                matched['threat_score_total'] += threat_score

                if threat_level in harmful_levels:
                    matched['harmful_bills_count'] += 1

                if threat_level == 'critical':
                    matched['critical_bills'] += 1
                elif threat_level == 'high':
                    matched['high_bills'] += 1

    # Calculate average threat score
    for leg in legislators.values():
        if leg['bills_count'] > 0:
            leg['avg_threat_score'] = round(leg['threat_score_total'] / leg['bills_count'], 2)
        else:
            leg['avg_threat_score'] = 0

        # Limit stored bill list to top 20
        leg['bills_sponsored'] = leg['bills_sponsored'][:20]

    return legislators


if __name__ == "__main__":
    exit(fetch_legislators())
