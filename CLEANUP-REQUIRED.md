# Cleanup Required - Latest Batch Duplicates

**Status**: Found during 2026-04-21 audit  
**Action**: MUST resolve before next batch

---

## Critical Issues (ISBN Duplicates - Must Delete One)

### 1. His Dark Materials (Duplicate)
- **Issue**: Created `his-dark-materials.md` but `the-golden-compass.md` already exists
- **ISBN**: 9780440238133 (same book, different slug)
- **Action**: 
  ```bash
  # DELETE the newer file (created 2026-04-21):
  rm src/content/books/his-dark-materials.md
  
  # KEEP: src/content/books/the-golden-compass.md (original)
  ```
- **Reason**: Both refer to Philip Pullman's "The Golden Compass" (same ISBN). The original slug is better.

### 2. The Curious Incident (Duplicate)
- **Issue**: Created `the-curious-incident.md` but `the-curious-incident-of-the-dog-in-the-night-time.md` already exists
- **ISBN**: 9781400032716 (same book)
- **Action**:
  ```bash
  # DELETE the newer file:
  rm src/content/books/the-curious-incident.md
  
  # KEEP: src/content/books/the-curious-incident-of-the-dog-in-the-night-time.md (original)
  ```
- **Reason**: Exact same book. The longer slug is more specific.

---

## Likely Issues (Check & Decide)

### 3. Lord of the Flies (Variant or Duplicate?)
- **Slugs**: `lord-of-the-flies` vs `lord-of-the-flies-expanded` (both created 2026-04-21)
- **ISBN**: TBD - need to verify
- **Decision Needed**:
  - If same ISBN → DELETE one (likely `lord-of-the-flies-expanded` is just poor naming)
  - If different ISBN → Keep both IF one is actually the expanded edition

### 4. Scary Stories (Variant or Duplicate?)
- **Slugs**: `scary-stories` vs `scary-stories-to-tell-in-the-dark`
- **Both exist, different naming**:
  - `scary-stories` (created 2026-04-21)
  - `scary-stories-to-tell-in-the-dark` (pre-existing)
- **Decision**: Probably same book. Check ISBN.

### 5. Gender Queer (Likely Same)
- **Slugs**: `gender-queer` vs `gender-queer-a-memoir`
- **Decision**: Consolidate to one canonical slug. Both point to same book (ISBN 9781549304002).

---

## Remediation Steps

### Step 1: Remove Known Duplicates
```bash
cd /Users/ross/.openclaw/workspace/isitbanned
git rm src/content/books/his-dark-materials.md
git rm src/content/books/the-curious-incident.md
```

### Step 2: Verify Variants
```bash
# Check ISBN for lord-of-the-flies files
grep isbn13 src/content/books/lord-of-the-flies*.md

# Check ISBN for scary-stories files  
grep isbn13 src/content/books/scary-stories*.md

# Check ISBN for gender-queer files
grep isbn13 src/content/books/gender-queer*.md
```

### Step 3: Remove or Consolidate
- If ISBNs are same: delete the variant file
- If ISBNs differ: confirm it's a true edition difference, then add note in YAML

### Step 4: Commit Cleanup
```bash
git commit -m "Cleanup: Remove ISBN-based duplicates from latest batch

Removed:
- his-dark-materials.md (duplicate of the-golden-compass, ISBN 9780440238133)
- the-curious-incident.md (duplicate of the-curious-incident-of-the-dog-in-the-night-time, ISBN 9781400032716)

This reduces duplicate confusion and improves search/SEO performance.

Related: .duplicate-check-protocol.md"
```

### Step 5: Update Duplicate-Check Script
```bash
# The duplicate-check.py script is now in place for future batches
# Test it against the current inventory:
python3 scripts/check-duplicates.py --show-protocol
```

---

## Prevention for Next Batch

**Before adding ANY new books:**
1. Prepare candidates as JSON: `{slug: {title, author, isbn}, ...}`
2. Run: `python3 scripts/check-duplicates.py --candidates new_books.json`
3. Review output:
   - ✅ CLEAN → safe to commit
   - ⚠️  VARIANT → decide
   - ❌ DUPLICATE → remove from batch
4. Only commit after dedup report shows 0 duplicates

---

## Summary

| File | Action | Reason |
|------|--------|--------|
| `his-dark-materials.md` | DELETE | ISBN duplicate of `the-golden-compass` |
| `the-curious-incident.md` | DELETE | ISBN duplicate of long-form slug |
| `lord-of-the-flies-expanded.md` | CHECK | Verify if true edition variant |
| `scary-stories.md` | CHECK | Verify against `scary-stories-to-tell-in-the-dark` |
| `gender-queer*.md` | CONSOLIDATE | Merge into one canonical slug |

---

**Next Steps:**
1. Ross approves cleanup plan
2. Execute deletions and consolidations
3. Commit cleanup
4. Re-test duplicate-check script
5. Proceed to next batch with protocol in place

_Last Updated: 2026-04-21_
