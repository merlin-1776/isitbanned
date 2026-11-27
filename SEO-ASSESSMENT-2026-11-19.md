# IsItBanned SEO Agent — First Assessment

**Run date:** 2026-11-19  
**Scope:** Read-only first operational run: site foundations, Search Console opportunity scan, on-page/content trust review, and existing brand-context validation. No site edits or publication.

## Inputs and freshness

- Existing brand context: `brand-voice.md` (created 2026-04-18); it already covers positioning, audience language, tone, and claim constraints, so the brand interview was not repeated.
- Search Console property: `sc-domain:isitbanned.com`, accessed with the assigned side-project account (`merlin@1776productions.com`); window **2026-08-21–2026-11-16** (latest date queried, not live-through-today data).
- Live pages and crawl files fetched 2026-11-19.
- The older `Ops/SEO/legacy/seo-agent/reports/2026-04-18-isitbanned-gap-analysis.md` is a historical baseline, not treated as current evidence.

## Executive summary

The technical crawl/indexation foundation is working: the homepage, book index, About page, representative book page, `robots.txt`, and sitemap index returned HTTP 200. Google URL Inspection reports the homepage, `/books/`, `/about/`, and `/books/1984/` as **Submitted and indexed**, with successful mobile crawls and Google/user canonical agreement.

The most important issue is structured-data accuracy, not a missing schema layer. Every book page currently emits a hard-coded 4.5/5 `AggregateRating` with one review, though no such rating/review is displayed in the page content. Search Console detects **Review snippets** on the inspected 1984 page. Separately, the book template labels each record “BANNED” / “Yes, [title] Is Banned” while the visible site promise and data describe both banned **and challenged** books. These need a factuality pass before more SEO expansion.

## Search Console receipts

Search Console returned 748 page rows for the 90-day window. Summing those rows gives **2,625 impressions and 110 clicks** (4.2% row-weighted CTR).

| Page | Impressions | Clicks | CTR | Avg. position | Readout |
|---|---:|---:|---:|---:|---|
| `/books/` | 555 | 1 | 0.18% | 27.9 | Largest visible landing-page opportunity; mostly page-two-or-lower visibility and very few clicks. |
| `/` | 25 | 8 | 32.0% | 19.4 | Small sample; do not generalize from the high CTR. |
| `/about/` | 19 | 5 | 26.3% | 8.5 | Small but positive result; preserve what is working. |
| `/books/to-kill-a-mockingbird/` | 117 | 0 | 0% | 88.3 | Visibility is far back; investigate intent/data fit before rewriting. |
| `/books/1984/` | 68 | 0 | 0% | 84.5 | Same pattern; not yet a page-one refresh candidate. |

The visible query report contained 293 rows / 469 impressions, substantially below the page-row total because Search Console does not expose every query (including anonymized queries). **No returned query/page row met both 5+ impressions and average position 5–20.** The data therefore does not yet support a confident “quick-win keyword” claim. Do not infer missing demand from the hidden query share.

## Foundation and trust checks

- **Crawlability:** `robots.txt` is live (200), allows general and named search/AI crawlers, and references `https://isitbanned.com/sitemap-index.xml`; sitemap index is live (200).
- **Search Console indexation:** sampled home, books hub, About, and 1984 URLs pass URL Inspection; all are mobile-crawled, indexing-allowed, and have matching user/Google canonicals. Crawl dates range from 2026-09-23 (`/books/`) to 2026-11-07 (home), so inspection is a sample, not proof of whole-site coverage.
- **Sitemap submission record:** Search Console’s sitemap-list call returned `null`; this did not surface a submission record. The live sitemap is still discoverable through `robots.txt`. Verify the property UI/API record before calling sitemap submission complete.
- **Schema:** homepage source includes `WebSite`, `Organization`, and FAQ markup matching visible FAQ copy; book pages include `Book`, FAQ, and breadcrumbs. However, `src/components/BookSchema.astro` hard-codes `AggregateRating` at 4.5 with `reviewCount: 1` for every title (lines 74–80). Google detects a Review snippet on the inspected 1984 URL. A passing inspection is not evidence that the rating data is true or that Google will display a rich result.
- **Status language:** book template uses a universal “BANNED” stamp and “Yes, … Is Banned!” title, while `/about/` defines the product as tracking books “banned or challenged.” The template supplies challenge counts/locations but no per-record status flag in its props. Clarify the underlying evidence and distinguish challenged, restricted, and removed records where the data permits; avoid blanket claims when it does not.
- **Freshness/methodology:** About page names ALA and PEN America but says records are updated “regularly” without a visible as-of date, update cadence, inclusion rule, or per-record source trail. That weakens verification for a time-sensitive database.
- **Analytics:** the assigned Google account lookup did not surface a GA4 account/property in this pass, so no landing-page conversion or AI-referrer layer is included.
- **Performance:** Core Web Vitals/PageSpeed were not measured in this first pass; no performance score is claimed.

## Prioritized next actions

### Search for Agents pilot — added 2026-11-26

- **Status: planned, not enabled.** Ross requested an IsItBanned pilot and inclusion in the SEO roadmap. The live `/.well-known/search?q=1984` returned the site's HTML homepage, not search results, on 2026-11-26.
- **Owner:** Merlin. Enable Cloudflare Search for Agents for `isitbanned.com` after confirming the account's billing plan, usage, and an acceptable cost limit or receiving Ross's approval for usage charges. Cloudflare says billing starts 2026-12-01; included monthly usage is 5 million ingestion tokens, 10 GB-month storage, 1,000 semantic and 1,000 full-text queries per account; overages are usage-priced. The default public endpoint can receive third-party queries.
- **Verify:** allow indexing to complete; check discovery metadata and test title, author, and state queries at `/.well-known/search`; check indexed coverage and whether results link to accurate source pages. Record current usage and periodically review agent requests, costs, and any measurable referrals. Establish a baseline before attributing traffic changes to the pilot.
- **Expansion:** evaluate other owned sites only after the pilot; CBR infrastructure changes require Ross's approval and Staff coordination. This does not replace conventional SEO or guarantee AI citations or referral traffic.
- **Sources:** https://blog.cloudflare.com/search-for-agents/ and https://developers.cloudflare.com/ai-search/platform/limits-pricing/

1. **Correct trust-critical book data signals.** Remove the fabricated rating markup unless genuine, visible review data exists; separately audit the universal “banned” labeling against record-level source evidence and define the challenged/restricted/removed distinction.
2. **Build an edit card for `/books/` before changing its snippet.** It owns 555 impressions but only one click at average position 27.9. First recover the page’s full query distribution/intent from Search Console where available; then decide whether title/description, hub copy, or internal links are the right lever. No net-new page is justified by this report alone.
3. **Make the dataset verifiable and measurable.** Add a real dataset as-of/methodology/source trail, verify whether the sitemap is registered in Search Console, and resolve GA4 access if it is intended to be part of this site’s measurement loop.

## Limits / deferred

- The web-search provider failed with HTTP 402, so no fresh competitor SERP analysis was completed. The April 18 competitor set is historical and is not presented as current winners.
- Query data is incomplete due to Search Console query privacy; page-level totals are the more complete receipt in this export.
- This is a bounded first pass, not a full crawl, CWV test, or data-by-data accuracy audit.

## Source pointers

- `src/components/BookSchema.astro` — rating and book FAQ markup.
- `src/pages/books/[...slug].astro` — book-page title and universal banned presentation.
- `src/pages/books/index.astro` — books-hub title/intro.
- `src/pages/about.astro` — source, mission, and freshness statements.
- `brand-voice.md` — existing brand interview profile.
