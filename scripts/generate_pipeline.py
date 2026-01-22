#!/usr/bin/env python3
"""
Generate legislative pipeline data showing where bills are in the process.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# Pipeline stages in order
STAGES = [
    {'id': 'introduced', 'name': 'Introduced', 'patterns': ['introduced', 'prefiled', 'first reading']},
    {'id': 'passed_origin', 'name': 'Passed Origin Chamber', 'patterns': ['passed house', 'passed senate', 'third reading']},
    {'id': 'passed_both', 'name': 'Passed Both Chambers', 'patterns': ['passed', 'concurred']},
    {'id': 'enrolled', 'name': 'Enrolled', 'patterns': ['enrolled']},
    {'id': 'signed', 'name': 'Signed into Law', 'patterns': ['signed', 'enacted', 'chapter']},
]

DEAD_PATTERNS = ['dead', 'failed', 'vetoed', 'indefinitely postponed']


def get_stage(bill: dict) -> str:
    """Determine which pipeline stage a bill is in."""
    status = (bill.get('status') or '').lower()
    last_action = (bill.get('last_action') or '').lower()

    combined = status + ' ' + last_action

    # Check for dead bills first
    for pattern in DEAD_PATTERNS:
        if pattern in combined:
            return 'dead'

    # Check stages in reverse order (furthest along first)
    for stage in reversed(STAGES):
        for pattern in stage['patterns']:
            if pattern in combined:
                return stage['id']

    return 'introduced'  # Default


def generate_pipeline():
    """Generate pipeline analysis data."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Count bills at each stage
    stage_counts = {s['id']: {'total': 0, 'harmful': 0, 'bills': []} for s in STAGES}
    stage_counts['dead'] = {'total': 0, 'harmful': 0, 'bills': []}

    harmful_levels = {'critical', 'high'}

    for bill in bills:
        stage = get_stage(bill)
        threat_level = bill.get('threat_level', 'moderate')
        is_harmful = threat_level in harmful_levels

        stage_counts[stage]['total'] += 1
        if is_harmful:
            stage_counts[stage]['harmful'] += 1
            # Track harmful bills for "bills to watch"
            if stage not in ['introduced', 'dead']:
                stage_counts[stage]['bills'].append({
                    'bill_number': bill.get('bill_number'),
                    'title': bill.get('title', '')[:100],
                    'threat_level': threat_level,
                    'status': bill.get('status'),
                    'last_action_date': bill.get('last_action_date')
                })

    # Build output
    pipeline_data = []
    for stage in STAGES:
        stage_id = stage['id']
        pipeline_data.append({
            'id': stage_id,
            'name': stage['name'],
            'total': stage_counts[stage_id]['total'],
            'harmful': stage_counts[stage_id]['harmful']
        })

    # Get bills to watch (harmful bills furthest along)
    bills_to_watch = []
    for stage in reversed(STAGES):
        bills_to_watch.extend(stage_counts[stage['id']]['bills'])
        if len(bills_to_watch) >= 20:
            break
    bills_to_watch = bills_to_watch[:20]

    output = {
        'pipeline': pipeline_data,
        'dead': stage_counts['dead'],
        'bills_to_watch': bills_to_watch,
        'summary': {
            'total_active': sum(s['total'] for s in pipeline_data),
            'total_harmful_active': sum(s['harmful'] for s in pipeline_data),
            'total_dead': stage_counts['dead']['total']
        }
    }

    output_file = DATA_DIR / "pipeline.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"Analyzing {len(bills)} bills...\n")
    print("Pipeline Analysis:")
    print("-" * 50)
    for stage in pipeline_data:
        print(f"  {stage['name']:25} {stage['total']:4} bills  ({stage['harmful']} harmful)")
    print("-" * 50)
    print(f"  Dead/Failed               {stage_counts['dead']['total']:4} bills\n")
    print(f"Total active harmful bills: {output['summary']['total_harmful_active']}")
    print(f"Bills to watch (top threats): {len(bills_to_watch)}")
    print(f"\nSaved to {output_file}")

    return 0


if __name__ == "__main__":
    exit(generate_pipeline())
