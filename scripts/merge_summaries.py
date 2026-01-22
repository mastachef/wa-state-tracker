#!/usr/bin/env python3
"""
Merge AI summaries from batch files back into bills.json
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"
TEMP_DIR = ROOT_DIR / "_temp_batches"


def merge_summaries():
    """Merge all batch summaries into bills.json."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Create lookup by bill_id
    bills_by_id = {b['bill_id']: b for b in bills}

    # Load and merge all batch summaries
    merged_count = 0
    for batch_file in sorted(TEMP_DIR.glob("batch_*_summaries.json")):
        print(f"Processing {batch_file.name}...")
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                summaries = json.load(f)

            for item in summaries:
                bill_id = item.get('bill_id')
                summary = item.get('ai_summary')

                if bill_id and summary and bill_id in bills_by_id:
                    bills_by_id[bill_id]['ai_summary'] = summary
                    merged_count += 1
        except Exception as e:
            print(f"  Error processing {batch_file.name}: {e}")

    # Write back to bills.json
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2)

    print(f"\nMerged {merged_count} AI summaries into bills.json")
    return 0


if __name__ == "__main__":
    exit(merge_summaries())
