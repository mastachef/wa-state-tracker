# Research Report: Washington State Legislator and Campaign Finance Data Sources
Generated: 2026-01-22

## Summary

Washington State provides excellent FREE public data access through three main sources:
1. WA Legislature SOAP Web Services for legislator info
2. Public Disclosure Commission (PDC) via Socrata/SODA API for campaign finance and lobbyist data
3. LegiScan API for bill sponsor data

All APIs are free with reasonable rate limits. The WA Legislature API requires no API key. PDC data is accessed via data.wa.gov with no key needed. LegiScan offers 30,000 free queries/month with a free API key.

---

## 1. WA State Legislature Web Services (FREE, No API Key)

### Service URL
https://wslwebservices.leg.wa.gov/

### Key Endpoints for Legislators

#### Get All House Members
```
GET https://wslwebservices.leg.wa.gov/SponsorService.asmx/GetHouseSponsors?biennium=2025-26
```

#### Get All Senate Members
```
GET https://wslwebservices.leg.wa.gov/SponsorService.asmx/GetSenateSponsors?biennium=2025-26
```

#### Get Committees
```
GET https://wslwebservices.leg.wa.gov/CommitteeService.asmx/GetCommittees?biennium=2025-26
```

### Response Format (XML)
```xml
<ArrayOfMember>
  <Member>
    <Id>31526</Id>
    <Name>Peter Abbarno</Name>
    <Party>R</Party>
    <District>20</District>
    <Phone>(360) 786-7896</Phone>
    <Email>Peter.Abbarno@leg.wa.gov</Email>
  </Member>
</ArrayOfMember>
```

### Fields Available
- Id: Unique legislator ID
- Name: Full name
- Party: R or D
- District: Legislative district number
- Phone: Office phone
- Email: Official email
- FirstName, LastName: Name parts

### Biennium Format
IMPORTANT: Use format YYYY-YY (e.g., 2025-26), not 2025-2026

### Rate Limits
None documented - public service available 24/7

---

## 2. PDC Campaign Finance Data (FREE, No API Key for basic access)

### Base URL
https://data.wa.gov/resource/

### Key Datasets

| Dataset | Socrata ID | Description |
|---------|------------|-------------|
| Contributions | kv7h-kjye | All contributions to candidates and committees |
| Expenditures | tijg-9zyp | All expenditures by candidates and committees |
| Campaign Summary | 3h9x-7bvm | Summary totals per candidate/committee |
| Lobbyist Registrations | xhn7-64im | Lobbyist-employer relationships |
| Lobbyist Compensation | 9nnw-c693 | Lobbyist pay and expenses |

### API Endpoints

#### Get Contributions (JSON)
```
GET https://data.wa.gov/resource/kv7h-kjye.json
```

#### Get Expenditures (JSON)
```
GET https://data.wa.gov/resource/tijg-9zyp.json
```

#### Filter by Election Year
```
GET https://data.wa.gov/resource/kv7h-kjye.json?election_year=2024
```

### Contribution Record Fields
- id: Record ID
- filer_id: Candidate/committee ID
- filer_name: Name of campaign/committee
- party: DEMOCRATIC, REPUBLICAN
- election_year: Year
- amount: Contribution amount
- cash_or_in_kind: Cash or In-Kind
- receipt_date: Date received
- contributor_name: Donor name
- contributor_employer_name: Employer
- contributor_occupation: Occupation

### Rate Limits
- Without app token: 1000 requests/hour per IP
- With app token: Higher limits (free registration)

---

## 3. PDC Lobbyist Data (FREE)

### Lobbyist Employment Registrations
```
GET https://data.wa.gov/resource/xhn7-64im.json
```

### Record Fields
- lobbyist_id: Lobbyist ID
- lobbyist_name: Lobbyist firm name
- employer_id: Client/employer ID
- employer_name: Client organization
- employment_year: Year

### Lobbyist Compensation
```
GET https://data.wa.gov/resource/9nnw-c693.json
```

---

## 4. LegiScan API (FREE tier: 30,000 queries/month)

### API Key
Required - Free registration at https://legiscan.com/legiscan

### Key Operations
- getSessionPeople: All legislators for a session
- getPerson: Individual legislator details
- getSponsoredList: Bills sponsored by a legislator

### Rate Limits
- Free tier: 30,000 queries/month

---

## Comparison Matrix

| Source | Data Type | Format | API Key | Rate Limit |
|--------|-----------|--------|---------|------------|
| WA Legislature | Legislators | XML | None | None |
| PDC (data.wa.gov) | Campaign Finance | JSON | Optional | 1000/hr |
| LegiScan | Bill Sponsors | JSON | Required | 30k/month |

---

## Sources

1. https://wslwebservices.leg.wa.gov/
2. https://pdc.wa.gov/political-disclosure-reporting-data/open-data
3. https://data.wa.gov/
4. https://dev.socrata.com/
5. https://legiscan.com/legiscan
6. https://api.legiscan.com/dl/LegiScan_API_User_Manual.pdf
