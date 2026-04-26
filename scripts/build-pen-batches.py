#!/usr/bin/env python3
"""
Build 25-at-a-time PEN production batches and a Ross review bucket.

Inputs:
- pen-action-report.json

Outputs:
- pen-batch-01.json / .csv / .md
- pen-batch-01-ross-review.json / .csv / .md
"""

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SRC = BASE_DIR / 'pen-action-report.json'
BATCH_SIZE = 25

SENSITIVE_TERMS = [
    'sexual', 'assault', 'rape', 'abuse', 'child', 'traffick', 'kidnap',
    'suicide', 'self-harm', 'violence', 'shooting', 'trans', 'lgbt', 'queer'
]

KNOWN_REVIEW_TITLES = {
    'Gender Queer: A Memoir',
    'Flamer',
    'This Book Is Gay',
    'All Boys Aren\'t Blue',
    'The Perks of Being a Wallflower',
    'Sold',
    'The Bluest Eye',
    'Thirteen Reasons Why',
    'Melissa (George)',
    'Lawn Boy',
    'Lucky',
    'Nineteen Minutes',
    'Forever...',
}


def needs_review(row):
    hay = f"{row.get('title','')} {row.get('notes','')}".lower()
    if row.get('title') in KNOWN_REVIEW_TITLES:
        return True
    return any(term in hay for term in SENSITIVE_TERMS)


def write_csv(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path, title, rows):
    lines = [f'# {title}', '']
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. **{row['title']}** — {row['author']} (occurrences: {row['occurrenceCount']})")
        if row.get('notes'):
            lines.append(f"   - notes: {row['notes']}")
        if row.get('matchedSlug'):
            lines.append(f"   - matched slug: {row['matchedSlug']}")
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    rows = json.loads(SRC.read_text(encoding='utf-8'))
    missing = [r for r in rows if r['bucket'] == 'likely_truly_missing']

    review = []
    ready = []
    for row in missing:
        if needs_review(row):
            review.append(row)
        else:
            ready.append(row)

    batch = ready[:BATCH_SIZE]
    review_bucket = review[:BATCH_SIZE]

    (BASE_DIR / 'pen-batch-01.json').write_text(json.dumps(batch, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    write_csv(BASE_DIR / 'pen-batch-01.csv', batch)
    write_md(BASE_DIR / 'PEN_BATCH_01.md', 'PEN Batch 01', batch)

    (BASE_DIR / 'pen-batch-01-ross-review.json').write_text(json.dumps(review_bucket, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    write_csv(BASE_DIR / 'pen-batch-01-ross-review.csv', review_bucket)
    write_md(BASE_DIR / 'PEN_BATCH_01_ROSS_REVIEW.md', 'PEN Batch 01 — Ross Review Bucket', review_bucket)

    print(f'Wrote batch of {len(batch)} ready titles and {len(review_bucket)} Ross-review titles')


if __name__ == '__main__':
    main()
