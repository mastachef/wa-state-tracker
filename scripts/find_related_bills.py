#!/usr/bin/env python3
"""
Find related bills based on title similarity and bill number patterns.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# Topic keywords for grouping
TOPIC_KEYWORDS = {
    'tax': ['tax', 'levy', 'excise', 'revenue'],
    'health': ['health', 'medical', 'hospital', 'insurance', 'medicare', 'medicaid'],
    'education': ['education', 'school', 'student', 'teacher', 'university', 'college'],
    'housing': ['housing', 'rent', 'landlord', 'tenant', 'homeless', 'affordable'],
    'environment': ['environment', 'climate', 'emission', 'pollution', 'clean energy'],
    'labor': ['labor', 'worker', 'wage', 'employment', 'union'],
    'public safety': ['police', 'firearm', 'gun', 'crime', 'prison', 'jail'],
    'transportation': ['transportation', 'highway', 'transit', 'traffic', 'vehicle'],
}


def extract_bill_number(bill_number: str) -> tuple:
    """Extract prefix and number from bill number."""
    match = re.match(r'([A-Z]+)\s*(\d+)', bill_number.upper())
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def get_words(text: str) -> set:
    """Extract meaningful words from text."""
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                 'could', 'should', 'may', 'might', 'must', 'shall', 'concerning',
                 'relating', 'regarding', 'making', 'providing', 'establishing'}

    words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
    return words - stopwords


def word_overlap(words1: set, words2: set) -> float:
    """Calculate word overlap ratio."""
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def find_topic(title: str) -> str:
    """Find the primary topic for a bill."""
    title_lower = title.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return topic
    return None


def find_related_bills():
    """Find and link related bills."""
    print("Finding related bills...")

    bills_file = DATA_DIR / "bills.json"
    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    print(f"Loaded {len(bills)} bills")

    # Build indices
    by_number = {}  # Map (prefix, number) -> bill
    by_topic = defaultdict(list)  # Map topic -> [bills]

    for bill in bills:
        bill_number = bill.get('bill_number', '')
        prefix, num = extract_bill_number(bill_number)

        if prefix and num:
            by_number[(prefix, num)] = bill

        title = bill.get('title', '')
        topic = find_topic(title)
        if topic:
            by_topic[topic].append(bill)

        # Pre-compute word set
        bill['_words'] = get_words(title)

    # Find relations
    related_count = 0
    clusters = defaultdict(set)

    for bill in bills:
        bill_number = bill.get('bill_number', '')
        prefix, num = extract_bill_number(bill_number)
        related = set()

        # 1. Find companion bills (HB <-> SB with same/similar number)
        if prefix in ('HB', 'SB') and num:
            companion_prefix = 'SB' if prefix == 'HB' else 'HB'
            # Check exact match and nearby numbers
            for offset in range(-10, 11):
                companion = by_number.get((companion_prefix, num + offset))
                if companion and companion['bill_number'] != bill_number:
                    # Check title similarity for nearby numbers
                    if offset == 0 or word_overlap(bill['_words'], companion['_words']) > 0.4:
                        related.add(companion['bill_number'])

        # 2. Find bills with similar titles (>50% word overlap)
        title = bill.get('title', '')
        topic = find_topic(title)

        if topic:
            cluster_key = f"{topic}"
            clusters[cluster_key].add(bill_number)

            for other in by_topic[topic]:
                if other['bill_number'] != bill_number:
                    overlap = word_overlap(bill['_words'], other['_words'])
                    if overlap > 0.5:
                        related.add(other['bill_number'])

        if related:
            bill['related_bills'] = sorted(list(related))[:10]  # Limit to 10
            related_count += 1
        else:
            bill['related_bills'] = []

    # Clean up temp data
    for bill in bills:
        if '_words' in bill:
            del bill['_words']

    print(f"Found relations for {related_count} bills")
    print(f"Generated {len(clusters)} bill clusters")

    # Save updated bills
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2)
    print(f"Updated {bills_file}")

    # Save clusters
    cluster_data = []
    for key, bill_numbers in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if len(bill_numbers) > 1:
            cluster_data.append({
                'topic': key,
                'count': len(bill_numbers),
                'bills': sorted(list(bill_numbers))[:20]
            })

    clusters_file = DATA_DIR / "bill_clusters.json"
    with open(clusters_file, 'w', encoding='utf-8') as f:
        json.dump(cluster_data, f, indent=2)
    print(f"Created {clusters_file}")

    print("\nLargest bill clusters:")
    for cluster in cluster_data[:5]:
        bills_preview = ', '.join(cluster['bills'][:3])
        print(f"  {cluster['topic']}: {cluster['count']} bills - {bills_preview}...")

    return 0


if __name__ == "__main__":
    exit(find_related_bills())
