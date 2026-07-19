# StoryGraph Automation via Claude-in-Chrome

**Extracted:** 2026-07-18
**Context:** Managing the user's StoryGraph library (username `freidelosc`) — reading the library, adding books, setting the Up Next queue, pinning editions/translations, exporting data.

## Problem

StoryGraph has no public API, and its Cloudflare JS challenge blocks both WebFetch and curl (even with a browser user-agent — you get "Just a moment…"). Profile pages also require login. Naive scraping is a dead end.

## Solution

Drive the user's real logged-in Chrome session via Claude-in-Chrome (the Mac Mini's Chrome is signed in). Key mechanics discovered:

- **Membership check (fastest primitive):** `https://app.thestorygraph.com/search-to-read/<pile-uuid>?search_to_read=<query>` searches only the to-read pile. The pile UUID is stable per user (freidelosc: `57e9ff5e-afa5-43ad-94c8-bc070d32474d`). Also searches author names.
- **Adding a book:** `https://app.thestorygraph.com/browse?search_term=<title+author>` → first result's teal "to read" button (≈ (893–899, 186) at 1568px viewport). **Button state matters:** solid teal = not shelved, white/outlined = already shelved — check before clicking or you'll un-shelve. Verify each add via the search-to-read URL.
- **Enumerating shelves:** `books-read/<user>`, `to-read/<user>`, `currently-reading/<user>` use infinite scroll — scroll in batches, then one `get_page_text` captures everything loaded so far (text accumulates; no need to capture per-scroll).
- **Editions/translations:** each book page's "N editions" link → editions page has per-edition **"switch to this edition"** buttons ("Move your reading history to this edition"). Translations are usually *editions* of one canonical entry (Gilgamesh), but sometimes separate books (Headley's *Beowulf: A New Translation*) — search both ways.
- **Up Next queue:** max 5 books; "add to 'up next'" buttons live on to-read search result rows; order = insertion order.
- **CSV export:** `https://app.thestorygraph.com/user-export` → Generate export → refresh → Download link. **Chrome may leave the finished file as an unrenamed `.com.google.Chrome.XXXXXX` temp file in `~/Downloads`** — it's complete despite the name; find it by mtime, copy it out, and analyze with python csv (columns: Title, Authors, ISBN/UID, Read Status, Star Rating, Date Added, …).

## Workflow for "add these N books"

Pipeline one round-trip per book: batch `[click prev result's to-read button, navigate to next search, screenshot]` — the screenshot verifies the *next* book's first result before the following batch clicks it.

## Related: researching book-club lists

- Defector's archive pagination ignores `?page=N` (returns page 1 silently — verify content actually changes!); real pagination is the "Older" link with a base64 `?after=` cursor. Click through in-browser.
- A club's Bookshop.org list can lag/omit selections (missed 5 of ~33 for Defector Reads A Book); crawl the article archive for announcement posts, which also name the **specific translation** chosen (e.g. Helle's Gilgamesh, Harman's Castle) — cross-check ISBNs before assuming a shelved copy matches.

## When to Use

Any StoryGraph task ("what should I read next", "add X to my TBR", "check my reading stats"), or scraping cursor-paginated archives that fake-accept `?page=` params.
