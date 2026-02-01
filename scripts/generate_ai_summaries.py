#!/usr/bin/env python3
"""
Generate AI summaries for Washington State bills using OpenRouter API.

This script analyzes bills through a constitutional/liberty-focused lens,
helping identify deceptive or overreaching legislation.

Features:
- Only processes bills without existing ai_summary (cost-effective)
- Uses threat_level and concerns from scoring as context
- Rate limiting to stay within free tier (20 req/min)
- Graceful error handling (missing summaries don't break site)

Usage:
    python scripts/generate_ai_summaries.py          # Process all bills needing summaries
    python scripts/generate_ai_summaries.py --test   # Test with sample data (no API calls)
    python scripts/generate_ai_summaries.py --limit 5  # Process only 5 bills

Environment Variables:
    OPENROUTER_API_KEY: Your OpenRouter API key (required for actual API calls)
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path

# Try to import requests, handle gracefully if not available
try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free models to try in order of preference
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
]

# Rate limiting: 20 requests per minute for free tier
RATE_LIMIT_DELAY = 3.0  # seconds between requests (20/min = 3s each)

# Analysis prompt template
ANALYSIS_PROMPT = """You are a constitutional watchdog analyzing Washington State legislation from an American nationalist, pro-republic perspective.

Your core principles:
- The Constitution is the supreme law, not a living document to be reinterpreted
- Government power must be limited and enumerated; all else belongs to states and people
- Individual liberty and property rights are sacred and pre-exist government
- Bureaucratic expansion is inherently suspect; the administrative state undermines republican government
- Taxation is confiscation; new taxes/fees require extreme justification
- The Second Amendment means what it says; any infringement is unconstitutional
- Free speech includes unpopular speech; government has no role policing expression
- States created the federal government, not the reverse; federal overreach must be resisted

Analyze this bill for:
1. HIDDEN COSTS: Unfunded mandates, new taxes/fees, spending increases, economic burden
2. RIGHTS VIOLATIONS: Infringements on speech, arms, property, privacy, due process, religious liberty
3. GOVERNMENT EXPANSION: New agencies, bureaucrats, regulations, reporting requirements, enforcement powers
4. DECEPTIVE LANGUAGE: Vague terms hiding broad powers, feel-good titles masking control, undefined "emergency" powers
5. CONSTITUTIONAL ISSUES: Enumerated powers exceeded, improper delegation to agencies, due process violations

Bill: {title}
Description: {description}
Threat Level: {threat_level}
Red Flags Identified: {concerns}

Write a 2-3 sentence plain-English summary for citizens. Be blunt about what this bill actually does. Call out deceptive framing. If it expands liberty or reduces government, say so clearly."""


def get_api_key():
    """Get OpenRouter API key from environment."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not set. Skipping AI summary generation.")
        return None
    return api_key


def generate_summary(bill: dict, api_key: str, model: str = None) -> str | None:
    """
    Generate an AI summary for a bill using OpenRouter API.

    Returns the summary text or None if generation fails.
    """
    if model is None:
        model = FREE_MODELS[0]

    # Build the prompt with bill context
    title = bill.get("title", "Unknown")
    description = bill.get("description", "")

    # If no description, use title and note it
    if not description:
        description = f"(No official description available. Analyze based on title: {title})"

    prompt = ANALYSIS_PROMPT.format(
        title=title,
        description=description,
        threat_level=bill.get("threat_label", "Unknown"),
        concerns=", ".join(bill.get("concerns", [])) or "None identified by keyword scan"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/wa-state-tracker",
        "X-Title": "WA State Bill Tracker"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.3  # Lower temperature for more consistent analysis
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
        elif response.status_code == 429:
            print(f"  Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            return None
        else:
            print(f"  API error {response.status_code}: {response.text[:100]}")
            return None

    except requests.exceptions.Timeout:
        print(f"  Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Request error: {e}")
        return None

    return None


def get_test_summary(bill: dict) -> str:
    """Generate a test summary without API calls."""
    threat_level = bill.get("threat_level", "unknown")
    title = bill.get("title", "Unknown bill")

    if threat_level == "critical":
        return f"[TEST] This bill poses a direct threat to constitutional rights or dramatically expands state power. The bureaucracy wins, citizens lose. Read the full text - the title '{title[:40]}' likely obscures the real agenda."
    elif threat_level == "high":
        return f"[TEST] Another expansion of the administrative state. Expect new regulations, compliance burdens, and government intrusion. Washington taxpayers will foot the bill."
    elif threat_level == "beneficial":
        return f"[TEST] A rare win for liberty. This bill appears to roll back government overreach or protect individual rights. Worth supporting."
    else:
        return f"[TEST] Requires scrutiny. Government rarely passes 'neutral' legislation - look for hidden mandates, fee increases, or regulatory expansion buried in the text."


def process_bills(test_mode: bool = False, limit: int = None):
    """
    Process bills and generate AI summaries for those without them.

    Args:
        test_mode: If True, use test summaries instead of API calls
        limit: Maximum number of bills to process (None for all)
    """
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    # Load bills
    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Filter bills that need summaries
    bills_needing_summary = [
        b for b in bills
        if not b.get("ai_summary")
    ]

    print(f"Found {len(bills_needing_summary)} bills without AI summaries (of {len(bills)} total)")

    if not bills_needing_summary:
        print("All bills already have summaries. Nothing to do.")
        return 0

    # Apply limit if specified
    if limit:
        bills_needing_summary = bills_needing_summary[:limit]
        print(f"Processing limited to {limit} bills")

    # Get API key (unless test mode)
    api_key = None
    if not test_mode:
        api_key = get_api_key()
        if not api_key:
            print("No API key available. Use --test for test mode.")
            return 0  # Not an error, just skip

    # Process bills
    summaries_generated = 0
    errors = 0

    for i, bill in enumerate(bills_needing_summary):
        bill_number = bill.get("bill_number", "Unknown")
        print(f"[{i+1}/{len(bills_needing_summary)}] Processing {bill_number}...")

        if test_mode:
            summary = get_test_summary(bill)
        else:
            summary = generate_summary(bill, api_key)

            # Try fallback models if first one fails
            if summary is None:
                for fallback_model in FREE_MODELS[1:]:
                    print(f"  Trying fallback model: {fallback_model}")
                    summary = generate_summary(bill, api_key, fallback_model)
                    if summary:
                        break

        if summary:
            # Find and update the bill in the main list
            for b in bills:
                if b.get("bill_id") == bill.get("bill_id"):
                    b["ai_summary"] = summary
                    break
            summaries_generated += 1
            print(f"  Generated summary ({len(summary)} chars)")
        else:
            errors += 1
            print(f"  Failed to generate summary")

        # Rate limiting (skip in test mode)
        if not test_mode and i < len(bills_needing_summary) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    # Save updated bills
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)

    print(f"\nSummary Generation Complete:")
    print(f"  Generated: {summaries_generated}")
    print(f"  Errors: {errors}")
    print(f"  Updated: {bills_file}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI summaries for Washington State bills"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test summaries instead of API calls"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of bills to process"
    )

    args = parser.parse_args()

    return process_bills(test_mode=args.test, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
