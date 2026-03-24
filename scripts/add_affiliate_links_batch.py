#!/usr/bin/env python3
"""Add affiliate links to book .md files using Open Library API to find ISBN-10.
Uses curl for HTTPS requests to avoid Python SSL cert issues."""

import os
import sys
import json
import time
import subprocess
import urllib.parse
import yaml
import re

BOOKS_DIR = "/Users/rossrojek/.openclaw/workspace/isitbanned/src/content/books"
AFFILIATE_TAG = "isitbanned-20"
BOOKSHOP_ID = "2537"
PROGRESS_FILE = "/Users/rossrojek/.openclaw/workspace/isitbanned/scripts/affiliate_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed": [], "skipped": [], "failed": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def is_valid_isbn10(isbn):
    if len(isbn) != 10:
        return False
    return isbn[:9].isdigit() and (isbn[9].isdigit() or isbn[9] == 'X')

def isbn13_to_isbn10(isbn13):
    isbn13 = isbn13.replace("-", "").strip()
    if len(isbn13) != 13 or not isbn13.startswith("978"):
        return None
    core = isbn13[3:12]
    total = sum(int(d) * (i + 1) for i, d in enumerate(core))
    check = total % 11
    check_char = "X" if check == 10 else str(check)
    return core + check_char

def search_openlibrary(title, author):
    """Search Open Library for a book and return ISBN-10 and ISBN-13."""
    title_clean = re.sub(r'[^\w\s]', ' ', title).strip()
    # Take first author if multiple
    author_clean = re.sub(r'[^\w\s]', ' ', author.split('&')[0].split(',')[0]).strip()
    
    params = urllib.parse.urlencode({
        'title': title_clean,
        'author': author_clean,
        'limit': 1,
        'fields': 'isbn'
    })
    url = f"https://openlibrary.org/search.json?{params}"
    
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None, None
        data = json.loads(result.stdout)
    except Exception as e:
        return None, None
    
    docs = data.get('docs', [])
    if not docs or 'isbn' not in docs[0]:
        return None, None
    
    isbns = docs[0]['isbn']
    isbn10 = None
    isbn13 = None
    
    for isbn in isbns:
        isbn = isbn.strip()
        if len(isbn) == 13 and isbn.startswith('978') and isbn.isdigit():
            if isbn13 is None:
                isbn13 = isbn
        elif is_valid_isbn10(isbn):
            if isbn10 is None:
                isbn10 = isbn
        if isbn10 and isbn13:
            break
    
    # If we have isbn13 but no isbn10, try to convert
    if isbn13 and not isbn10:
        isbn10 = isbn13_to_isbn10(isbn13)
    
    return isbn10, isbn13

def get_books_needing_links():
    books = []
    for f in sorted(os.listdir(BOOKS_DIR)):
        if not f.endswith('.md'):
            continue
        filepath = os.path.join(BOOKS_DIR, f)
        with open(filepath) as fh:
            content = fh.read()
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except:
            continue
        if not fm:
            continue
        if 'amazonUrl' in fm:
            continue
        tc = fm.get('totalChallenges', 0) or 0
        books.append((tc, f, fm.get('title', ''), fm.get('author', ''), fm.get('isbn13', '')))
    
    books.sort(key=lambda x: -x[0])
    return books

def add_links_to_file(filename, isbn10, isbn13=None):
    filepath = os.path.join(BOOKS_DIR, filename)
    with open(filepath) as fh:
        content = fh.read()
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False
    
    fm_text = parts[1]
    body = parts[2]
    
    amazon_url = f"https://www.amazon.com/dp/{isbn10}/ref=nosim?tag={AFFILIATE_TAG}"
    
    new_fields = f'amazonUrl: "{amazon_url}"\n'
    if isbn13:
        bookshop_url = f"https://bookshop.org/a/{BOOKSHOP_ID}/{isbn13}"
        capital_url = f"https://store.capitalbooksonk.com/browse/filter/t/{isbn13}/k/keyword"
        new_fields += f'bookshopUrl: "{bookshop_url}"\n'
        new_fields += f'capitalBooksUrl: "{capital_url}"\n'
    
    new_content = f'---{fm_text.rstrip()}\n{new_fields}---{body}'
    
    with open(filepath, 'w') as fh:
        fh.write(new_content)
    
    return True

def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    progress = load_progress()
    already_done = set(progress["processed"] + progress["skipped"] + progress["failed"])
    
    books = get_books_needing_links()
    todo = [(tc, f, t, a, i) for tc, f, t, a, i in books if f not in already_done]
    
    print(f"Total needing links: {len(books)}")
    print(f"Already attempted: {len(already_done)}")
    print(f"Remaining: {len(todo)}")
    print(f"Processing batch of {batch_size}...")
    print()
    
    batch = todo[:batch_size]
    batch_processed = 0
    batch_skipped = 0
    
    for i, (tc, filename, title, author, existing_isbn13) in enumerate(batch):
        print(f"[{i+1}/{len(batch)}] {title} by {author} (challenges: {tc})")
        
        isbn10, found_isbn13 = search_openlibrary(title, author)
        
        isbn13 = str(existing_isbn13) if existing_isbn13 else found_isbn13
        
        if not isbn10:
            print(f"  -> SKIP: No ISBN-10 found")
            progress["skipped"].append(filename)
            batch_skipped += 1
            time.sleep(0.3)
            continue
        
        print(f"  -> ISBN-10: {isbn10}, ISBN-13: {isbn13 or 'none'}")
        
        if add_links_to_file(filename, isbn10, isbn13):
            progress["processed"].append(filename)
            batch_processed += 1
            print(f"  -> Added links")
        else:
            progress["failed"].append(filename)
            print(f"  -> FAILED")
        
        time.sleep(0.3)
    
    save_progress(progress)
    
    print()
    print(f"=== Batch Complete ===")
    print(f"Processed: {batch_processed}")
    print(f"Skipped: {batch_skipped}")
    print(f"Total done so far: {len(progress['processed'])} processed, {len(progress['skipped'])} skipped, {len(progress['failed'])} failed")
    print(f"Remaining: {len(todo) - len(batch)}")

if __name__ == "__main__":
    main()
