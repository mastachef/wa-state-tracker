#!/usr/bin/env python3
"""
Detect amendments in Washington State bills.
Marks bills that have been amended based on status, title, and history.
"""

import json
import re
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"


def detect_amendments():
    """Detect and mark amended bills."""
    print("=" * 60)
    print("WA Bill Tracker - Amendment Detection")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    bills_file = DATA_DIR / "bills.json"
    if not bills_file.exists():
        print("No bills.json found")
        return 1

    print("\nLoading bills...")
    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    print(f"Loaded {len(bills)} bills")
    print("\nDetecting amendments...")

    amended_count = 0
    detection_types = {
        'engrossed': 0,
        'substitute': 0,
        'history': 0
    }

    amendment_patterns = [
        r'amended',
        r'substitute',
        r'striking amendment',
        r'engrossed',
        r'floor amendment'
    ]

    for bill in bills:
        amended = False
        amendment_count = 0

        # Check status for "Engrossed"
        status = bill.get('status', '').lower()
        if 'engrossed' in status:
            amended = True
            detection_types['engrossed'] += 1

        # Check title for "substitute"
        title = bill.get('title', '').lower()
        if 'substitute' in title:
            amended = True
            detection_types['substitute'] += 1

        # Check history for amendment actions
        history = bill.get('history', [])
        for event in history:
            action = event.get('action', '').lower()
            for pattern in amendment_patterns:
                if re.search(pattern, action):
                    amendment_count += 1
                    if not amended:
                        amended = True
                        detection_types['history'] += 1
                    break

        if amended:
            bill['amended'] = True
            bill['amendment_count'] = max(1, amendment_count)
            amended_count += 1
        else:
            bill['amended'] = False
            bill['amendment_count'] = 0

    print(f"\nAmendment Detection Results:")
    print("-" * 40)
    print(f"Total bills:     {len(bills)}")
    print(f"Amended:         {amended_count}")
    print(f"Not amended:     {len(bills) - amended_count}")
    print(f"\nBy detection type:")
    print(f"  Engrossed status:  {detection_types['engrossed']}")
    print(f"  Substitute title:  {detection_types['substitute']}")
    print(f"  History actions:   {detection_types['history']}")

    print("\nSaving updated bills...")
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2)

    print(f"Saved to {bills_file}")
    print("\n" + "=" * 60)
    print("WATCHDOG NOTE: Amendments are how politicians sneak in")
    print("unpopular provisions. Always read the LATEST version!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(detect_amendments())
