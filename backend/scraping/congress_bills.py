# scraping/congress_bills.py - Congress.gov bill & sponsor lookup
"""
Resolves a bill reference (e.g. "hr 1234") into its title, sponsor, and
status via the official Congress.gov API v3 (Library of Congress).

Requires a free API key - sign up at https://api.congress.gov/sign-up/ and
set CONGRESS_GOV_API_KEY. Without a key, lookups degrade gracefully: bill
references extracted from lobbying filings still surface, just without
title/sponsor enrichment.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.cache import cached_fetch

CONGRESS_API_BASE = "https://api.congress.gov/v3"


def _api_key() -> Optional[str]:
    key = os.getenv('CONGRESS_GOV_API_KEY')
    return key if key else None


def is_configured() -> bool:
    return _api_key() is not None


def year_to_congress(year: int) -> int:
    """Map a calendar year to its Congress number (e.g. 2023 -> 118th Congress)."""
    return (year - 1789) // 2 + 1


def get_bill_details(congress: int, bill_type: str, bill_number: str) -> Dict[str, Any]:
    """
    Fetch a single bill's title, sponsor (name/party/state), latest action,
    and policy area from Congress.gov.
    """
    api_key = _api_key()
    if not api_key:
        return {
            'success': False,
            'error': 'CONGRESS_GOV_API_KEY not configured - sign up free at https://api.congress.gov/sign-up/',
            'source': 'Congress.gov API',
        }

    cache_key = f"congress_bill_{congress}_{bill_type}_{bill_number}"

    def fetch():
        resp = requests.get(
            f"{CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{bill_number}",
            params={'api_key': api_key, 'format': 'json'},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    try:
        data = cached_fetch(cache_key, ttl_seconds=24 * 3600, fetch_fn=fetch)
        bill = data.get('bill', {})

        sponsors = bill.get('sponsors', []) or []
        sponsor = None
        if sponsors:
            s = sponsors[0]
            sponsor = {
                'name': s.get('fullName'),
                'party': s.get('party'),
                'state': s.get('state'),
                'bioguide_id': s.get('bioguideId'),
                'chamber': 'House' if bill_type.startswith('h') else 'Senate',
            }

        latest_action = bill.get('latestAction', {})

        return {
            'success': True,
            'congress': congress,
            'bill_type': bill_type,
            'bill_number': bill_number,
            'title': bill.get('title'),
            'sponsor': sponsor,
            'cosponsors_count': (bill.get('cosponsors') or {}).get('count'),
            'policy_area': (bill.get('policyArea') or {}).get('name'),
            'introduced_date': bill.get('introducedDate'),
            'latest_action': {
                'text': latest_action.get('text'),
                'date': latest_action.get('actionDate'),
            },
            'congress_gov_url': f"https://www.congress.gov/bill/{congress}th-congress/{_bill_type_url_segment(bill_type)}/{bill_number}",
            'source': 'Congress.gov API',
        }
    except requests.HTTPError as e:
        return {'success': False, 'error': f"Bill {bill_type}{bill_number} (Congress {congress}) not found or API error: {str(e)}", 'source': 'Congress.gov API'}
    except Exception as e:
        return {'success': False, 'error': f"Error fetching bill details: {str(e)}", 'source': 'Congress.gov API'}


_BILL_TYPE_URL_SEGMENTS = {
    'hr': 'house-bill', 's': 'senate-bill',
    'hjres': 'house-joint-resolution', 'sjres': 'senate-joint-resolution',
    'hconres': 'house-concurrent-resolution', 'sconres': 'senate-concurrent-resolution',
    'hres': 'house-resolution', 'sres': 'senate-resolution',
}


def _bill_type_url_segment(bill_type: str) -> str:
    return _BILL_TYPE_URL_SEGMENTS.get(bill_type, bill_type)


def resolve_bill_references(bill_refs: List[Dict[str, Any]], filing_years: List[int], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Resolve a list of {bill_type, number} refs (as produced by
    scraping/lobbying.py) into full bill details, guessing the Congress
    number from the filing years they were mentioned in.
    """
    if not is_configured():
        return [{
            'bill_type': ref['bill_type'], 'number': ref['number'], 'raw': ref.get('raw'),
            'success': False,
            'error': 'CONGRESS_GOV_API_KEY not configured',
        } for ref in bill_refs[:limit]]

    congresses = sorted({year_to_congress(y) for y in filing_years}, reverse=True) or [year_to_congress(datetime.now().year)]

    resolved = []
    for ref in bill_refs[:limit]:
        details = None
        for congress in congresses:
            details = get_bill_details(congress, ref['bill_type'], ref['number'])
            if details.get('success'):
                break
        resolved.append(details or {'success': False, 'error': 'No details found'})

    return resolved


if __name__ == "__main__":
    print("Configured:", is_configured())
    if is_configured():
        print(get_bill_details(118, 'hr', '1234'))
