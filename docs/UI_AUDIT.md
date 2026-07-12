# UI Audit — House Hunter Dashboard

**Date:** 2026-07-12 · **Branch:** `audit/ui-defects` (off `master` @ `b97506e`, post-Cycle-6)
**Scope:** observation only — no fixes. This document is the sole input to the
redesign cycle and is written to be self-sufficient (no need to re-run the sweep).

## How this was captured

- **Frontend:** `npm run dev` (Next 16 dev mode) at `http://localhost:3000`.
- **API:** local `api.py` in **production mode** (`ENVIRONMENT=production`) —
  serves the **live Supabase data**, i.e. exact data parity with the deployed
  board. The real Render URL is not present in the repo
  (`frontend/.env.local` points at `localhost:8000`), so this is the sanctioned
  fallback; CORS allowed `localhost:3000`. Default board at capture time:
  **3 cards** (2 New→"Pending", 1 Interested); `include_rejected` reveals ~46.
- **Sweep:** Playwright (Python, repo venv), `device_scale_factor=2`. Script
  committed as [`artifacts/ui-audit/ui_sweep.py`](../artifacts/ui-audit/ui_sweep.py) — rerunnable.
- **Viewports:** mobile 390×844 · tablet 768×1024 · desktop 1440×900.
- **States per viewport (14):** loading, default (Best Fit), 4 other sorts,
  filters_open, include_rejected, long_title, password_modal, status_change
  (auth + POST fully route-mocked — no backend write), empty_board (mocked `[]`),
  api_down (aborted request), null_fields (mocked null deposit/sqft).
- **Screenshots:** `artifacts/ui-audit/{viewport}_{state}.png` (42 files).
- **Dev-mode artifacts in shots:** the Next.js floating badge (bottom-left "N",
  and a red "1 Issue" chip in `api_down` from the deliberately aborted fetch)
  belongs to the dev overlay, not the product. Ignore it in review.

---

## 1. Defect table

Severity: **breaks-usage** > **degrades** > **cosmetic**.

| ID | Severity | Viewport | Screenshot(s) | Description |
|----|----------|----------|---------------|-------------|
| D1 | breaks-usage | mobile | `mobile_default`, `mobile_empty_board`, `mobile_api_down` | **208px horizontal page scroll on a 390px viewport** (measured `scrollWidth − clientWidth = 208`, tablet/desktop = 0). Root cause: the decorative glow `div`s in `page.tsx` (`w-[500px]` at `left-1/4`, `w-[400px]` at `right-1/4`) — 390·0.25 + 500 ≈ 598px document width. Nothing constrains overflow (`overflow-x-hidden` absent on `main`/`body`). Compounding it, the exposed strip renders **white**: `globals.css` sets body background from the light-scheme token (`--background:#ffffff`) while the app hard-codes `bg-slate-950`, so in light-OS-scheme browsers the overflow area is a glaring white band down the whole page. |
| D2 | breaks-usage (content loss) | all | `mobile_default`, `desktop_default`, `mobile_null_fields`, `mobile_status_change` | **Status badge clipped off the card at every viewport** — renders "PENDIN…", "INTERE…". The badge row (`flex gap-2`, no wrap) overflows the card because the badges render far larger than designed (see D3); the status pill (justify-end side) gets pushed past the card edge and is cut by `overflow-hidden`. Status is a primary signal on this board — it is partially unreadable everywhere. |
| D3 | degrades (root cause of D2) | all | `mobile_null_fields` (close-up), any default | **`text-3xs` and `text-2xs` are undefined utilities.** `globals.css` defines no custom font sizes (bare `@import "tailwindcss"` + two color tokens), and Tailwind v4 ships no `2xs/3xs`. Measured computed size: **16px** for both (vs `text-xs` = 12px). Every element using them — card badges (source/BHK/fit/status), card metric labels (RENT/COMMUTE/DEPOSIT/AREA SIZE), slider legends — renders at body-text size: "3 BHK" and "FIT 50" pills wrap to two lines, badge row overflows (D2), metric labels shout. |
| D4 | degrades (a11y/interaction) | all | none (interaction finding) | **Collapsed advanced-filter panel keeps its controls interactive.** When closed it is `opacity-0 max-h-0 overflow-hidden` but not `hidden`/`inert` — its buttons remain in the DOM, **focusable and clickable** (measured a click landing on the invisible "Interested" status pill, 93×34, silently toggling the filter; discovered when the sweep's own click hit it). Keyboard users can Tab into invisible controls and change filter state with no visual feedback. |
| D5 | degrades (a11y, mobile) | mobile (present at all) | measurements below | **19 interactive elements under the 44px touch-target minimum** on mobile, including every primary action: card status buttons 97×38, filter status pills 81–94×34, header buttons ("Clear Session Auth" 143×34, "Refresh Feed" 138×36), Show-Rejected toggle 44×24, location map-links 157–218×**16**, range sliders 308×**6**. |
| D6 | degrades (a11y, contrast) | all | measured on live DOM | **WCAG AA failures.** Slider legends (`text-slate-600` on slate-950): **2.55:1** — fails every level. All `slate-500` small labels — stat-tile labels ("TOTAL TRACKED" 3.98:1), card metric labels ("RENT" 4.15:1), SORT label (4.07:1), location links (4.07:1) — sit below the 4.5:1 normal-text minimum. Fit badge (8.88) and header sub-copy (7.66) pass. |
| D7 | degrades | all | `mobile_loading`, `mobile_api_down` | **Stat tiles flash false zeros.** During fetch, tiles render "0 Properties / 0 Listings / N/A / N/A" (only the card area has a loading treatment; `MetricsBar` has no loading awareness). The same misleading "0" shows during an API outage — "0 properties" ≠ "unknown". |
| D8 | degrades (copy) | all | `mobile_api_down`, `mobile_password_modal` | **Developer copy leaks into the UI.** Error state: "Could not connect to FastAPI server. Ensure python backend api.py is running." (shown to any production visitor on API hiccup). Modal: "…complete this state mutation." Loading: "Retrieving normalized listings…". Clear-auth uses a browser `alert()` ("Authorization token cleared…"). |
| D9 | cosmetic | all | measured | **Dead animation classes.** `animate-fade-in` (every card, with a per-card `animationDelay` style) and `animate-shake` (modal error) are undefined — computed `animation-name: none`. Cards pop in with no transition; the stagger logic is dead code. |
| D10 | cosmetic | all | `desktop_default` | Collapsed filter panel retains ~24px phantom height inside the filter card, which reads as a half-empty container below the search row. |
| D11 | degrades (Safari, code-level) | n/a | code: `page.tsx` `created_desc` sort | **"Newly Listed" sort breaks on Safari in local mode.** `new Date("2026-07-08 18:52:57")` (SQLite format, non-ISO) → `Invalid Date` in Safari/WebKit → `NaN` comparator → arbitrary order. Cloud mode sends ISO strings and is fine. Found by code inspection during the sweep; not screenshot-able in Chromium. |
| D12 | cosmetic (locale) | all | `mobile_default` | Currency uses default `toLocaleString()` (en-US grouping): "₹3,000,000" instead of Indian-system "₹30,00,000" (`en-IN`). Same for rent/deposit/average-rent tiles. |
| D13 | cosmetic | mobile | `mobile_default` | Search placeholder truncates mid-word ("…or configuratic"); the "Filters" button also sits flush against/clipped by the right padding edge on 390px (see `mobile_default`). |

**Not defects (verified working):** null deposit/sqft render "N/A" without
crashing (`mobile_null_fields`); long titles clamp at 2 lines with ellipsis and
long locations truncate (`*_long_title`, default shots); all five sort options
reorder correctly; status-change flow (modal → authorize → badge/button update)
works (`mobile_status_change`); empty and API-down states render dedicated
panels; `include_rejected` fetches and shows rejected rows.

---

## 2. Design-debt inventory (distinct from bugs)

1. **Filter ranges ignore the real data envelope.** Rent slider 0–₹100,000
   (step 5k) against a hard ₹45k data cap — more than half the range is dead.
   Commute slider 10–120 min against a 60-min server cap — same. Initial
   `maxPrice` state is 60,000 but "Reset Active Filters" sets 100,000 —
   two different "defaults".
2. **Naming drift.**
   - UI "Pending" vs DB `'New'` (renamed on the client, `page.tsx` normalize).
   - "Safest Commute" tile actually shows the *shortest* commute.
   - "Total Tracked" counts only rows the API served (post commute/staleness/
     rejected filters) — not what "tracked" implies (81 rows in the store, tile
     says 3).
   - Tile stats mix bases: min-commute is computed over *all* fetched
     properties, average rent over the *filtered* subset.
3. **`include_rejected` has no volume management** — toggling it renders a
   ~46-card single column (56,000px tall on mobile), no pagination, count
   summary, or grouping; rejected cards look identical to active ones apart
   from the (clipped) badge.
4. **Card information hierarchy.** Badge row → title → location → 2×2 metric
   grid → 3 equal-weight action buttons. Rent (the #1 ranking factor) has the
   same visual weight as deposit; the fit score (the product's headline
   feature) is a tiny clipped pill; three full-width buttons dominate the card
   bottom on every card.
5. **Copy tone is mixed dev/marketing:** "Curated rental shortlist optimized
   against your personal daily office commute time", "Security Gate",
   "state mutation", "Retrieving normalized listings", `alert()` confirmations.
   Empty-state copy ("Try adjusting your price filters…") also shows when the
   server genuinely has zero rows — misdirects the user.
6. **Theming is half-committed.** The app is designed dark-only
   (`bg-slate-950` hard-coded) but `globals.css` carries light-scheme tokens
   that actually paint (the D1 white strip); body font-family falls back to
   Arial outside `main` while Geist is loaded in `layout.tsx`.
7. **Dead/vestigial props & code:** `PropertyCard.index` exists only for the
   dead `animationDelay` (D9); `showRejected` and `selectedStatus` overlap in
   meaning (toggle just injects "Rejected" into the pill set).

---

## 3. Component inventory (redesign maps onto this)

| Component | File | Responsibilities | Props / state |
|---|---|---|---|
| **Home (page shell)** | `frontend/src/app/page.tsx` | Owns all state: `properties`, `loading`, `errorMessage`, `searchQuery`, `minPrice`/`maxPrice`, `maxCommute`, `selectedStatus[]`, `showRejected`, `sortBy`, `isAuthModalOpen`, `pendingMutation`. Fetches `/api/listings` (adds `?include_rejected=true` when toggled; refetch on toggle), normalizes `'New'`→"Pending", client-side filter (search/price/commute/status) + sort (fit/commute/price/newest), status mutation via `X-Master-Password` header with sessionStorage password cache, renders header (title, Clear Session Auth, Refresh Feed), decorative glows (D1), and composes everything below. | — (top-level) |
| **MetricsBar** | `components/MetricsBar.tsx` | 4 stat tiles: Total Tracked (`properties.length`), Active Listings (non-Rejected count), Safest Commute (min commute over non-rejected), Average Rent (mean over *filtered*). No loading/error awareness (D7). | `properties`, `filteredProperties` |
| **FilterBar** | `components/FilterBar.tsx` | Search input; sort `<select>` (5 options, `fit_desc` default); collapsible advanced panel: rent slider (0–100k), commute slider (10–120), status pills (Pending/Interested/Contacted), Show-Rejected toggle (injects "Rejected" pill + triggers refetch), Reset. Collapsed panel stays interactive in DOM (D4). | 13 props: `searchQuery`, `minPrice`, `maxPrice`, `maxCommute`, `selectedStatus`, `showRejected`, `sortBy` + setters |
| **PropertyCard** | `components/PropertyCard.tsx` | Badge row (source, BHK, `Fit NN`, status — clipping, D2/D3); 2-line-clamped title linking to the listing URL; location linking to Google Maps (text-search fallback when lat/long null — works); 2×2 metric grid (Rent, Commute w/ ≤30 green / ≤45 amber / else rose, Deposit "N/A"-safe, Area "N/A"-safe); footer: per-status action buttons with per-button spinner, current status hidden from options. | `property`, `onStatusChange`, `index` (dead, D9) |
| **PasswordModal** | `components/PasswordModal.tsx` | Backdrop-dismiss modal; POSTs `/api/auth/verify`; inline error (dead `animate-shake`, D9); loading spinner on submit; `autoFocus` input. No focus trap, no Escape handling, no close X. | `isOpen`, `onClose`, `onSuccess(password)`, `apiBaseUrl` |
| **Types** | `types/property.ts` | `Property` interface mirrors `PropertyResponse` incl. `fit_score`; `deposit?`/`area_sqft?` optional. | — |
| **Global styles** | `app/globals.css`, `app/layout.tsx` | Bare Tailwind v4 import; light/dark body tokens (conflict, D1); Geist fonts loaded but body falls back Arial; **no custom utilities defined** — everything referencing `text-3xs`, `text-2xs`, `animate-fade-in`, `animate-shake` is unstyled (D3, D9). | — |

---

## 4. Console & runtime health

Captured across all 42 state/viewport combinations (dev mode):

- **Zero page errors. Zero React/hydration warnings. Zero key warnings.**
- Only messages: React DevTools install hint (info), `[HMR] connected`,
  Fast-Refresh rebuild logs, and `net::ERR_FAILED` + "Listing fetch failed:
  TypeError: Failed to fetch" — the latter only in the deliberate `api_down`
  mock (they are the correct failure path, surfaced in the error panel).

## 5. Measurement appendix

- Horizontal overflow (`scrollWidth − clientWidth`): **mobile 208px**, tablet 0, desktop 0.
- Computed font sizes: `.text-3xs` → **16px**, `.text-2xs` → **16px**, `.text-xs` → 12px.
- `animate-fade-in` computed `animation-name`: **none**.
- Collapsed filter panel: `max-height: 0px` but rect height ~24px (phantom spacing).
- Contrast (canvas-normalized oklch → sRGB, composited over slate-950):
  slider legend 2.55 · stat label 3.98 · SORT label 4.07 · location link 4.07 ·
  card metric label 4.15 · header sub 7.66 · fit badge 8.88.
- Sub-44px tap targets (mobile, deduped): header buttons (143×34, 138×36),
  sliders (308×6 ×2), filter pills (81–94×34 ×3), Show-Rejected toggle (44×24),
  map links (×3, height 16), card action buttons (97–150×38 ×8).

## 6. Reproduction

1. `venv/Scripts/python.exe -m uvicorn api:app --port 8000` with
   `ENVIRONMENT=production` (or local mode for SQLite data).
2. `cd frontend && npm run dev`.
3. `venv/Scripts/python.exe artifacts/ui-audit/ui_sweep.py` — regenerates all
   42 screenshots and the measurements (console/tap-target/contrast raw data).
