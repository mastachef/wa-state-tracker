#!/usr/bin/env python3
"""
Analyze full bill text for Washington State legislation.

This script fetches the actual bill text (not just descriptions) and uses AI
to provide deep constitutional analysis, exposing hidden mandates, deceptive
language, and government overreach.

Features:
- Fetches bill text from LegiScan API or WA Legislature website
- Prioritizes actionable bills (not yet passed)
- Focuses on high-threat bills first
- Constitutional/liberty-focused AI analysis
- Extracts what the bill ACTUALLY does vs what it claims

Usage:
    python scripts/analyze_bill_text.py                    # Analyze high-priority bills
    python scripts/analyze_bill_text.py --limit 10         # Limit to 10 bills
    python scripts/analyze_bill_text.py --bill "HB 1234"   # Analyze specific bill
    python scripts/analyze_bill_text.py --test             # Test mode (no API calls)

Environment Variables:
    LEGISCAN_API_KEY: LegiScan API key for fetching bill text
    OPENROUTER_API_KEY: OpenRouter API key for AI analysis
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Run: pip install requests")
    sys.exit(1)

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"

# API Configuration
LEGISCAN_BASE_URL = "https://api.legiscan.com/"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Rate limiting
LEGISCAN_DELAY = 2.0  # seconds between LegiScan requests
OPENROUTER_DELAY = 3.0  # seconds between OpenRouter requests (free tier)

# AI Models (free tier)
AI_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
]

# Deep analysis prompt - constitutional watchdog perspective
ANALYSIS_PROMPT = """You are a constitutional analyst examining Washington State legislation. Your job is to cut through legislative doublespeak and explain what bills ACTUALLY do.

Your principles:
- The Constitution means what it says - not what judges reinterpret it to mean
- All government power not explicitly granted is reserved to states and people
- Individual rights (speech, arms, property, privacy, due process) are non-negotiable
- "Public safety" and "general welfare" are not blank checks for unlimited power
- Vague language in laws is a feature, not a bug - it grants bureaucrats discretion
- Follow the money: who benefits, who pays, who gains power

BILL NUMBER: {bill_number}
BILL TITLE: {title}

FULL BILL TEXT:
{bill_text}

Analyze this bill and provide:

## WHAT IT ACTUALLY DOES
In 2-3 plain English sentences, explain what this bill does in practice. Cut through the legislative jargon. If the title is misleading, say so.

## RED FLAGS
List specific concerning provisions (quote the actual text when possible):
- Hidden mandates or requirements
- New government powers or agencies
- Vague language granting broad discretion
- Penalties, fines, or enforcement mechanisms
- Unfunded mandates on businesses/individuals
- Constitutional concerns

## WHO BENEFITS / WHO PAYS
- Who gains power or money from this bill?
- Who bears the costs or loses freedom?
- Any special interests behind this?

## DECEPTION RATING
Rate 1-5 how deceptive the bill title/framing is vs what it actually does:
1 = Honest and straightforward
5 = Title is opposite of what bill does

## BOTTOM LINE
One sentence a citizen needs to know about this bill.

Be direct. Be specific. Quote the bill text when exposing problems."""


def get_legiscan_key():
    """Get LegiScan API key."""
    key = os.environ.get("LEGISCAN_API_KEY")
    if not key:
        print("Warning: LEGISCAN_API_KEY not set")
    return key


def get_openrouter_key():
    """Get OpenRouter API key."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Warning: OPENROUTER_API_KEY not set")
    return key


def fetch_bill_text_legiscan(bill_id: int, api_key: str) -> str | None:
    """Fetch bill text from LegiScan API."""
    try:
        # First get bill details to find text document ID
        params = {"key": api_key, "op": "getBill", "id": bill_id}
        response = requests.get(LEGISCAN_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ERROR":
            print(f"    LegiScan error: {data.get('alert', {}).get('message', 'Unknown')}")
            return None

        bill = data.get("bill", {})
        texts = bill.get("texts", [])

        if not texts:
            print(f"    No text documents available")
            return None

        # Get the most recent text (last in list, usually the enrolled/latest version)
        latest_text = texts[-1]
        doc_id = latest_text.get("doc_id")

        if not doc_id:
            return None

        time.sleep(LEGISCAN_DELAY)

        # Fetch the actual text document
        params = {"key": api_key, "op": "getBillText", "id": doc_id}
        response = requests.get(LEGISCAN_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ERROR":
            return None

        text_data = data.get("text", {})
        doc_content = text_data.get("doc")

        if doc_content:
            # LegiScan returns base64 encoded content
            try:
                decoded = base64.b64decode(doc_content).decode('utf-8', errors='ignore')
                # Clean up HTML/XML tags if present
                cleaned = re.sub(r'<[^>]+>', ' ', decoded)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                return cleaned
            except Exception as e:
                print(f"    Error decoding text: {e}")
                return None

        return None

    except requests.exceptions.RequestException as e:
        print(f"    Request error: {e}")
        return None


def fetch_bill_text_wa_leg(bill_number: str) -> str | None:
    """Fetch bill text from WA Legislature website as fallback."""
    try:
        # Parse bill number (e.g., "HB 1234" -> bill_num=1234, prefix=HB)
        match = re.match(r'([A-Z]+)\s*(\d+)', bill_number.upper())
        if not match:
            return None

        prefix, num = match.groups()

        # WA Legislature URL pattern
        # https://lawfilesext.leg.wa.gov/biennium/2025-26/Htm/Bills/House%20Bills/1234.htm
        chamber = "House" if prefix.startswith("H") else "Senate"
        bill_type = "Bills"

        if "JR" in prefix:
            bill_type = "Joint%20Resolutions"
        elif "CR" in prefix:
            bill_type = "Concurrent%20Resolutions"
        elif "R" in prefix and "J" not in prefix:
            bill_type = "Resolutions"

        url = f"https://lawfilesext.leg.wa.gov/biennium/2025-26/Htm/Bills/{chamber}%20{bill_type}/{num}.htm"

        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Parse HTML to extract text
            html = response.text
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        return None

    except Exception as e:
        print(f"    WA Leg fetch error: {e}")
        return None


def analyze_with_ai(bill_number: str, title: str, bill_text: str, api_key: str) -> str | None:
    """Analyze bill text with AI."""
    # Truncate bill text if too long (keep first 60k chars for context window)
    max_text_length = 60000
    if len(bill_text) > max_text_length:
        bill_text = bill_text[:max_text_length] + "\n\n[TEXT TRUNCATED - Bill continues...]"

    prompt = ANALYSIS_PROMPT.format(
        bill_number=bill_number,
        title=title,
        bill_text=bill_text
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/wa-state-tracker",
        "X-Title": "WA State Bill Tracker"
    }

    for model in AI_MODELS:
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.3
            }

            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=120  # Longer timeout for long analysis
            )

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            elif response.status_code == 429:
                print(f"    Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            else:
                print(f"    AI error ({model}): {response.status_code}")
                continue

        except Exception as e:
            print(f"    AI error ({model}): {e}")
            continue

    return None


def get_priority_bills(bills: list) -> list:
    """Get bills prioritized for analysis: actionable + high threat first."""
    # Filter to actionable bills (not passed/dead)
    passed_statuses = ['Passed', 'Signed', 'Enacted', 'Vetoed', 'Dead', 'Failed']
    actionable = [b for b in bills if b.get('status') not in passed_statuses]

    # Filter to those without deep analysis
    needs_analysis = [b for b in actionable if not b.get('bill_analysis')]

    # Sort by threat level (critical first, then high, etc.)
    threat_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3, 'beneficial': 4, 'unknown': 5}
    needs_analysis.sort(key=lambda b: threat_order.get(b.get('threat_level', 'unknown'), 5))

    return needs_analysis


def process_bills(limit: int = None, specific_bill: str = None, test_mode: bool = False):
    """Process bills and generate deep analysis."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    print(f"Loaded {len(bills)} bills")

    # Get API keys
    legiscan_key = get_legiscan_key()
    openrouter_key = get_openrouter_key()

    if not test_mode and (not legiscan_key or not openrouter_key):
        print("Missing API keys. Use --test for test mode.")
        return 1

    # Determine which bills to process
    if specific_bill:
        to_process = [b for b in bills if b.get('bill_number') == specific_bill]
        if not to_process:
            print(f"Bill {specific_bill} not found")
            return 1
    else:
        to_process = get_priority_bills(bills)

    print(f"Bills to analyze: {len(to_process)}")

    if limit:
        to_process = to_process[:limit]
        print(f"Limited to: {limit}")

    # Process each bill
    analyzed = 0
    errors = 0

    for i, bill in enumerate(to_process):
        bill_number = bill.get('bill_number', 'Unknown')
        bill_id = bill.get('bill_id')
        title = bill.get('title', '')

        print(f"\n[{i+1}/{len(to_process)}] Analyzing {bill_number}...")
        print(f"  Title: {title[:60]}...")
        print(f"  Threat: {bill.get('threat_level', 'unknown')}")

        if test_mode:
            # Generate test analysis
            analysis = f"""## WHAT IT ACTUALLY DOES
[TEST MODE] This bill would need full text analysis to determine actual impact.

## RED FLAGS
- Unable to analyze without bill text (test mode)

## WHO BENEFITS / WHO PAYS
- Analysis requires full bill text

## DECEPTION RATING
3 - Cannot determine without text analysis

## BOTTOM LINE
[TEST] Run with API keys to get real analysis of {bill_number}."""
        else:
            # Fetch bill text
            print(f"  Fetching text...")
            bill_text = None

            if legiscan_key and bill_id:
                bill_text = fetch_bill_text_legiscan(bill_id, legiscan_key)
                time.sleep(LEGISCAN_DELAY)

            if not bill_text:
                print(f"  Trying WA Legislature website...")
                bill_text = fetch_bill_text_wa_leg(bill_number)

            if not bill_text:
                print(f"  Could not fetch bill text, skipping")
                errors += 1
                continue

            print(f"  Got {len(bill_text)} chars of text")
            print(f"  Analyzing with AI...")

            analysis = analyze_with_ai(bill_number, title, bill_text, openrouter_key)
            time.sleep(OPENROUTER_DELAY)

        if analysis:
            # Update bill in main list
            for b in bills:
                if b.get('bill_id') == bill_id or b.get('bill_number') == bill_number:
                    b['bill_analysis'] = analysis
                    break
            analyzed += 1
            print(f"  Analysis complete ({len(analysis)} chars)")
        else:
            errors += 1
            print(f"  Analysis failed")

    # Save updated bills
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Analysis Complete")
    print(f"  Analyzed: {analyzed}")
    print(f"  Errors: {errors}")
    print(f"  Saved to: {bills_file}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Analyze full bill text with AI")
    parser.add_argument("--limit", type=int, help="Maximum bills to analyze")
    parser.add_argument("--bill", type=str, help="Analyze specific bill (e.g., 'HB 1234')")
    parser.add_argument("--test", action="store_true", help="Test mode (no API calls)")

    args = parser.parse_args()

    return process_bills(
        limit=args.limit,
        specific_bill=args.bill,
        test_mode=args.test
    )


if __name__ == "__main__":
    sys.exit(main())
