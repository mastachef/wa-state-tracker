#!/usr/bin/env python3
"""
Generate individual legislator profile pages from legislators.json.
"""

import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"
LEGISLATORS_DIR = ROOT_DIR / "_legislators"


def slugify(name: str) -> str:
    """Convert name to URL-safe slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def format_currency(amount: float) -> str:
    """Format amount as currency."""
    if amount >= 1000000:
        return f"${amount/1000000:.1f}M"
    elif amount >= 1000:
        return f"${amount/1000:.0f}K"
    else:
        return f"${amount:.0f}"


def generate_legislator_pages():
    """Generate markdown pages for each legislator."""
    print("=" * 60)
    print("WA Bill Tracker - Generating Legislator Pages")
    print("=" * 60)

    leg_file = DATA_DIR / "legislators.json"
    if not leg_file.exists():
        print("No legislators.json found")
        return 1

    with open(leg_file, 'r', encoding='utf-8') as f:
        legislators = json.load(f)

    # Create legislators directory
    LEGISLATORS_DIR.mkdir(exist_ok=True)

    # Clean old files
    for old_file in LEGISLATORS_DIR.glob("*.md"):
        old_file.unlink()

    count = 0
    for leg in legislators:
        name = leg.get('name', '')
        if not name:
            continue

        slug = slugify(name)
        filename = f"{slug}.md"

        # Build frontmatter
        party_full = 'Democrat' if leg.get('party') == 'D' else 'Republican' if leg.get('party') == 'R' else leg.get('party', 'Unknown')
        title = leg.get('title', 'Legislator')
        chamber = leg.get('chamber', '')
        district = leg.get('district', '')

        total_raised = leg.get('total_raised', 0)
        bills_count = leg.get('bills_count', 0)
        harmful_count = leg.get('harmful_bills_count', 0)
        critical_count = leg.get('critical_bills', 0)
        high_count = leg.get('high_bills', 0)
        avg_threat = leg.get('avg_threat_score', 0)

        content = f"""---
layout: legislator
name: "{name}"
title: "{title}"
chamber: "{chamber}"
district: "{district}"
party: "{leg.get('party', '')}"
party_full: "{party_full}"
email: "{leg.get('email', '')}"
phone: "{leg.get('phone', '')}"
legislator_id: "{leg.get('id', '')}"
total_raised: {total_raised}
total_raised_formatted: "{format_currency(total_raised)}"
bills_count: {bills_count}
harmful_bills_count: {harmful_count}
critical_bills: {critical_count}
high_bills: {high_count}
avg_threat_score: {avg_threat}
contribution_count: {leg.get('contribution_count', 0)}
permalink: /legislators/{slug}/
---
"""

        # Write file
        filepath = LEGISLATORS_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        count += 1

    print(f"\nGenerated {count} legislator pages in {LEGISLATORS_DIR}")

    # Create legislator index data for sorting
    index_data = []
    for leg in legislators:
        if leg.get('name'):
            index_data.append({
                'name': leg['name'],
                'slug': slugify(leg['name']),
                'party': leg.get('party', ''),
                'chamber': leg.get('chamber', ''),
                'district': leg.get('district', ''),
                'total_raised': leg.get('total_raised', 0),
                'bills_count': leg.get('bills_count', 0),
                'harmful_bills_count': leg.get('harmful_bills_count', 0),
                'avg_threat_score': leg.get('avg_threat_score', 0)
            })

    index_file = DATA_DIR / "legislators_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)

    print(f"Created index at {index_file}")

    return 0


if __name__ == "__main__":
    exit(generate_legislator_pages())
