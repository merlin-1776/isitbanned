#!/usr/bin/env python3
"""Add affiliate links to book .md files that have isbn13 but no amazonUrl."""

import os
import sys
import yaml
import re

BOOKS_DIR = "/Users/rossrojek/.openclaw/workspace/isitbanned/src/content/books"
AFFILIATE_TAG = "isitbanned-20"
BOOKSHOP_ID = "2537"

def isbn13_to_isbn10(isbn13: str) -> str | None:
    """Convert ISBN-13 to ISBN-10. Only works for 978-prefix ISBNs."""
    isbn13 = isbn13.replace("-", "").strip()
    if len(isbn13) != 13 or not isbn13.startswith("978"):
        return None
    core = isbn13[3:12]  # 9 digits
    # Calculate check digit
    total = 0
    for i, d in enumerate(core):
        total += int(d) * (i + 1)
    check = total % 11
    check_char = "X" if check == 10 else str(check)
    return core + check_char

def process_books_with_isbn13():
    """Process books that have isbn13 but no amazonUrl."""
    processed = 0
    skipped = 0
    errors = []
    
    files = sorted(os.listdir(BOOKS_DIR))
    for f in files:
        if not f.endswith('.md'):
            continue
        filepath = os.path.join(BOOKS_DIR, f)
        with open(filepath) as fh:
            content = fh.read()
        
        # Skip if already has amazonUrl
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue
        
        fm_text = parts[1]
        body = parts[2]
        
        try:
            fm = yaml.safe_load(fm_text)
        except:
            continue
        if not fm:
            continue
        
        if 'amazonUrl' in fm:
            continue
        
        isbn13 = fm.get('isbn13')
        if not isbn13:
            continue
        
        isbn13 = str(isbn13).strip()
        isbn10 = isbn13_to_isbn10(isbn13)
        if not isbn10:
            errors.append(f"{f}: Could not convert ISBN-13 '{isbn13}' to ISBN-10")
            continue
        
        # Build the new fields
        amazon_url = f"https://www.amazon.com/dp/{isbn10}/ref=nosim?tag={AFFILIATE_TAG}"
        bookshop_url = f"https://bookshop.org/a/{BOOKSHOP_ID}/{isbn13}"
        capital_url = f"https://store.capitalbooksonk.com/browse/filter/t/{isbn13}/k/keyword"
        
        # Add fields to frontmatter - insert before the closing ---
        new_fields = f'amazonUrl: "{amazon_url}"\nbookshopUrl: "{bookshop_url}"\ncapitalBooksUrl: "{capital_url}"\n'
        
        # Reconstruct: add new fields at end of frontmatter
        new_content = f'---{fm_text.rstrip()}\n{new_fields}---{body}'
        
        with open(filepath, 'w') as fh:
            fh.write(new_content)
        
        processed += 1
    
    print(f"Processed: {processed}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(f"  {e}")

if __name__ == "__main__":
    process_books_with_isbn13()
