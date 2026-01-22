#!/usr/bin/env python3
"""
Score Washington State bills based on liberty, fiscal, and constitutional criteria.

This script analyzes bill titles and descriptions to assign threat levels.
Default assumption: most bills expand government power and are harmful.

Scoring Philosophy:
- Bills are GUILTY until proven innocent
- Government expansion = bad
- New mandates/regulations = bad
- Tax increases = bad
- Spending increases = bad
- Rights restrictions = bad
- Deregulation/tax cuts/liberty expansion = good

Threat Levels:
- RED (Critical): Direct attack on rights, major tax/spend, new mandates
- ORANGE (High): Expands government power, new regulations, moderate fiscal impact
- YELLOW (Moderate): Minor expansion, unclear impact, needs scrutiny
- GREEN (Low): Reduces government, protects rights, cuts taxes/spending
- GRAY (Unknown): Insufficient info to score

Usage:
    python scripts/score_bills.py
"""

import json
import re
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "_data"


# === SCORING KEYWORDS ===
# Negative indicators (increase threat level)
RED_FLAGS = {
    # Direct rights violations
    r'\b(ban|prohibit|restrict|forbid|criminalize|penalize|mandate|require|compel|force)\b': 3,
    r'\b(surveillance|monitor|track|database|registry|registration)\b': 3,
    r'\b(firearm|gun|weapon|ammunition)\b.*\b(restrict|ban|prohibit|regulate|limit)': 4,
    r'\b(speech|expression|protest)\b.*\b(restrict|limit|regulate)': 4,
    r'\b(emergency powers?|executive authority|governor.{0,20}authority)': 3,

    # Tax and fiscal harm
    r'\b(tax increase|raise.{0,10}tax|new tax|additional tax|impose.{0,10}tax)': 3,
    r'\b(fee increase|new fee|additional fee|surcharge)': 2,
    r'\b(bond|borrow|debt|deficit spending)': 2,
    r'\b(appropriat|spend|fund|allocat).{0,20}(\d+\s*(million|billion)|substantial)': 2,

    # New government expansion
    r'\b(new (agency|department|bureau|commission|board|authority|office|program))': 3,
    r'\b(creat|establish|implement).{0,20}(program|initiative|system|framework)': 2,
    r'\b(expand|increase|enhance).{0,20}(authority|power|jurisdiction|enforcement)': 2,
    r'\b(regulat|licensing|permit|certification).{0,10}(requirement|mandate|new)': 2,

    # Mandates on people/business
    r'\b(employer.{0,10}(must|shall|required)|business.{0,10}(must|shall|required))': 2,
    r'\b(landlord.{0,10}(must|shall|required)|property owner.{0,10}(must|shall))': 2,
    r'\b(insurance.{0,10}(mandate|require|coverage))': 2,
    r'\b(minimum wage|wage.{0,10}increase)': 2,
    r'\b(zoning|land use).{0,10}(restrict|limit|regulate)': 2,

    # Environmental overreach
    r'\b(carbon tax|emission.{0,10}(fee|tax|limit)|climate.{0,10}mandate)': 2,
    r'\b(renewable.{0,10}(mandate|requirement)|clean energy.{0,10}standard)': 2,

    # Education control
    r'\b(curriculum.{0,10}(mandate|require)|school.{0,10}(mandate|require))': 2,
    r'\b(dei|equity|inclusion).{0,10}(require|mandate|training)': 2,
}

ORANGE_FLAGS = {
    # Regulatory expansion
    r'\b(regulat|oversight|compliance|enforce)': 1,
    r'\b(license|permit|certificate|credential)': 1,
    r'\b(report|disclosure|transparency).{0,10}(require|mandate)': 1,
    r'\b(study|task force|commission|committee|working group)': 1,

    # Spending indicators
    r'\b(grant|subsid|incentive|credit|rebate)': 1,
    r'\b(fund|financ|appropriat)': 1,

    # Government growth
    r'\b(agency|department|bureau|office|program)': 1,
    r'\b(state employ|public employ|government employ)': 1,
}

# Positive indicators (decrease threat level)
GREEN_FLAGS = {
    # Liberty expansion
    r'\b(repeal|abolish|eliminate|remove).{0,20}(regulation|requirement|mandate|restriction|ban|prohibition)': -3,
    r'\b(deregulat|reduce.{0,10}regulation|regulatory reform)': -3,
    r'\b(protect|preserve|defend).{0,20}(right|liberty|freedom|property)': -2,
    r'\b(due process|constitutional right|civil libert)': -2,

    # Fiscal responsibility
    r'\b(tax (cut|reduction|relief|credit|deduction)|reduce.{0,10}tax|lower.{0,10}tax)': -3,
    r'\b(spending (cut|reduction|limit)|reduce.{0,10}spending|fiscal restraint)': -3,
    r'\b(balanced budget|debt reduction|deficit reduction)': -2,
    r'\b(sunset|expir|terminat).{0,20}(program|agency|tax)': -2,

    # Government reduction
    r'\b(eliminat|abolish|dissolve).{0,20}(agency|department|program|office)': -3,
    r'\b(privatiz|contract out|outsource)': -2,
    r'\b(limit|restrict|reduce).{0,20}(government|state|authority|power)': -2,

    # Transparency/accountability
    r'\b(audit|inspector general|accountability|oversight).{0,20}government': -1,
    r'\b(public record|freedom of information|open meeting)': -1,

    # Self-defense/2A
    r'\b(second amendment|right to bear|self.defense|concealed carry|constitutional carry)': -2,
    r'\b(firearm|gun).{0,20}(right|freedom|protect)': -2,
}


def score_bill(bill: dict) -> dict:
    """
    Score a bill based on its title and description.
    Returns the bill dict with added scoring fields.
    """
    title = (bill.get("title") or "").lower()
    description = (bill.get("description") or "").lower()
    last_action = (bill.get("last_action") or "").lower()

    # Combine text for analysis
    text = f"{title} {description} {last_action}"

    # Start with baseline score (skeptical - assume slight harm)
    score = 1  # Default slight negative (yellow)

    matched_concerns = []
    matched_positives = []

    # Check red flags (most harmful)
    for pattern, weight in RED_FLAGS.items():
        if re.search(pattern, text, re.IGNORECASE):
            score += weight
            matched_concerns.append(pattern.split(r'\b')[1] if r'\b' in pattern else pattern[:30])

    # Check orange flags (moderate harm)
    for pattern, weight in ORANGE_FLAGS.items():
        if re.search(pattern, text, re.IGNORECASE):
            score += weight
            if weight > 0:
                matched_concerns.append(pattern.split(r'\b')[1] if r'\b' in pattern else pattern[:30])

    # Check green flags (beneficial)
    for pattern, weight in GREEN_FLAGS.items():
        if re.search(pattern, text, re.IGNORECASE):
            score += weight  # weight is negative, so this reduces score
            matched_positives.append(pattern.split(r'\b')[1] if r'\b' in pattern else pattern[:30])

    # Determine threat level
    if score >= 6:
        threat_level = "critical"
        threat_label = "Critical Threat"
    elif score >= 3:
        threat_level = "high"
        threat_label = "High Threat"
    elif score >= 1:
        threat_level = "moderate"
        threat_label = "Moderate Concern"
    elif score >= -2:
        threat_level = "low"
        threat_label = "Low Concern"
    else:
        threat_level = "beneficial"
        threat_label = "Potentially Beneficial"

    # If we have no text to analyze, mark as unknown
    if not title and not description:
        threat_level = "unknown"
        threat_label = "Insufficient Data"
        score = 0

    # Add scoring data to bill
    bill["threat_score"] = score
    bill["threat_level"] = threat_level
    bill["threat_label"] = threat_label

    # Add brief concern summary (top 3)
    if matched_concerns:
        bill["concerns"] = list(set(matched_concerns))[:3]
    if matched_positives:
        bill["positives"] = list(set(matched_positives))[:3]

    return bill


def score_all_bills():
    """Load bills, score them, and save back."""
    bills_file = DATA_DIR / "bills.json"

    if not bills_file.exists():
        print("No bills.json found")
        return 1

    with open(bills_file, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    print(f"Scoring {len(bills)} bills...")

    # Score each bill
    threat_counts = {
        "critical": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "beneficial": 0,
        "unknown": 0
    }

    for bill in bills:
        score_bill(bill)
        threat_counts[bill["threat_level"]] += 1

    # Save scored bills
    with open(bills_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)

    print("\nThreat Level Distribution:")
    print(f"  🔴 Critical:   {threat_counts['critical']:4d} bills")
    print(f"  🟠 High:       {threat_counts['high']:4d} bills")
    print(f"  🟡 Moderate:   {threat_counts['moderate']:4d} bills")
    print(f"  🟢 Low:        {threat_counts['low']:4d} bills")
    print(f"  💚 Beneficial: {threat_counts['beneficial']:4d} bills")
    print(f"  ⚪ Unknown:    {threat_counts['unknown']:4d} bills")

    print(f"\nScoring complete. Updated {bills_file}")
    return 0


if __name__ == "__main__":
    exit(score_all_bills())
