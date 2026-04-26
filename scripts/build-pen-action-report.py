#!/usr/bin/env python3
"""
Turn pen-vs-site-reconciliation.json into a clean action report.

Outputs:
- pen-action-report.json
- pen-action-report.csv
- PEN_ACTION_REPORT.md
"""

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SRC = BASE_DIR / 'pen-vs-site-reconciliation.json'


def classify(row):
    title = row.get('title', '')
    match_type = row.get('matchType', '')
    status = row.get('status', '')
    occ = int(row.get('occurrenceCount', 0) or 0)
    notes = row.get('notes', '')

    if status == 'exists_incomplete':
        bucket = 'existing_but_incomplete'
        priority = 'high' if occ >= 3 else 'normal'
    elif status == 'manual_review' or match_type in {'variant', 'fuzzy'}:
        bucket = 'likely_existing_but_mismatch'
        priority = 'high'
    else:
        bucket = 'likely_truly_missing'
        priority = 'high' if occ >= 5 else 'normal'

    return {
        'bucket': bucket,
        'priority': priority,
        'title': title,
        'author': row.get('author', ''),
        'occurrenceCount': occ,
        'statesCount': row.get('statesCount', 0),
        'districtsCount': row.get('districtsCount', 0),
        'topBanStatus': row.get('topBanStatus', ''),
        'matchedSlug': row.get('matchedSlug', ''),
        'existingCompleteness': row.get('existingCompleteness', ''),
        'matchType': match_type,
        'notes': notes,
    }


def main():
    rows = json.loads(SRC.read_text(encoding='utf-8'))
    out = [classify(r) for r in rows]
    out.sort(key=lambda r: (r['bucket'], -r['occurrenceCount'], r['title'].lower()))

    (BASE_DIR / 'pen-action-report.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    with (BASE_DIR / 'pen-action-report.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

    buckets = {
        'likely_truly_missing': [r for r in out if r['bucket'] == 'likely_truly_missing'],
        'likely_existing_but_mismatch': [r for r in out if r['bucket'] == 'likely_existing_but_mismatch'],
        'existing_but_incomplete': [r for r in out if r['bucket'] == 'existing_but_incomplete'],
    }

    lines = []
    lines.append('# PEN Action Report\n')
    lines.append('Generated from `pen-vs-site-reconciliation.json`.\n')
    for bucket_name, items in buckets.items():
        lines.append(f'## {bucket_name} ({len(items)})\n')
        for row in items[:50]:
            extra = f" -> {row['matchedSlug']}" if row['matchedSlug'] else ''
            lines.append(f"- {row['title']} — {row['author']} (occurrences: {row['occurrenceCount']}){extra}")
        lines.append('')

    (BASE_DIR / 'PEN_ACTION_REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Wrote pen-action-report.json, pen-action-report.csv, PEN_ACTION_REPORT.md')


if __name__ == '__main__':
    main()
