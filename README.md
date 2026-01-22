# WA Bill Tracker

A free-to-host static website that tracks Washington State bills, provides direct links to official comment/testimony pages, and explains bills in plain language to help citizens engage with the legislative process.

## Features

- **Bill Tracking Dashboard**: Browse all bills in the current WA legislative session
- **Featured Bills**: Curated list of important bills with plain-English summaries
- **Direct Action Links**: One-click access to comment on bills and sign up for testimony
- **Search & Filter**: Find bills by keyword, chamber, or status
- **Civic Action Guide**: Learn how to submit comments, testify, and contact legislators
- **Automated Updates**: Daily data refresh via GitHub Actions

## Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| Hosting | GitHub Pages | Free |
| Static Site Generator | Jekyll | Free |
| Data Source | LegiScan API | Free (30k queries/month) |
| Automation | GitHub Actions | Free (public repo) |
| Domain (optional) | Custom | ~$12/year |

**Total Cost: $0** (with optional custom domain)

## Quick Start

### 1. Fork This Repository

Click "Fork" in the top right corner to create your own copy.

### 2. Get a LegiScan API Key

1. Go to [https://legiscan.com/legiscan](https://legiscan.com/legiscan)
2. Create a free account
3. Your API key will be in your account settings

### 3. Add API Key to GitHub Secrets

1. Go to your repository's **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `LEGISCAN_API_KEY`
4. Value: Your LegiScan API key
5. Click **Add secret**

### 4. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: **GitHub Actions**

### 5. Trigger Your First Update

1. Go to **Actions** → **Update Bill Data**
2. Click **Run workflow**
3. Optionally check "Use sample data" for testing without API

Your site will be live at `https://yourusername.github.io/wa-bill-tracker/`

## Local Development

### Prerequisites

- Ruby 3.0+ with Bundler
- Python 3.9+

### Setup

```bash
# Install Ruby dependencies
bundle install

# Install Python dependencies
pip install requests

# Fetch sample bill data (no API key needed)
python scripts/fetch_bills.py --test

# Generate bill pages
python scripts/generate_pages.py

# Run Jekyll locally
bundle exec jekyll serve
```

Visit `http://localhost:4000` to see the site.

### Fetching Real Data

```bash
# Set your API key
export LEGISCAN_API_KEY=your_key_here

# Fetch all bills (rate-limited, may take a while)
python scripts/fetch_bills.py

# Or fetch a limited number for testing
python scripts/fetch_bills.py --limit 20

# Regenerate pages
python scripts/generate_pages.py
```

## Customization

### Adding Featured Bills

Edit `_data/featured.json` to highlight specific bills:

```json
[
  {
    "bill_number": "HB 1234",
    "why_featured": "Why this bill matters",
    "plain_summary": "What this bill does in plain English...",
    "why_it_matters": "How this affects you...",
    "stance": "watch",
    "urgency": "high",
    "hearing_date": "2025-02-15",
    "hearing_info": "Public hearing details..."
  }
]
```

Fields:
- `bill_number` (required): Must match a bill in `bills.json`
- `why_featured`: Brief reason shown on homepage
- `plain_summary`: Your plain-English explanation
- `why_it_matters`: Impact statement
- `stance`: `watch`, `support`, or `oppose`
- `urgency`: `high`, `medium`, or `low`
- `hearing_date`: Upcoming hearing date
- `hearing_info`: Additional hearing details

### Changing Site Settings

Edit `_config.yml`:

```yaml
title: WA Bill Tracker
description: Your custom description
current_session: "2025-26"
legislature_year: 2025
```

### Styling

All styles are in `assets/css/style.css`. The design uses CSS custom properties for easy theming:

```css
:root {
  --color-primary: #2563eb;  /* Blue accent */
  --color-slate-900: #0f172a; /* Dark text */
  /* etc. */
}
```

## Project Structure

```
wa-bill-tracker/
├── .github/workflows/
│   └── update-bills.yml    # Automated daily updates
├── _data/
│   ├── bills.json          # All bill data (auto-updated)
│   └── featured.json       # Your curated bills
├── _layouts/
│   ├── default.html        # Base page layout
│   └── bill.html           # Individual bill pages
├── _includes/
│   ├── header.html
│   ├── footer.html
│   └── bill-card.html
├── _bills/                  # Generated bill pages
├── assets/
│   ├── css/style.css
│   └── js/search.js
├── scripts/
│   ├── fetch_bills.py      # LegiScan API fetcher
│   └── generate_pages.py   # Bill page generator
├── index.html              # Homepage
├── all-bills.html          # Searchable bill list
├── how-to-act.html         # Civic action guide
├── _config.yml             # Jekyll config
└── Gemfile                 # Ruby dependencies
```

## Maintenance

### Daily (Automated)

GitHub Actions runs at 8 AM UTC daily to:
1. Fetch latest bill data from LegiScan
2. Update `_data/bills.json`
3. Regenerate bill pages
4. Rebuild and deploy the site

### Weekly (Manual, ~15 min)

1. Review new bills in `_data/bills.json`
2. Add important bills to `_data/featured.json` with plain summaries
3. Update hearing dates and urgency levels

### As Needed

- Update site copy and styling
- Add new bills to featured list when hearings are announced

## Official WA Legislature URLs

| Purpose | URL Pattern |
|---------|-------------|
| Comment on bill | `https://app.leg.wa.gov/pbc/bill/{BILL_NUMBER}` |
| Official bill page | `https://app.leg.wa.gov/billsummary?BillNumber={NUM}&Year=2025` |
| Find your legislator | `https://app.leg.wa.gov/districtfinder/` |
| Committee schedules | `https://leg.wa.gov/legislature/pages/calendar.aspx` |
| Legislative hotline | 1-800-562-6000 |

## Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or suggestions
- Submit pull requests for improvements
- Share the project to help more citizens engage

## License

MIT License - Use this project however you like.

## Disclaimer

This is an independent, non-partisan resource. It is not affiliated with or endorsed by the Washington State Legislature. Always verify information on the [official WA Legislature website](https://leg.wa.gov).

---

**Made to help Washington citizens participate in democracy.**
