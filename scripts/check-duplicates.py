#!/usr/bin/env python3
"""
IsItBanned Duplicate Detection Script

Usage:
  python3 check-duplicates.py [--candidates candidates.json] [--report-only]

Pre-flight check for new books before commit.
"""

import os
import sys
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

BOOKS_DIR = "src/content/books"
PROTOCOL_FILE = ".duplicate-check-protocol.md"


def normalize_title(title):
    """Remove articles, punctuation, lowercase for comparison"""
    t = title.lower().strip() if title else ""
    t = re.sub(r'^(the|a|an)\s+', '', t)  # Remove leading articles
    t = re.sub(r'[^\w\s]', '', t)  # Remove punctuation
    return ' '.join(t.split())


def fuzzy_match(s1, s2, threshold=0.85):
    """Levenshtein-style similarity ratio"""
    if not s1 or not s2:
        return False
    ratio = SequenceMatcher(None, s1, s2).ratio()
    return ratio >= threshold


def build_inventory_index():
    """Parse all existing book files and build searchable index"""
    inventory = {}
    
    if not os.path.exists(BOOKS_DIR):
        print(f"Error: {BOOKS_DIR} not found")
        sys.exit(1)
    
    for filename in sorted(os.listdir(BOOKS_DIR)):
        if not filename.endswith('.md'):
            continue
        
        slug = filename.replace('.md', '')
        filepath = os.path.join(BOOKS_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML frontmatter
            match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                continue
            
            fm = match.group(1)
            
            # Extract key fields
            title_match = re.search(r'title:\s*"([^"]+)"', fm)
            author_match = re.search(r'author:\s*"([^"]+)"', fm)
            isbn_match = re.search(r'isbn13:\s*"([^"]+)"', fm)
            
            title = title_match.group(1) if title_match else None
            author = author_match.group(1) if author_match else None
            isbn = isbn_match.group(1) if isbn_match else None
            
            inventory[slug] = {
                'title': title,
                'author': author,
                'isbn': isbn,
                'filepath': filepath
            }
        except Exception as e:
            print(f"Warning: Could not parse {filename}: {e}")
            continue
    
    return inventory


def check_candidates(candidates, inventory, verbose=False):
    """
    Check candidates against existing inventory.
    
    Args:
        candidates: {slug: {title, author, isbn}, ...}
        inventory: {slug: {title, author, isbn, filepath}, ...}
        verbose: Print detailed reasoning
    
    Returns:
        {slug: {status, reason, existing_slug}}
    """
    results = {}
    
    # Build quick lookup indices
    isbn_index = {}
    title_author_index = {}
    
    for slug, data in inventory.items():
        if data.get('isbn'):
            isbn_index[data['isbn']] = slug
        
        if data.get('title') and data.get('author'):
            norm_key = f"{normalize_title(data['title'])} | {data['author'].lower().strip()}"
            title_author_index[norm_key] = slug
    
    # Check each candidate
    for c_slug, c_data in candidates.items():
        c_isbn = c_data.get('isbn', '').strip()
        c_title = c_data.get('title', '').strip()
        c_author = c_data.get('author', '').strip()
        c_norm_title = normalize_title(c_title)
        c_norm_author = c_author.lower().strip()
        
        status = "✅ CLEAN"
        reason = "No conflicts found"
        existing_slug = None
        
        # 1. ISBN check (highest priority)
        if c_isbn and c_isbn in isbn_index:
            existing_slug = isbn_index[c_isbn]
            status = "❌ DUPLICATE"
            reason = f"ISBN {c_isbn} already exists"
            results[c_slug] = {'status': status, 'reason': reason, 'existing': existing_slug}
            if verbose:
                print(f"  {c_slug}: {status} - {reason} as {existing_slug}")
            continue
        
        # 2. Normalized title + author check
        c_norm_key = f"{c_norm_title} | {c_norm_author}"
        if c_norm_key in title_author_index:
            existing_slug = title_author_index[c_norm_key]
            
            # Check if legitimate variant (volume, edition, etc)
            is_variant = any(x in c_title.lower() for x in [
                'vol.', 'volume', 'edition', 'graphic', 'revised', 'expanded',
                'reissue', 'special', 'deluxe', 'anniversary', 'illustrated'
            ])
            
            if is_variant:
                status = "⚠️  VARIANT"
                reason = f"Edition/volume variant of {existing_slug}"
            else:
                status = "❌ DUPLICATE"
                reason = f"Exact title/author match with {existing_slug}"
            
            results[c_slug] = {'status': status, 'reason': reason, 'existing': existing_slug}
            if verbose:
                print(f"  {c_slug}: {status} - {reason}")
            continue
        
        # 3. Fuzzy match as last resort
        for e_slug, e_data in inventory.items():
            e_norm_title = normalize_title(e_data.get('title', ''))
            e_norm_author = (e_data.get('author', '') or '').lower().strip()
            
            if c_norm_author == e_norm_author and fuzzy_match(c_norm_title, e_norm_title, threshold=0.85):
                similarity = int(SequenceMatcher(None, c_norm_title, e_norm_title).ratio() * 100)
                status = "⚠️  FUZZY"
                reason = f"{similarity}% match with {e_slug} (same author, similar title)"
                results[c_slug] = {'status': status, 'reason': reason, 'existing': e_slug}
                existing_slug = e_slug
                if verbose:
                    print(f"  {c_slug}: {status} - {reason}")
                break
        
        if c_slug not in results:
            results[c_slug] = {'status': status, 'reason': reason, 'existing': None}
            if verbose:
                print(f"  {c_slug}: {status}")
    
    return results


def print_report(results):
    """Print human-readable report"""
    clean = [k for k, v in results.items() if v['status'] == '✅ CLEAN']
    variants = [k for k, v in results.items() if '⚠️' in v['status']]
    duplicates = [k for k, v in results.items() if '❌' in v['status']]
    
    print(f"\n{'='*60}")
    print(f"DUPLICATE CHECK REPORT")
    print(f"{'='*60}\n")
    
    print(f"✅ CLEAN:      {len(clean)} books safe to add")
    print(f"⚠️  VARIANTS:   {len(variants)} books (need manual review)")
    print(f"❌ DUPLICATES: {len(duplicates)} books (BLOCK)")
    print(f"\nTotal candidates: {len(results)}")
    
    if duplicates:
        print(f"\n{'─'*60}")
        print(f"❌ DUPLICATES (MUST REMOVE OR MERGE):\n")
        for slug in sorted(duplicates):
            v = results[slug]
            print(f"  {slug}")
            print(f"    Reason: {v['reason']}")
            if v['existing']:
                print(f"    Existing: {v['existing']}")
            print()
    
    if variants:
        print(f"\n{'─'*60}")
        print(f"⚠️  VARIANTS (REVIEW BEFORE ADDING):\n")
        for slug in sorted(variants):
            v = results[slug]
            print(f"  {slug}")
            print(f"    Reason: {v['reason']}")
            if v['existing']:
                print(f"    Existing: {v['existing']}")
            print()
    
    if clean and (len(clean) <= 10):
        print(f"\n{'─'*60}")
        print(f"✅ CLEAN (SAFE TO ADD):\n")
        for slug in sorted(clean):
            print(f"  {slug}")
        print()
    
    print(f"{'='*60}\n")
    
    # Exit code
    if duplicates:
        return 2  # BLOCK
    elif variants:
        return 1  # WARNING
    else:
        return 0  # OK


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for duplicate books in IsItBanned')
    parser.add_argument('--candidates', help='JSON file with candidate books', type=str)
    parser.add_argument('--verbose', '-v', help='Verbose output', action='store_true')
    parser.add_argument('--report-only', help='Print report and exit (no file checking)', action='store_true')
    parser.add_argument('--show-protocol', help='Print duplicate check protocol', action='store_true')
    
    args = parser.parse_args()
    
    # Show protocol if requested
    if args.show_protocol:
        if os.path.exists(PROTOCOL_FILE):
            with open(PROTOCOL_FILE, 'r') as f:
                print(f.read())
        else:
            print(f"Protocol file not found: {PROTOCOL_FILE}")
        return 0
    
    # Load candidates
    candidates = {}
    if args.candidates:
        try:
            with open(args.candidates, 'r') as f:
                candidates = json.load(f)
        except Exception as e:
            print(f"Error loading candidates: {e}")
            sys.exit(1)
    else:
        # Try to read from stdin or show usage
        print("No candidates provided. Usage:")
        print("  python3 check-duplicates.py --candidates new_books.json")
        print("  python3 check-duplicates.py --show-protocol")
        sys.exit(1)
    
    # Build inventory
    print("📚 Building inventory index...")
    inventory = build_inventory_index()
    print(f"   Loaded {len(inventory)} existing books")
    
    # Check candidates
    print(f"🔍 Checking {len(candidates)} candidates...\n")
    results = check_candidates(candidates, inventory, verbose=args.verbose)
    
    # Print report
    exit_code = print_report(results)
    
    # Save results to JSON if not report-only
    if not args.report_only:
        results_file = "duplicate-check-results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to: {results_file}")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
