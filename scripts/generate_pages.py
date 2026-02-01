#!/usr/bin/env python3
"""
Generate Jekyll markdown pages for each bill.

This script reads _data/bills.json and creates a markdown file in _bills/
for each bill. These pages will be built by Jekyll into the static site.

Usage:
    python scripts/generate_pages.py

The script reads featured.json to merge in any curated data like
plain_summary, why_featured, stance, urgency, and hearing_date.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"
BILLS_DIR = ROOT_DIR / "_bills"


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def load_json(filepath: Path) -> list | dict:
    """Load JSON from a file, returning empty list/dict if not found."""
    if not filepath.exists():
        return [] if filepath.name == "bills.json" else {}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def escape_yaml(value: str) -> str:
    """Escape a value for YAML front matter."""
    if not value:
        return '""'

    # Check if the value needs quoting
    needs_quotes = any([
        ':' in value,
        '#' in value,
        value.startswith(('-', '*', '&', '!', '|', '>', "'", '"', '%', '@', '`')),
        value.startswith('  '),
        value.endswith('  '),
        '\n' in value,
    ])

    if needs_quotes:
        # Escape double quotes and wrap in quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    return value


def generate_bill_page(bill: dict, featured_data: dict | None = None) -> str:
    """Generate markdown content for a bill page."""
    # Merge featured data if available
    if featured_data:
        bill = {**bill, **featured_data}

    # Build YAML front matter
    front_matter = ["---"]

    # Required fields
    front_matter.append(f"layout: bill")
    front_matter.append(f"bill_id: {bill.get('bill_id', '')}")
    front_matter.append(f"bill_number: {escape_yaml(bill.get('bill_number', ''))}")
    front_matter.append(f"title: {escape_yaml(bill.get('title', ''))}")

    # Optional string fields
    optional_fields = [
        "description",
        "status",
        "chamber",
        "committee",
        "introduced_date",
        "last_action",
        "last_action_date",
        "official_url",
        "plain_summary",
        "why_it_matters",
        "why_featured",
        "stance",
        "urgency",
        "hearing_date",
        "hearing_info",
        "ai_summary",
        "bill_analysis",
        "threat_level",
        "threat_label",
        "threat_score",
    ]

    for field in optional_fields:
        value = bill.get(field)
        if value:
            # Handle multiline content (like bill_analysis) with YAML block scalar
            if field == "bill_analysis" and '\n' in str(value):
                front_matter.append(f"{field}: |")
                for line in str(value).split('\n'):
                    front_matter.append(f"  {line}")
            else:
                front_matter.append(f"{field}: {escape_yaml(str(value))}")

    # Sponsors list
    sponsors = bill.get("sponsors", [])
    if sponsors:
        front_matter.append("sponsors:")
        for sponsor in sponsors:
            front_matter.append(f"  - {escape_yaml(sponsor)}")

    # History list
    history = bill.get("history", [])
    if history:
        front_matter.append("history:")
        for event in history:
            front_matter.append(f"  - date: {escape_yaml(event.get('date', ''))}")
            front_matter.append(f"    action: {escape_yaml(event.get('action', ''))}")

    front_matter.append("---")
    front_matter.append("")

    # Page content (can be empty since layout handles display)
    # Add any custom content that might be in the bill data
    content = bill.get("custom_content", "")

    return "\n".join(front_matter) + content


def generate_all_pages():
    """Generate markdown pages for all bills."""
    print("=" * 60)
    print("WA Bill Tracker - Page Generator")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Load data
    bills_file = DATA_DIR / "bills.json"
    featured_file = DATA_DIR / "featured.json"

    bills = load_json(bills_file)
    featured_list = load_json(featured_file)

    if not bills:
        print("No bills found in _data/bills.json")
        print("Run 'python scripts/fetch_bills.py' first to fetch bill data.")
        return 1

    # Create featured lookup by bill number
    featured_lookup = {}
    if isinstance(featured_list, list):
        for item in featured_list:
            bill_number = item.get("bill_number")
            if bill_number:
                featured_lookup[bill_number] = item

    print(f"Found {len(bills)} bills in bills.json")
    print(f"Found {len(featured_lookup)} featured bills in featured.json")

    # Create bills directory
    BILLS_DIR.mkdir(parents=True, exist_ok=True)

    # Track existing files for cleanup
    existing_files = set(BILLS_DIR.glob("*.md"))
    generated_files = set()

    # Generate pages
    for bill in bills:
        bill_number = bill.get("bill_number", "")
        if not bill_number:
            continue

        # Get featured data if available
        featured_data = featured_lookup.get(bill_number)

        # Generate filename from bill number
        filename = f"{slugify(bill_number)}.md"
        filepath = BILLS_DIR / filename

        # Generate content
        content = generate_bill_page(bill, featured_data)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        generated_files.add(filepath)

    print(f"\nGenerated {len(generated_files)} bill pages in _bills/")

    # Remove old files that are no longer needed
    stale_files = existing_files - generated_files
    if stale_files:
        print(f"\nRemoving {len(stale_files)} stale page(s)...")
        for filepath in stale_files:
            filepath.unlink()
            print(f"  Removed: {filepath.name}")

    print("\nPage generation complete!")
    return 0


def main():
    """Main entry point."""
    try:
        return generate_all_pages()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
