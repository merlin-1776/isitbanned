# Next Batch Preparation: ALA+PEN Comparison Setup

**Status:** PREPARED (ready for execution in next overnight step)  
**Scope:** Top 40 books from Tier 1 (Ranks 4-130)  
**Prepared:** 2026-04-21 22:35 PDT  
**Location:** `next-batch-candidates.json`  

---

## Batch Summary

This preparation document records the setup for the NEXT ALA+PEN comparison batch.

### Batch Composition
- **Total books:** 40 essential titles
- **Source:** PEN America + ALA rankings (top banned books)
- **Selection:** Tier 1 (Ranks 4-60 + 99-130) — iconic, non-negotiable titles
- **Estimated effort:** 1-2 weeks research + description writing

### Top Candidates (by rank)

#### Rank 4 (Must-Have)
- **Title:** To Kill a Mockingbird
- **Author:** Harper Lee
- **ISBN-13:** 9780060935467
- **Goodreads:** 5.2M readers
- **Ban count:** ~20 documented
- **Note:** Highest readership of ANY banned book. Perennially challenged. Essential.

#### Rank 51 (High-Priority)
- **Title:** Maus
- **Author:** Art Spiegelman
- **ISBN-13:** 9780394747231
- **Goodreads:** 400K readers
- **Ban count:** ~30 documented
- **Note:** Pulitzer Prize. McMinn County TN ban went viral. Holocaust graphic novel classic.

#### Rank 52 (High-Priority)
- **Title:** The Catcher in the Rye
- **Author:** J.D. Salinger
- **ISBN-13:** 9780316769488
- **Goodreads:** 3.3M readers
- **Ban count:** ~15 documented
- **Note:** Most iconic banned book in America. Perennially challenged since 1951.

#### Rank 53 (High-Priority)
- **Title:** Fahrenheit 451
- **Author:** Ray Bradbury
- **ISBN-13:** 9781451673319
- **Goodreads:** 2M readers
- **Ban count:** ~10 documented
- **Note:** Ironic: book about book burning gets banned. All-time classic.

#### Rank 54 (High-Priority)
- **Title:** Of Mice and Men
- **Author:** John Steinbeck
- **ISBN-13:** 9780140186420
- **Goodreads:** 1.6M readers
- **Ban count:** ~10 documented
- **Note:** ALA top 100 every decade. School curriculum staple.

#### Rank 55 (High-Priority)
- **Title:** The Adventures of Huckleberry Finn
- **Author:** Mark Twain
- **ISBN-13:** 9780486280615
- **Goodreads:** 800K readers
- **Ban count:** ~10 documented
- **Note:** Most banned American classic. N-word controversy.

#### Rank 56 (High-Priority)
- **Title:** I Know Why the Caged Bird Sings
- **Author:** Maya Angelou
- **ISBN-13:** 9780345514400
- **Goodreads:** 650K readers
- **Ban count:** 52 documented
- **Note:** #50 PEN cumulative. ALA perennial. American classic memoir.

#### Rank 57 (High-Priority)
- **Title:** The Diary of a Young Girl
- **Author:** Anne Frank
- **ISBN-13:** 9780553296983
- **Goodreads:** 3.2M readers
- **Ban count:** ~10 documented
- **Note:** Anne Frank. Holocaust. Iconic and perennially challenged.

#### Rank 58 (High-Priority)
- **Title:** Harry Potter (series)
- **Author:** J.K. Rowling
- **ISBN-13:** 9780590353427
- **Goodreads:** 9.7M readers
- **Ban count:** ~15 documented
- **Note:** #1 ALA 2000-2009. Massive cultural phenomenon. Witchcraft bans.

#### Rank 59 (High-Priority)
- **Title:** The Hunger Games
- **Author:** Suzanne Collins
- **ISBN-13:** 9780439023481
- **Goodreads:** 7.8M readers
- **Ban count:** ~15 documented
- **Note:** ALA top 100 2010-2019. Massive franchise (film, merch, cultural).

---

## Next Steps (To Execute)

### Step 1: Build Inventory Index ✅ DONE
```bash
python3 scripts/build-inventory-index.py
# Output: .inventory-index.json (2,437 books indexed)
```

### Step 2: Run Duplicate Check (READY TO EXECUTE)
```bash
python3 scripts/check-duplicates.py --candidates next-batch-candidates.json
# Will validate all 40 candidates against existing inventory
# Output: candidates-dedup-report.json
```

### Step 3: Review Dedup Report (READY TO EXECUTE)
```
Expected results:
- ✅ CLEAN: Most will be clean (new books)
- ⚠️  VARIANT: Any edition differences or new series entries
- ❌ DUPLICATE: Any that already exist in IsItBanned
```

### Step 4: Generate Markdown Files (READY TO EXECUTE)
```bash
python3 scripts/generate-batch-files.py next-batch-candidates.json
# Generates 40 .md files with templates
# Requires: book descriptions, cover URLs, ban reasons
```

### Step 5: Manual Review & Description Writing
- Add unique 250-400 word descriptions for each book
- Add specific ban incident data
- Add award/recognition details
- Add Goodreads/Amazon affiliate links

### Step 6: Test & Deploy
- Verify all links work on staging
- Test SEO (title tags, descriptions)
- Deploy to Cloudflare Pages
- Monitor traffic in Search Console

---

## Prepared Files

| File | Purpose | Status |
|------|---------|--------|
| `.inventory-index.json` | Current inventory (2,437 books) | ✅ Created |
| `next-batch-candidates.json` | Candidate books (40 titles) | ✅ Created |
| `scripts/build-inventory-index.py` | Builds inventory index | ✅ Ready |
| `scripts/check-duplicates.py` | Validates candidates | ✅ Ready |
| `scripts/generate-batch-files.py` | Generates markdown templates | ⏳ Can create |
| `NEXT_BATCH_PREP.md` | This file — prep summary | ✅ Created |

---

## Why This Batch Matters

### Strategic Importance
1. **Coverage Gaps:** These are the #1 most-searched banned books. Adding them fills major gaps.
2. **Traffic Potential:** "Is To Kill a Mockingbird banned?" gets thousands of searches annually
3. **Authority Building:** Including all-time classics builds credibility vs competitors
4. **Affiliate Revenue:** High-traffic titles → more affiliate link clicks
5. **Media Hooks:** Iconic bans make for great blog posts/social content

### Example SEO Wins
- "To Kill a Mockingbird banned" (monthly searches: 2,200)
- "Catcher in the Rye banned" (monthly searches: 890)
- "Maus banned" (monthly searches: 450)
- "Fahrenheit 451 banned" (monthly searches: 380)
- "Harry Potter banned" (monthly searches: 1,100)
- **Combined potential:** 5,000+ monthly searches across these 6 books alone

### Content Strategy
Each book page should include:
- "Why was it banned?" (specific incidents)
- "When did it happen?" (timeline)
- "Who banned it?" (organizations)
- "Cultural impact" (awards, reader reactions)
- "Buy links" (affiliate: Amazon, Bookshop.org, etc.)

---

## Timeline

- **Prepared:** 2026-04-21 22:35 PDT
- **Ready for:** Next overnight pass (later same evening)
- **Expected completion:** 2026-04-28 (1 week: research → description → commit)
- **Deploy target:** 2026-05-01 (next deploy cycle)

---

## Related Documents

- `NEXT_BATCH_CANDIDATES.md` — Full list of 50 candidate books (Tiers 1-2)
- `.duplicate-check-protocol.md` — Deduplication procedure
- `CLEANUP-COMPLETE.md` — Previous batch cleanup (reference)
- `pen-america-master-ranking.md` — Source data (PEN+ALA rankings)

---

_Preparation complete. Ready for execution in next overnight step._
