# scraping/political_contributions.py - Individual campaign contribution lookup
"""
Searches the FEC's public OpenFEC API (Schedule A - itemized individual
receipts) for federal campaign contributions made by named individuals,
filtered by employer. This is how we link a company's named executives to
the politicians they personally donate to - a real, legally-disclosed public
record (FEC individual contribution disclosures), not an inference.

Docs: https://api.open.fec.gov/developers/

Works out of the box against the public DEMO_KEY (rate-limited to light use).
Set FEC_API_KEY (free from https://api.data.gov/signup/) for the full
1,000 requests/hour limit.
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime

FEC_BASE_URL = "https://api.open.fec.gov/v1"
_HEADERS = {'User-Agent': 'Sentilyze Personal Use (political contributions dashboard)'}


def _api_key() -> str:
    return os.getenv('FEC_API_KEY', 'DEMO_KEY')


def search_individual_contributions(name: str, employer: str = None, per_page: int = 10) -> Dict[str, Any]:
    """
    Search FEC Schedule A itemized receipts for contributions from an
    individual, optionally filtered by their reported employer.
    """
    params = {
        'api_key': _api_key(),
        'contributor_name': name,
        'per_page': per_page,
        'sort': '-contribution_receipt_date',
        'is_individual': 'true',
    }
    if employer:
        params['contributor_employer'] = employer

    try:
        resp = requests.get(f"{FEC_BASE_URL}/schedules/schedule_a/", params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        contributions = []
        for record in data.get('results', []):
            committee = record.get('committee', {}) or {}
            contributions.append({
                'contributor_name': record.get('contributor_name'),
                'contributor_employer': record.get('contributor_employer'),
                'contributor_occupation': record.get('contributor_occupation'),
                'amount': record.get('contribution_receipt_amount'),
                'date': record.get('contribution_receipt_date'),
                'committee_name': committee.get('name'),
                'committee_party': committee.get('party') or committee.get('party_full'),
                'candidate_name': record.get('candidate_name'),
                'election_year': record.get('two_year_transaction_period'),
            })

        return {
            'success': True,
            'query_name': name,
            'query_employer': employer,
            'contributions': contributions,
            'total_found': (data.get('pagination') or {}).get('count', len(contributions)),
            'source': 'FEC OpenFEC API (Schedule A individual contributions)',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching FEC contributions for {name}: {str(e)}",
            'source': 'FEC OpenFEC API',
        }


def get_executive_donations(officers: List[Dict[str, Any]], employer_name: str, per_officer: int = 5) -> Dict[str, Any]:
    """Look up political contributions for a list of named company officers."""
    results = []
    for officer in officers:
        name = officer.get('name')
        if not name:
            continue
        donations = search_individual_contributions(name, employer=employer_name, per_page=per_officer)
        results.append({
            'name': name,
            'title': officer.get('title'),
            'donations': donations.get('contributions', []) if donations.get('success') else [],
            'lookup_error': donations.get('error') if not donations.get('success') else None,
        })
    return {
        'success': True,
        'employer_searched': employer_name,
        'executives': results,
        'timestamp': datetime.now().isoformat(),
        'source': 'FEC OpenFEC API',
    }


if __name__ == "__main__":
    result = search_individual_contributions("Tim Cook", employer="Apple")
    print(result.get('total_found'), result.get('contributions', [])[:2])
