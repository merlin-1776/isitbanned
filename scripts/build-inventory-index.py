#!/usr/bin/env python3
"""
Build canonical IsItBanned inventory and reconciliation outputs.

Outputs:
- .inventory-index.json            Legacy slug-keyed inventory for existing tools
- inventory-index-rich.json        Rich list of all current pages and completeness flags
- inventory-lookup.json            Search-friendly lookup indexes
- coverage-reconciliation.json     Candidate-vs-inventory reconciliation
- coverage-reconciliation.csv      Flat CSV report for manual review

Default candidate source:
- next-batch-candidates.json (if present)
"""

import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BOOKS_DIR = BASE_DIR / "src" / "content" / "books"
DEFAULT_CANDIDATES = BASE_DIR / "next-batch-candidates.json"

VARIANT_HINTS = [
    'vol.', 'volume', 'edition', 'graphic', 'revised', 'expanded',
    'reissue', 'special', 'deluxe', 'anniversary', 'illustrated',
    'series', 'book 1', 'book one', 'omnibus', 'boxed set'
]


def normalize_title(title: str) -> str:
    t = (title or "").lower().strip()
    t = re.sub(r'^(the|a|an)\s+', '', t)
    t = re.sub(r'[^\w\s]', '', t)
    return ' '.join(t.split())


def normalize_author(author: str) -> str:
    a = (author or "").lower().strip()
    a = re.sub(r'[^\w\s&]', '', a)
    return ' '.join(a.split())


def extract_frontmatter_and_body(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?', content, re.DOTALL)
    if not match:
        return {}, content
    fm_text = match.group(1)
    body = content[match.end():]

    metadata = {}
    current_key = None
    in_list = False
    for raw_line in fm_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if re.match(r'^\s+-\s+', line) and current_key:
            metadata.setdefault(current_key, []).append(re.sub(r'^\s+-\s+', '', line).strip().strip('"\''))
            in_list = True
            continue
        if ':' in line and not line.startswith('  '):
            key, value = line.split(':', 1)
            current_key = key.strip()
            value = value.strip()
            if value == '':
                metadata[current_key] = []
                in_list = True
            else:
                metadata[current_key] = value.strip('"\'')
                in_list = False
        elif in_list and current_key and line.startswith('  - '):
            metadata.setdefault(current_key, []).append(line[4:].strip().strip('"\''))
    return metadata, body


def parse_book_file(filepath: Path):
    metadata, body = extract_frontmatter_and_body(filepath)
    slug = filepath.stem
    title = metadata.get('title', '')
    author = metadata.get('author', '')
    isbn13 = metadata.get('isbn13', '') or metadata.get('isbn', '')
    amazon = metadata.get('amazonUrl', '')
    bookshop = metadata.get('bookshopUrl', '')
    capital = metadata.get('capitalBooksUrl', '')
    why_read = metadata.get('whyRead', '')
    desc = metadata.get('description', '')

    has_amazon = bool(amazon) and 'ASIN' not in amazon
    has_bookshop = bool(bookshop)
    has_capital = bool(capital)
    has_placeholder_amazon = 'ASIN' in amazon if amazon else False
    body_text = body.strip()
    body_len = len(body_text)
    has_sections = '## Why You Should Read This' in body_text or '## Why This Book Was Banned' in body_text
    has_real_body = body_len > max(len(desc) + len(why_read) + 80, 450)

    if has_amazon and has_bookshop and has_capital and has_real_body:
        completeness = 'complete'
    elif has_placeholder_amazon or not (has_amazon and has_bookshop and has_capital):
        completeness = 'incomplete_affiliate'
    elif not has_real_body:
        completeness = 'incomplete_content'
    else:
        completeness = 'partial'

    return {
        'slug': slug,
        'title': title,
        'normalizedTitle': normalize_title(title),
        'author': author,
        'normalizedAuthor': normalize_author(author),
        'isbn13': isbn13,
        'publisher': metadata.get('publisher', ''),
        'datePublished': metadata.get('datePublished', ''),
        'filepath': str(filepath.relative_to(BASE_DIR)),
        'hasAmazon': has_amazon,
        'hasBookshop': has_bookshop,
        'hasCapitalBooks': has_capital,
        'hasPlaceholderAmazon': has_placeholder_amazon,
        'bodyLength': body_len,
        'hasRealBody': has_real_body,
        'completenessStatus': completeness,
    }


def build_inventory():
    return [parse_book_file(md_file) for md_file in sorted(BOOKS_DIR.glob('*.md'))]


def build_legacy_inventory(inventory_rows):
    legacy = {}
    for row in inventory_rows:
        legacy[row['slug']] = {
            'title': row['title'],
            'author': row['author'],
            'isbn': row['isbn13'],
            'published': row['datePublished'],
            'category': '',
        }
    return legacy


def build_lookup(inventory_rows):
    by_slug = {row['slug']: row for row in inventory_rows}
    by_isbn = {}
    by_title_author = {}
    for row in inventory_rows:
        if row['isbn13']:
            by_isbn.setdefault(row['isbn13'], []).append(row['slug'])
        key = f"{row['normalizedTitle']} | {row['normalizedAuthor']}"
        by_title_author.setdefault(key, []).append(row['slug'])
    return {
        'bySlug': by_slug,
        'byIsbn': by_isbn,
        'byTitleAuthor': by_title_author,
    }


def looks_like_variant(candidate_title, existing_title):
    both = f"{candidate_title} {existing_title}".lower()
    return any(hint in both for hint in VARIANT_HINTS)


def reconcile_candidates(candidates, inventory_rows, lookup):
    rows = []
    for cand_slug, cand in candidates.items():
        title = cand.get('title', '')
        author = cand.get('author', '')
        isbn13 = cand.get('isbn', '') or cand.get('isbn13', '') or ''
        norm_title = normalize_title(title)
        norm_author = normalize_author(author)
        match_type = 'missing'
        status = 'missing_ready'
        matched_slug = ''
        notes = ''

        if isbn13 and isbn13 in lookup['byIsbn']:
            matched_slug = lookup['byIsbn'][isbn13][0]
            matched = lookup['bySlug'][matched_slug]
            match_type = 'exact_isbn'
            status = 'exists_complete' if matched['completenessStatus'] == 'complete' else 'exists_incomplete'
            notes = f"ISBN already present in {matched_slug}"
        else:
            key = f"{norm_title} | {norm_author}"
            if key in lookup['byTitleAuthor']:
                matched_slug = lookup['byTitleAuthor'][key][0]
                matched = lookup['bySlug'][matched_slug]
                match_type = 'title_author'
                status = 'exists_complete' if matched['completenessStatus'] == 'complete' else 'exists_incomplete'
                notes = f"Title/author already present in {matched_slug}"
            else:
                best = None
                best_ratio = 0
                for inv in inventory_rows:
                    if norm_author and inv['normalizedAuthor'] != norm_author:
                        continue
                    ratio = SequenceMatcher(None, norm_title, inv['normalizedTitle']).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best = inv
                if best and best_ratio >= 0.85:
                    matched_slug = best['slug']
                    match_type = 'variant' if looks_like_variant(title, best['title']) else 'fuzzy'
                    status = 'manual_review'
                    notes = f"{int(best_ratio*100)}% title match with {best['slug']}"

        rows.append({
            'candidateSlug': cand_slug,
            'title': title,
            'normalizedTitle': norm_title,
            'author': author,
            'isbn13': isbn13,
            'sourceRank': cand.get('rank', ''),
            'sourceList': 'next-batch-candidates.json',
            'priorityTier': 'tier1' if cand.get('rank', 9999) and int(cand.get('rank', 9999)) <= 133 else 'tier2',
            'matchedSlug': matched_slug,
            'matchType': match_type,
            'status': status,
            'existingCompleteness': lookup['bySlug'][matched_slug]['completenessStatus'] if matched_slug and matched_slug in lookup['bySlug'] else '',
            'notes': notes,
        })
    return rows


def save_json(data, path: Path):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def save_csv(rows, path: Path):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fieldnames = list(rows[0].keys())
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print('Building canonical inventory...')
    inventory_rows = build_inventory()
    print(f'📚 Parsed {len(inventory_rows)} books')

    legacy = build_legacy_inventory(inventory_rows)
    save_json(legacy, BASE_DIR / '.inventory-index.json')

    lookup = build_lookup(inventory_rows)
    save_json(inventory_rows, BASE_DIR / 'inventory-index-rich.json')
    save_json({
        'byIsbn': lookup['byIsbn'],
        'byTitleAuthor': lookup['byTitleAuthor'],
    }, BASE_DIR / 'inventory-lookup.json')

    print('✅ Wrote .inventory-index.json, inventory-index-rich.json, inventory-lookup.json')

    if DEFAULT_CANDIDATES.exists():
        candidates = json.loads(DEFAULT_CANDIDATES.read_text(encoding='utf-8'))
        reconciliation = reconcile_candidates(candidates, inventory_rows, lookup)
        save_json(reconciliation, BASE_DIR / 'coverage-reconciliation.json')
        save_csv(reconciliation, BASE_DIR / 'coverage-reconciliation.csv')
        print(f'✅ Wrote coverage-reconciliation.json and coverage-reconciliation.csv ({len(reconciliation)} candidates)')
    else:
        print('ℹ️ No next-batch-candidates.json found, skipped reconciliation output')

    complete = len([r for r in inventory_rows if r['completenessStatus'] == 'complete'])
    incomplete = len(inventory_rows) - complete
    print(f'Complete pages: {complete}')
    print(f'Incomplete/partial pages: {incomplete}')


if __name__ == '__main__':
    main()
