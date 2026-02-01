#!/usr/bin/env python3
"""
Fetch Washington State bill data from the LegiScan API.

This script fetches current session bills and saves them to _data/bills.json
for use by the Jekyll static site.

Usage:
    python scripts/fetch_bills.py [--test]

Environment Variables:
    LEGISCAN_API_KEY: Your LegiScan API key (required unless --test)

API Documentation: https://legiscan.com/legiscan
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


# Configuration
LEGISCAN_BASE_URL = "https://api.legiscan.com/"
WA_STATE_ID = 48  # Washington State
CURRENT_SESSION_YEAR = 2025
DATA_DIR = Path(__file__).parent.parent / "_data"

# Rate limiting
REQUESTS_PER_MINUTE = 30
REQUEST_DELAY = 60.0 / REQUESTS_PER_MINUTE


def get_api_key() -> str:
    """Get the LegiScan API key from environment variable."""
    api_key = os.environ.get("LEGISCAN_API_KEY")
    if not api_key:
        raise ValueError(
            "LEGISCAN_API_KEY environment variable not set.\n"
            "Get a free API key at https://legiscan.com/legiscan"
        )
    return api_key


def make_api_request(operation: str, params: dict[str, Any], api_key: str) -> dict:
    """Make a request to the LegiScan API with rate limiting."""
    params["key"] = api_key
    params["op"] = operation

    response = requests.get(LEGISCAN_BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data.get("status") == "ERROR":
        raise RuntimeError(f"LegiScan API error: {data.get('alert', {}).get('message', 'Unknown error')}")

    # Rate limiting
    time.sleep(REQUEST_DELAY)

    return data


def get_wa_session(api_key: str) -> dict | None:
    """Get the current Washington State legislative session."""
    data = make_api_request("getSessionList", {"state": "WA"}, api_key)

    sessions = data.get("sessions", [])

    # Find the most recent regular session
    for session in sessions:
        if session.get("year_start", 0) >= CURRENT_SESSION_YEAR:
            return session

    # Fall back to the most recent session
    return sessions[0] if sessions else None


def get_master_bill_list(session_id: int, api_key: str) -> list[dict]:
    """Get the master list of all bills in a session."""
    data = make_api_request("getMasterList", {"id": session_id}, api_key)

    master_list = data.get("masterlist", {})

    # The master list is a dict with numeric keys
    bills = []
    for key, bill in master_list.items():
        if isinstance(bill, dict) and bill.get("bill_id"):
            bills.append(bill)

    return bills


def get_bill_details(bill_id: int, api_key: str) -> dict | None:
    """Get detailed information for a specific bill."""
    try:
        data = make_api_request("getBill", {"id": bill_id}, api_key)
        return data.get("bill")
    except Exception as e:
        print(f"  Warning: Could not fetch bill {bill_id}: {e}")
        return None


def normalize_status(status_input) -> str:
    """Normalize bill status to consistent values for display.

    LegiScan returns status as an integer code. Map it to human-readable text.
    """
    # LegiScan status codes
    # https://legiscan.com/misc/LegiScan_API_User_Manual.pdf
    status_codes = {
        0: "N/A",
        1: "Introduced",
        2: "Engrossed",
        3: "Enrolled",
        4: "Passed",
        5: "Vetoed",
        6: "Failed",
        # Additional common statuses we may see as text
    }

    # Handle integer status codes
    if isinstance(status_input, int):
        return status_codes.get(status_input, f"Status {status_input}")

    # Handle string status
    status_text = str(status_input) if status_input else "Unknown"
    status_lower = status_text.lower()

    status_map = {
        "introduced": "Introduced",
        "prefiled": "Prefiled",
        "in committee": "In Committee",
        "passed committee": "Passed Committee",
        "passed house": "Passed House",
        "passed senate": "Passed Senate",
        "passed": "Passed",
        "signed": "Signed",
        "enacted": "Enacted",
        "vetoed": "Vetoed",
        "dead": "Dead",
        "failed": "Failed",
        "engrossed": "Engrossed",
        "enrolled": "Enrolled",
    }

    for key, value in status_map.items():
        if key in status_lower:
            return value

    return status_text


def determine_chamber(bill_number: str) -> str:
    """Determine chamber based on bill number prefix."""
    bill_upper = bill_number.upper()
    if bill_upper.startswith(("HB", "HJR", "HCR", "HR")):
        return "House"
    elif bill_upper.startswith(("SB", "SJR", "SCR", "SR")):
        return "Senate"
    return "Unknown"


def format_bill_number(bill_number: str) -> str:
    """Format bill number consistently (e.g., 'HB 1234')."""
    # Insert space if not present
    for prefix in ["HB", "SB", "HJR", "SJR", "HCR", "SCR", "HR", "SR"]:
        if bill_number.upper().startswith(prefix) and not bill_number.startswith(f"{prefix} "):
            return f"{prefix} {bill_number[len(prefix):]}"
    return bill_number


def transform_bill_data(master_bill: dict, detail_bill: dict | None) -> dict:
    """Transform API data into the format needed for the site."""
    bill_number = format_bill_number(master_bill.get("number", ""))

    # Base data from master list
    bill = {
        "bill_id": master_bill.get("bill_id"),
        "bill_number": bill_number,
        "title": master_bill.get("title", ""),
        "description": "",
        "status": normalize_status(master_bill.get("status", "Unknown")),
        "chamber": determine_chamber(bill_number),
        "sponsors": [],
        "introduced_date": "",
        "last_action": master_bill.get("last_action", ""),
        "last_action_date": master_bill.get("last_action_date", ""),
        "history": [],
        "official_url": f"https://app.leg.wa.gov/billsummary?BillNumber={bill_number.split()[-1]}&Year={CURRENT_SESSION_YEAR}",
    }

    # Enrich with detail data if available
    if detail_bill:
        # Clean description of problematic characters
        desc = detail_bill.get("description", "") or ""
        # Replace smart quotes and other problematic chars with ASCII equivalents
        desc = desc.replace('\u2019', "'").replace('\u2018', "'")
        desc = desc.replace('\u201c', '"').replace('\u201d', '"')
        desc = desc.replace('\u2013', '-').replace('\u2014', '-')
        desc = desc.encode('utf-8', errors='ignore').decode('utf-8')
        bill["description"] = desc

        # Sponsors
        sponsors = detail_bill.get("sponsors", [])
        bill["sponsors"] = [
            s.get("name", "") for s in sponsors if s.get("name")
        ]

        # Committee
        committee = detail_bill.get("committee", {})
        if committee:
            bill["committee"] = committee.get("name", "")

        # History
        history = detail_bill.get("history", [])
        bill["history"] = [
            {"date": h.get("date", ""), "action": h.get("action", "")}
            for h in history[-10:]  # Last 10 actions
        ]

        # Introduced date (first history entry)
        if history:
            bill["introduced_date"] = history[0].get("date", "")

    return bill


def load_existing_bills() -> dict[int, dict]:
    """Load existing bills.json and return a lookup by bill_id."""
    bills_file = DATA_DIR / "bills.json"
    if bills_file.exists():
        try:
            with open(bills_file, 'r', encoding='utf-8', errors='ignore') as f:
                bills = json.load(f)
                return {b.get("bill_id"): b for b in bills if b.get("bill_id")}
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Warning: Could not load existing bills: {e}")
            return {}
    return {}


def fetch_all_bills(api_key: str, limit: int | None = None, fetch_details: bool = False) -> list[dict]:
    """Fetch all bills from the current WA session.

    By default, uses master list data only (fast, no extra API calls).
    Set fetch_details=True to get full bill details (slow, many API calls).

    Smart mode (default): Fetches details only for bills missing descriptions,
    preserving existing data for bills we already have.
    """
    print("Fetching Washington State session info...")
    session = get_wa_session(api_key)

    if not session:
        raise RuntimeError("Could not find Washington State session")

    session_id = session.get("session_id")
    session_name = session.get("session_name", "Unknown")
    print(f"Found session: {session_name} (ID: {session_id})")

    print("Fetching master bill list...")
    master_bills = get_master_bill_list(session_id, api_key)
    print(f"Found {len(master_bills)} bills")

    # Sort by last_action_date (newest first) so most recent bills get descriptions first
    master_bills.sort(key=lambda b: b.get("last_action_date") or "", reverse=True)
    print("Sorted bills by last action date (newest first)")

    # Load existing bills to preserve data and check what needs details
    existing_bills = load_existing_bills()
    print(f"Found {len(existing_bills)} existing bills in cache")

    # Count how many need details
    needs_detail_count = sum(
        1 for b in master_bills
        if b.get("bill_id") not in existing_bills or not existing_bills.get(b.get("bill_id"), {}).get("description")
    )
    print(f"Bills needing description fetch: {needs_detail_count}")

    if limit:
        # Limit only applies to bills needing details, not total
        print(f"Limiting detail fetches to {limit} bills")

    bills = []
    total = len(master_bills)
    details_fetched = 0

    for i, master_bill in enumerate(master_bills, 1):
        bill_id = master_bill.get("bill_id")
        bill_number = master_bill.get("number", "Unknown")

        existing = existing_bills.get(bill_id)

        # Check if we need to fetch details for this bill
        needs_details = False
        if fetch_details:
            needs_details = True
        elif existing is None:
            # New bill - fetch details
            needs_details = True
        elif not existing.get("description"):
            # Existing bill but missing description
            needs_details = True

        if needs_details:
            # Check if we've hit the limit for detail fetches
            if limit and details_fetched >= limit:
                # Skip fetching, use existing data if available
                bill_data = transform_bill_data(master_bill, None)
                if existing:
                    bill_data["description"] = existing.get("description", "")
                    bill_data["sponsors"] = existing.get("sponsors", [])
                    bill_data["history"] = existing.get("history", [])
                    bill_data["introduced_date"] = existing.get("introduced_date", "")
                    for key in ["threat_score", "threat_level", "threat_label", "concerns",
                               "positives", "ai_summary", "plain_summary", "amended",
                               "amendment_count", "related_bills", "fiscal_impact", "bill_analysis"]:
                        if key in existing:
                            bill_data[key] = existing[key]
            else:
                print(f"  [{details_fetched + 1}/{needs_detail_count if not limit else min(limit, needs_detail_count)}] Fetching {bill_number}...", end="", flush=True)
                detail_bill = get_bill_details(bill_id, api_key)
                bill_data = transform_bill_data(master_bill, detail_bill)
                details_fetched += 1
                print(" done")
        else:
            # Use existing data, just update from master list
            bill_data = transform_bill_data(master_bill, None)
            # Preserve existing description, sponsors, history, ai_summary, scores
            if existing:
                bill_data["description"] = existing.get("description", "")
                bill_data["sponsors"] = existing.get("sponsors", [])
                bill_data["history"] = existing.get("history", [])
                bill_data["introduced_date"] = existing.get("introduced_date", "")
                # Preserve scoring and AI data
                for key in ["threat_score", "threat_level", "threat_label", "concerns",
                           "positives", "ai_summary", "plain_summary", "amended",
                           "amendment_count", "related_bills", "fiscal_impact"]:
                    if key in existing:
                        bill_data[key] = existing[key]

        bills.append(bill_data)

    print(f"\nProcessed {len(bills)} bills ({details_fetched} detail fetches)")
    return bills


def generate_sample_data() -> list[dict]:
    """Generate sample bill data for testing without API."""
    print("Generating sample bill data for testing...")

    sample_bills = [
        {
            "bill_id": 1001,
            "bill_number": "HB 1234",
            "title": "Concerning digital privacy protections for consumers",
            "description": "An act relating to establishing comprehensive digital privacy rights for Washington residents, including data collection transparency requirements and consumer opt-out provisions.",
            "status": "In Committee",
            "chamber": "House",
            "sponsors": ["Rep. Smith", "Rep. Johnson"],
            "introduced_date": "2025-01-13",
            "last_action": "Referred to Innovation, Community & Economic Development, & Veterans.",
            "last_action_date": "2025-01-15",
            "committee": "Innovation, Community & Economic Development, & Veterans",
            "history": [
                {"date": "2025-01-13", "action": "First reading, referred to Innovation, Community & Economic Development, & Veterans."},
                {"date": "2025-01-15", "action": "Scheduled for public hearing in committee."}
            ],
            "official_url": "https://app.leg.wa.gov/billsummary?BillNumber=1234&Year=2025",
        },
        {
            "bill_id": 1002,
            "bill_number": "SB 5678",
            "title": "Establishing a statewide housing affordability program",
            "description": "An act relating to creating a comprehensive housing affordability initiative, including incentives for affordable housing development and tenant protection measures.",
            "status": "Passed Senate",
            "chamber": "Senate",
            "sponsors": ["Sen. Williams", "Sen. Davis", "Sen. Martinez"],
            "introduced_date": "2025-01-10",
            "last_action": "Third reading, passed; yeas, 35; nays, 14.",
            "last_action_date": "2025-02-01",
            "committee": "Housing",
            "history": [
                {"date": "2025-01-10", "action": "First reading, referred to Housing."},
                {"date": "2025-01-18", "action": "Public hearing in the Senate Committee on Housing."},
                {"date": "2025-01-25", "action": "Executive action taken in the Senate Committee on Housing."},
                {"date": "2025-02-01", "action": "Third reading, passed; yeas, 35; nays, 14."}
            ],
            "official_url": "https://app.leg.wa.gov/billsummary?BillNumber=5678&Year=2025",
        },
        {
            "bill_id": 1003,
            "bill_number": "HB 2001",
            "title": "Concerning environmental protection standards",
            "description": "An act relating to strengthening environmental protection standards for industrial facilities, including emission reporting requirements and compliance enforcement.",
            "status": "Introduced",
            "chamber": "House",
            "sponsors": ["Rep. Chen"],
            "introduced_date": "2025-01-20",
            "last_action": "First reading, referred to Environment & Energy.",
            "last_action_date": "2025-01-20",
            "committee": "Environment & Energy",
            "history": [
                {"date": "2025-01-20", "action": "First reading, referred to Environment & Energy."}
            ],
            "official_url": "https://app.leg.wa.gov/billsummary?BillNumber=2001&Year=2025",
        },
        {
            "bill_id": 1004,
            "bill_number": "SB 5100",
            "title": "Relating to public education funding",
            "description": "An act relating to increasing state funding for K-12 public education, including provisions for teacher compensation and classroom resources.",
            "status": "In Committee",
            "chamber": "Senate",
            "sponsors": ["Sen. Thompson", "Sen. Anderson"],
            "introduced_date": "2025-01-12",
            "last_action": "Public hearing scheduled for February 5.",
            "last_action_date": "2025-01-28",
            "committee": "Early Learning & K-12 Education",
            "history": [
                {"date": "2025-01-12", "action": "First reading, referred to Early Learning & K-12 Education."},
                {"date": "2025-01-20", "action": "Scheduled for public hearing."},
                {"date": "2025-01-28", "action": "Public hearing scheduled for February 5."}
            ],
            "official_url": "https://app.leg.wa.gov/billsummary?BillNumber=5100&Year=2025",
        },
        {
            "bill_id": 1005,
            "bill_number": "HB 1500",
            "title": "Establishing healthcare price transparency requirements",
            "description": "An act relating to requiring healthcare providers and insurers to publish pricing information for common procedures and services.",
            "status": "Passed Committee",
            "chamber": "House",
            "sponsors": ["Rep. Garcia", "Rep. Lee", "Rep. Patel"],
            "introduced_date": "2025-01-11",
            "last_action": "Executive action taken; reported out of committee as substitute.",
            "last_action_date": "2025-01-30",
            "committee": "Health Care & Wellness",
            "history": [
                {"date": "2025-01-11", "action": "First reading, referred to Health Care & Wellness."},
                {"date": "2025-01-22", "action": "Public hearing in committee."},
                {"date": "2025-01-30", "action": "Executive action taken; reported out of committee as substitute."}
            ],
            "official_url": "https://app.leg.wa.gov/billsummary?BillNumber=1500&Year=2025",
        },
    ]

    return sample_bills


def save_bills(bills: list[dict]) -> None:
    """Save bills to the data file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "bills.json"

    # Sort by last action date (most recent first), handling None values
    bills.sort(key=lambda b: b.get("last_action_date") or "", reverse=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(bills, f, indent=2, ensure_ascii=True)  # ASCII-safe to prevent UTF-8 issues

    print(f"\nSaved {len(bills)} bills to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fetch WA State bill data from LegiScan")
    parser.add_argument("--test", action="store_true", help="Use sample data instead of API")
    parser.add_argument("--limit", type=int, help="Limit number of bills to fetch")
    parser.add_argument("--details", action="store_true", help="Fetch full details for each bill (slow)")
    args = parser.parse_args()

    print("=" * 60)
    print("WA Bill Tracker - Data Fetch")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    try:
        if args.test:
            bills = generate_sample_data()
        else:
            api_key = get_api_key()
            bills = fetch_all_bills(api_key, limit=args.limit, fetch_details=args.details)

        save_bills(bills)

        print("\nFetch completed successfully!")
        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
