#!/usr/bin/env python3
"""
Fetch PEN America's public banned-books index (Google Sheet CSV export),
aggregate title/author occurrences, and reconcile against the live IsItBanned inventory.

Outputs:
- pen-america-live-index.csv
- pen-america-live-summary.json
- pen-vs-site-reconciliation.csv
- pen-vs-site-reconciliation.json
"""

import csv
import io
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from urllib.request import Request, urlopen
import ssl

BASE_DIR = Path(__file__).parent.parent
PEN_CSV_URL = 'https://docs.google.com/spreadsheets/d/1eU3rCvzLjBwnVpph_Svs8MFmnp9EH8RG_72UofANVeM/export?format=csv'
INVENTORY_PATH = BASE_DIR / 'inventory-index-rich.json'

VARIANT_HINTS = [
    'vol.', 'volume', 'edition', 'graphic', 'revised', 'expanded',
    'reissue', 'special', 'deluxe', 'anniversary', 'illustrated',
    'series', 'book 1', 'book one', 'omnibus', 'boxed set'
]


def normalize_title(title: str) -> str:
    t = (title or '').lower().strip()
    t = re.sub(r'^(the|a|an)\s+', '', t)
    t = re.sub(r'[^\w\s]', '', t)
    return ' '.join(t.split())


def normalize_author(author: str) -> str:
    a = (author or '').lower().strip()
    a = re.sub(r'[^\w\s&]', '', a)
    return ' '.join(a.split())


def fetch_pen_rows():
    req = Request(PEN_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    context = ssl._create_unverified_context()
    with urlopen(req, timeout=60, context=context) as resp:
        raw = resp.read().decode('utf-8', errors='replace')

    all_rows = list(csv.reader(io.StringIO(raw)))
    header_idx = None
    for i, row in enumerate(all_rows):
        if row and len(row) >= 2 and row[0].strip() == 'Title' and row[1].strip() == 'Author':
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError('Could not find PEN CSV header row')

    header = all_rows[header_idx]
    data_rows = all_rows[header_idx + 1:]
    rows = [dict(zip(header, row + [''] * (len(header) - len(row)))) for row in data_rows if any(cell.strip() for cell in row)]
    return rows


def aggregate_pen(rows):
    grouped = {}
    for row in rows:
        title = (row.get('Title') or row.get('\ufeffTitle') or '').strip()
        author = (row.get('Author') or '').strip()
        if not title:
            continue
        key = (normalize_title(title), normalize_author(author))
        if key not in grouped:
            grouped[key] = {
                'title': title,
                'author': author,
                'normalizedTitle': key[0],
                'normalizedAuthor': key[1],
                'occurrenceCount': 0,
                'states': set(),
                'districts': set(),
                'banStatuses': Counter(),
                'origins': Counter(),
                'sampleChallenges': [],
            }
        entry = grouped[key]
        entry['occurrenceCount'] += 1
        if row.get('State'):
            entry['states'].add(row['State'].strip())
        if row.get('District'):
            entry['districts'].add(row['District'].strip())
        if row.get('Ban Status'):
            entry['banStatuses'][row['Ban Status'].strip()] += 1
        if row.get('Origin of Challenge'):
            entry['origins'][row['Origin of Challenge'].strip()] += 1
        if len(entry['sampleChallenges']) < 5:
            entry['sampleChallenges'].append({
                'state': row.get('State', '').strip(),
                'district': row.get('District', '').strip(),
                'date': row.get('Date of Challenge/Removal', '').strip(),
                'banStatus': row.get('Ban Status', '').strip(),
            })

    out = []
    for entry in grouped.values():
        out.append({
            'title': entry['title'],
            'author': entry['author'],
            'normalizedTitle': entry['normalizedTitle'],
            'normalizedAuthor': entry['normalizedAuthor'],
            'occurrenceCount': entry['occurrenceCount'],
            'statesCount': len(entry['states']),
            'districtsCount': len(entry['districts']),
            'topBanStatus': entry['banStatuses'].most_common(1)[0][0] if entry['banStatuses'] else '',
            'topOrigin': entry['origins'].most_common(1)[0][0] if entry['origins'] else '',
            'sampleChallenges': entry['sampleChallenges'],
        })
    out.sort(key=lambda x: (-x['occurrenceCount'], x['title'].lower()))
    return out


def load_inventory():
    return json.loads(INVENTORY_PATH.read_text(encoding='utf-8'))


def looks_like_variant(candidate_title, existing_title):
    both = f"{candidate_title} {existing_title}".lower()
    return any(hint in both for hint in VARIANT_HINTS)


def reconcile(pen_books, inventory):
    by_title_author = {}
    for row in inventory:
        key = (row['normalizedTitle'], row['normalizedAuthor'])
        by_title_author.setdefault(key, []).append(row)

    results = []
    for book in pen_books:
        key = (book['normalizedTitle'], book['normalizedAuthor'])
        matched = by_title_author.get(key, [])
        match_type = 'missing'
        status = 'missing'
        matched_slug = ''
        completeness = ''
        notes = ''

        if matched:
            m = matched[0]
            matched_slug = m['slug']
            completeness = m['completenessStatus']
            match_type = 'title_author'
            status = 'exists_complete' if completeness == 'complete' else 'exists_incomplete'
            notes = f"Matched by normalized title/author to {matched_slug}"
        else:
            best = None
            best_ratio = 0
            for inv in inventory:
                if book['normalizedAuthor'] and inv['normalizedAuthor'] != book['normalizedAuthor']:
                    continue
                ratio = SequenceMatcher(None, book['normalizedTitle'], inv['normalizedTitle']).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best = inv
            if best and best_ratio >= 0.88:
                matched_slug = best['slug']
                completeness = best['completenessStatus']
                match_type = 'variant' if looks_like_variant(book['title'], best['title']) else 'fuzzy'
                status = 'manual_review'
                notes = f"{int(best_ratio*100)}% title match with {best['slug']}"

        results.append({
            'title': book['title'],
            'author': book['author'],
            'occurrenceCount': book['occurrenceCount'],
            'statesCount': book['statesCount'],
            'districtsCount': book['districtsCount'],
            'topBanStatus': book['topBanStatus'],
            'matchedSlug': matched_slug,
            'matchType': match_type,
            'status': status,
            'existingCompleteness': completeness,
            'notes': notes,
        })
    results.sort(key=lambda x: (-x['occurrenceCount'], x['title'].lower()))
    return results


def write_csv(rows, path):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    print('Fetching PEN America live index...')
    rows = fetch_pen_rows()
    print(f'Fetched {len(rows)} raw PEN rows')

    pen_books = aggregate_pen(rows)
    write_csv([{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v) for k, v in row.items()} for row in pen_books], BASE_DIR / 'pen-america-live-index.csv')
    (BASE_DIR / 'pen-america-live-summary.json').write_text(json.dumps(pen_books, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Aggregated to {len(pen_books)} unique title/author entries')

    inventory = load_inventory()
    reconciliation = reconcile(pen_books, inventory)
    write_csv(reconciliation, BASE_DIR / 'pen-vs-site-reconciliation.csv')
    (BASE_DIR / 'pen-vs-site-reconciliation.json').write_text(json.dumps(reconciliation, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    counts = Counter(r['status'] for r in reconciliation)
    print('Reconciliation summary:')
    for k, v in counts.items():
        print(f'  {k}: {v}')
    print('Wrote pen-america-live-index.csv, pen-america-live-summary.json, pen-vs-site-reconciliation.csv, pen-vs-site-reconciliation.json')


if __name__ == '__main__':
    main()
