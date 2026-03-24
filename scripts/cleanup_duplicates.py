#!/usr/bin/env python3
"""Clean up duplicate affiliate link fields and ensure correct ISBN-10 from isbn13."""

import os
import re
import yaml

BOOKS_DIR = "/Users/rossrojek/.openclaw/workspace/isitbanned/src/content/books"
AFFILIATE_TAG = "isitbanned-20"
BOOKSHOP_ID = "2537"

def isbn13_to_isbn10(isbn13):
    isbn13 = str(isbn13).replace("-", "").strip()
    if len(isbn13) != 13 or not isbn13.startswith("978"):
        return None
    core = isbn13[3:12]
    total = sum(int(d) * (i + 1) for i, d in enumerate(core))
    check = total % 11
    check_char = "X" if check == 10 else str(check)
    return core + check_char

def cleanup():
    fixed = 0
    for f in sorted(os.listdir(BOOKS_DIR)):
        if not f.endswith('.md'):
            continue
        filepath = os.path.join(BOOKS_DIR, f)
        with open(filepath) as fh:
            content = fh.read()
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue
        
        fm_text = parts[1]
        body = parts[2]
        
        # Check for duplicate fields
        lines = fm_text.strip().split('\n')
        seen_keys = {}
        has_dupes = False
        
        for line in lines:
            if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                key = line.split(':')[0].strip()
                if key in seen_keys:
                    has_dupes = True
                    break
                seen_keys[key] = True
        
        if not has_dupes:
            continue
        
        # Parse frontmatter properly, removing duplicates
        try:
            fm = yaml.safe_load(fm_text)
        except:
            continue
        if not fm:
            continue
        
        isbn13 = fm.get('isbn13')
        
        # If we have isbn13, recalculate the correct ISBN-10
        if isbn13:
            isbn13_str = str(isbn13).strip()
            isbn10 = isbn13_to_isbn10(isbn13_str)
            if isbn10:
                fm['amazonUrl'] = f"https://www.amazon.com/dp/{isbn10}/ref=nosim?tag={AFFILIATE_TAG}"
                fm['bookshopUrl'] = f"https://bookshop.org/a/{BOOKSHOP_ID}/{isbn13_str}"
                fm['capitalBooksUrl'] = f"https://store.capitalbooksonk.com/browse/filter/t/{isbn13_str}/k/keyword"
        
        # Rebuild frontmatter without duplicates, preserving order
        # We need to rebuild carefully to maintain YAML format
        new_lines = []
        seen = set()
        in_list = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this is a top-level key
            if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                key = line.split(':')[0].strip()
                if key in seen:
                    # Skip duplicate - but also skip any following list items
                    in_list = True
                    continue
                seen.add(key)
                in_list = False
                
                # If this key was recalculated, use new value
                if key in ('amazonUrl', 'bookshopUrl', 'capitalBooksUrl') and key in fm:
                    val = fm[key]
                    new_lines.append(f'{key}: "{val}"')
                    continue
            elif in_list and (line.startswith(' ') or line.startswith('-')):
                continue
            else:
                in_list = False
            
            new_lines.append(line)
        
        new_fm = '\n'.join(new_lines)
        new_content = f'---\n{new_fm}\n---{body}'
        
        with open(filepath, 'w') as fh:
            fh.write(new_content)
        
        fixed += 1
        print(f"Fixed: {f}")
    
    print(f"\nTotal fixed: {fixed}")

if __name__ == "__main__":
    cleanup()
