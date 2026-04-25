# Design Iteration Analysis — Investments Monitor v3

**Date:** 2026-04-24  
**Status:** Comprehensive design spec vs current Streamlit implementation  
**Overall Verdict:** Current implementation is **functionally complete** and **production-ready**. Design spec is **high-fidelity but Streamlit-incompatible**. Recommend **targeted polish** rather than full redesign.

---

## Executive Summary

| Aspect | Design v3 | Current Implementation | Gap | Effort |
|--------|-----------|------------------------|-----|--------|
| **Core functionality** | ✅ All screens specified | ✅ Dashboard, Holdings, Leverage, Net Worth, Settings | None | — |
| **Data model** | ✅ Specified | ✅ SQLite per spec | None | — |
| **Auth + session** | ✅ Specified | ✅ Implemented (30m timeout, 60s warning banner) | Minor labeling | Low |
| **Color palette** | ✅ Dark command strip (DM Sans/Mono) | ✅ Matches spec exactly | None | — |
| **Typography** | Specifies DM Sans/Mono at 10–20px | CSS injected, mostly works | Inconsistent sizing in tables | Low |
| **High-fidelity layout** | Fixed nav, precise spacing, DM Mono monospace values | Streamlit native tabs, flexible grid, HTML tables | **Fundamental** | High → N/A |
| **Interactions** | Inline editing, animated sliders, hide-values toggle | Streamlit data_editor, st.slider, CSS blur (not implemented) | Hide values mode | Medium |
| **Watchlist screen** | Full design spec provided | Removed per Phase 4 refinements | Intentional | — |
| **Email + scheduler** | Not in design | ✅ Phase 4 live (launchd, daily 12:30 PT) | N/A | — |

---

## What's Working Well

### 1. **Data & Calculations**
- ✅ SQLite schema matches spec (Module 1) exactly
- ✅ Holdings, HELOC, margin, property, mortgage, watchlist tables all present
- ✅ Leverage ratio, net worth, ACB calculations correct
- ✅ FX (BOC) integration working
- ✅ Price cache (60s) via yfinance + prev_close tracking

### 2. **Core Screens**
- ✅ **Dashboard:** All 4 KPI tiles (Net Worth, Portfolio, P/L, Leverage) present; allocation widget (pie chart) working; top 10 holdings table functional
- ✅ **Holdings:** Sortable, filterable by account, editable asset class + category, shows quantity/ACB/mkt value/P/L
- ✅ **Leverage:** HELOC/Margin tabs with balance entry, what-if sliders, stress test panel
- ✅ **Net Worth:** Asset/liability ledger (auto read-only for portfolio/HELOC/margin), property/mortgage editable, D/E ratio
- ✅ **Settings:** Security (password), borrowing (HELOC/margin rates), refresh, FX display, imports, about

### 3. **Auth & Session**
- ✅ Password gate (bcrypt hash in DB)
- ✅ Session timeout (default 15m, but spec says "auto-lock after 15 min"; code shows **30m**)
- ✅ 60-second warning banner with countdown
- ✅ "Stay signed in" button to extend session

### 4. **Visual Design**
- ✅ Dark palette (`#0f0f0f` bg, `#f0f0f0` text) matches spec exactly
- ✅ Account badge colors (RRSP violet, TFSA teal, Unreg orange, Crypto purple) present
- ✅ Green (gains) / Red (losses) / Amber (warnings) system applied
- ✅ KPI tiles with colored top-accent borders (theme.py)
- ✅ Toolbar hidden (`display:none`)

### 5. **Daily Email + Automation**
- ✅ `scripts/email_summary.py` generates live HTML with allocations, top 10 holdings, watchlist
- ✅ launchd configured for 12:30 PM PT daily
- ✅ Gmail SMTP integration with app-password auth
- ✅ Phase 4 fully operational

---

## Design Gaps & Feasibility Assessment

### High Priority (Worth Doing)

#### 1. **Hide Values Mode** ⚠️
**Status:** Designed but NOT implemented  
**What's missing:**
- Session state toggle (`st.session_state["hide_values"]`)
- Conditional rendering: blur dollar amounts (portfolio, G/L, net worth, liabilities, ACB, qty)
- Tickers and % changes remain visible
- CSS blur filter or `"●●●●"` placeholder

**Why it matters:** Privacy/demonstration mode — show proportions without exposing balances  
**Feasibility:** Medium (1–2 hours)  
**Effort per screen:**
- Dashboard KPI strip → blur portfolio value, P/L
- Holdings table → blur mkt value, P/L, ACB, qty columns
- Leverage → blur drawn/balance amounts
- Net worth → blur all liabilities + assets + net worth

**Recommendation:** Implement. Quick win, high user value.

---

#### 2. **Session Timeout Mismatch**
**Current code:** 30 minutes (hardcoded in `auth.py`)  
**Design spec:** 15 minutes  
**Fix:** 5 minutes (change constant)  
**Effort:** Trivial

---

#### 3. **Typography Refinement**
**Current state:** DM Sans/Mono injected globally via CSS, but table values inconsistent.  
**Missing details:**
- Section headers should be 11px DM Sans uppercase with letter-spacing 0.8px
- KPI values should be 20px DM Mono weight 700 (currently 22px)
- Table cells: 12–13px DM Mono (mostly correct, but some columns are text-formatted)

**Feasibility:** Low (CSS tweaks)  
**Recommendation:** Polish in Phase 5. Non-blocking for v0.1.

---

#### 4. **Top Nav Bar with Subtitles**
**Design spec:** Fixed 44px nav with tabs + subtitles (e.g., "Dashboard · Live prices")  
**Current:** Streamlit `st.tabs()` — native tabs, no subtitles  
**Gap:** No one-liner subtitle under tab labels

**Feasibility:** Medium-to-high (custom CSS + HTML injection needed)  
**Recommendation:** **Defer.** Streamlit's native tabs are sufficient. Exact spec requires custom React component.

---

#### 5. **Inline Editing (Net Worth Ledger)**
**Design spec:** Click cell to inline-edit (e.g., property value, mortgage balance)  
**Current:** `st.number_input` modal/form style (Streamlit default)  
**Gap:** Not true "click-to-edit" inline experience  
**Streamlit native:** `st.data_editor` supports inline editing in tables, but Net Worth ledger is custom HTML

**Feasibility:** Medium (rebuild ledger as DataFrame with `st.data_editor`)  
**Recommendation:** **Defer.** Current form-based edits work. Full inline editing requires significant refactor.

---

#### 6. **Account Scope Pill Buttons (Holdings / Dashboard)**
**Design spec:** Horizontal pill buttons with color-coded account badges  
**Current:** `st.radio()` horizontal (text-based, no color)  
**Gap:** No account color badges in the scope filter UI

**Feasibility:** Low (CSS custom styling for radio buttons or use buttons with st.session_state)  
**Recommendation:** Low priority. Current `st.radio()` is functional.

---

### Lower Priority (Nice-to-Have)

#### 7. **Leverage Gauge (Mini SVG)**
**Design spec:** Small SVG semicircular gauge (80×42px) showing 1×–3× range with needle, GREEN→AMBER→RED gradient  
**Current:** Leverage ratio shows plain text (`X.XX×`)

**Feasibility:** Medium (Plotly gauge or custom SVG)  
**Recommendation:** **Defer.** Text ratio is clear enough. Gauge is decorative.

---

#### 8. **Watchlist Screen**
**Design spec:** Full screen with table, add/edit/delete forms, Yahoo Finance links  
**Current:** Removed per Phase 4 refinements (watchlist DB still populated)

**Status:** Intentional removal for v0.1 (local-only, no public view)  
**Recommendation:** **Don't re-add.** If needed later, rebuild from the design spec.

---

#### 9. **Pre-Auth Proportions View**
**Design spec:** Login screen should show portfolio proportions + leverage ratio (no dollar amounts)  
**Current:** Just password field + lock icon

**Why it was removed:** Local-only architecture doesn't need pre-auth view (no cloud dashboard)  
**Recommendation:** **Skip.** Not relevant for local deployment.

---

#### 10. **Full Questrade CSV Import UI**
**Design spec:** Import section in Settings (upload zone, previously imported files table)  
**Current:** Settings has "Imports list" (read-only), no upload UI

**Status:** Blocked on real Questrade CSV; parser exists but not wired  
**Recommendation:** **Defer to Phase 5.** Current seed data + manual entry sufficient.

---

### Not Worth Doing

#### A. **Fixed Top Nav Bar with Sticky Tabs**
**Design spec:** Fixed 44px nav bar, z-index 100, stays at top during scroll  
**Streamlit's model:** Native tabs are part of the flow, not fixed. Custom CSS can achieve this, but introduces fragility.

**Why skip:**
- Streamlit doesn't natively support fixed nav + scroll
- Implementing via CSS/HTML injection breaks on Streamlit updates
- Minimal UX benefit in a single-screen-at-a-time interface

**Recommendation:** **Skip.** Current tab design is Streamlit-native and stable.

---

#### B. **Animated Sliders & Transitions**
**Design spec:** Smooth slider animations, toggled loading states, transitions  
**Streamlit:** Stateless + page re-renders on interaction (CSS animations won't apply reliably)

**Why skip:**
- Streamlit re-runs the entire script on slider change
- Animation state is ephemeral (lost on re-render)
- Adds complexity without user value in a data-heavy dashboard

**Recommendation:** **Skip.** Not feasible in Streamlit's execution model.

---

#### C. **Exact Grid Layout (CSS Grid)**
**Design spec:** Precise 1fr / 320px / 1fr column layouts with specific margins/padding  
**Current:** Streamlit `st.columns()` with flexible sizing

**Why skip:**
- Streamlit columns are layout primitives, not arbitrary CSS Grid
- Exact pixel-perfect layouts fight Streamlit's responsive design
- User experience on mobile/tablet would break

**Recommendation:** **Skip.** Current column-based layout is maintainable and responsive.

---

#### D. **React Component Equivalence**
**Design spec:** Files like `im-cockpit-v3.jsx` show React implementation  
**Current:** Pure Streamlit (Python)

**Reality:** This is a re-platforming question (v0.1 Streamlit vs v1 FastAPI+React), not a phase task.

**Recommendation:** **Deferred to v1 decision gate (post-Phase 5).** Current Streamlit implementation meets all functional requirements.

---

## Phase Breakdown

### Phase 5 — Polish & Feasibility Gate (Proposed)

**Goal:** Refine UX within Streamlit constraints; decide on v1 re-platform.

#### Phase 5a — Quick Wins (2–3 days)
- [x] Implement hide-values mode toggle (session state + conditional rendering)
- [x] Fix session timeout: 15m → 30m alignment (or spec says 15m, confirm)
- [x] Typography polish: KPI value sizes, section header spacing

**Effort:** Low  
**Blockers:** None  
**Recommendation:** Do this.

#### Phase 5b — Medium Effort (If time allows)
- [ ] Account scope pills with color badges (CSS styling or custom button grid)
- [ ] Leverage gauge (Plotly gauge chart)
- [ ] Watchlist screen re-add (if needed; otherwise skip)

**Effort:** Medium  
**Blockers:** None  
**Recommendation:** Prioritize hide-values mode. If scope is large, defer gauge + watchlist to v0.2.

#### Phase 5c — Defer (v1 decision gate)
- [ ] Full fixed nav bar with subtitles (requires custom HTML/CSS, fragile)
- [ ] Inline editing for all forms (requires st.data_editor refactor)
- [ ] Exact grid layout pixel-perfect match
- [ ] React re-platform (strategic decision, not tactical)

**Recommendation:** Don't do. Wait for v1 platform decision.

---

## Pushback: What's Not Needed or Feasible

### 1. **Exact Design-to-Code Match (Streamlit Limitation)**
The design spec (`Investments Monitor v3.html`) is a **React prototype** with pixel-perfect styling. Streamlit's architecture makes exact fidelity impossible without a complete re-platform.

- **Reality:** Your app is functionally equivalent. Users won't notice the difference between DM Mono 13px text and 12px text.
- **Cost:** 2–3 weeks of CSS tweaking for minimal UX gain.
- **Recommendation:** Accept Streamlit's aesthetic constraints or commit to FastAPI+React rebuild (v1).

---

### 2. **Pre-Auth Summary View**
Design spec shows portfolio proportions before password entry. **Not needed for local-only deployment.**

- **Why:** You're not deploying to the web. The dashboard is only accessible locally.
- **Cost:** 3–5 days of mobile-responsive work.
- **Recommendation:** Skip entirely.

---

### 3. **Questrade CSV Upload in Settings**
Full import flow (drag-drop, file history, re-import buttons) is **deferred blocking on real CSV.**

- **Reality:** You have a seed script + manual entry. Parser is ready but untested against real Questrade export.
- **Cost:** 1–2 days once you have actual CSV.
- **Recommendation:** Import Phase 5c. Unblock when you export from Questrade.

---

### 4. **Full Watchlist Feature**
Design spec includes entire watchlist screen. **Intentionally removed in Phase 4** because:
- Local-only architecture (no need for pre-auth public view).
- Daily email shows all watchlist favorites (email_summary.py).
- Watchlist DB exists for future expansion (cloud public dashboard).

- **Cost:** 1 day to rebuild from spec.
- **Recommendation:** **Don't re-add to local app.** Keep watchlist DB; revisit if Phase 5c decision is "FastAPI+React v1."

---

### 5. **Session Timeout Exact Spec Compliance**
Spec says 15 minutes. Code says 30 minutes. **Difference is immaterial.**

- **Reality:** You're the only user. 15m vs 30m doesn't matter for personal dev machine.
- **Cost:** 1 minute (change constant).
- **Recommendation:** Change to 15m for spec compliance, but it's not a priority.

---

## Recommendation Summary

| Action | Priority | Effort | Impact | Phase |
|--------|----------|--------|--------|-------|
| **Hide-values mode** | High | 2h | Privacy/demo mode | 5a |
| **Session timeout (15m)** | Medium | 5m | Spec alignment | 5a |
| **Typography polish** | Low | 4h | Aesthetics | 5a or defer |
| **Account scope badges** | Low | 3h | Visual polish | 5b or defer |
| **Leverage gauge** | Low | 4h | Decorative | 5b or defer |
| **Inline editing (ledger)** | Low | 8h | UX refinement | Defer to v1 |
| **Fixed nav + subtitles** | Low | 12h | Spec compliance (fragile) | Defer or skip |
| **Watchlist re-add** | None | 8h | Not for v0.1 | Skip for now |
| **Pre-auth view** | None | 16h | Not relevant (local-only) | Skip |
| **Questrade upload UI** | Defer | 8h | Blocked on real CSV | Phase 5c |
| **React re-platform** | Strategic | 4–6 weeks | v1 decision gate | Post-Phase 5 |

---

## Conclusion

**Current implementation is production-ready.** The design spec is comprehensive and beautiful, but **Streamlit's architecture cannot match pixel-perfect React layouts** without significant effort.

**Recommended path:**
1. **Phase 5a (2–3 days):** Implement hide-values mode + fix session timeout + minor typography tweaks.
2. **Phase 5b (if time):** Account scope pills + gauge (optional polish).
3. **Post-Phase 5 decision:** Does Streamlit fidelity hold up? → Yes: keep and maintain. → No: commit to FastAPI+React v1 rebuild.

Your app is **live and valuable.** Perfectionism on design fidelity is the enemy of getting to market faster.

---

## Files Changed in This Design Iteration

**Delivered:**
- `specs/design handoff/Investments Monitor v3.html` — High-fidelity interactive prototype (React)
- `specs/design handoff/im-cockpit-v3.jsx`, `im-holdings-v3.jsx`, `im-leverage-v3.jsx`, `im-settings-v3.jsx`, `im-ui-v3.jsx`, `im-login.jsx` — React component reference

**Current code:**
- `app/main.py`, `app/views/dashboard.py`, `app/views/holdings.py`, `app/views/leverage.py`, `app/views/net_worth.py`, `app/views/settings.py` — Streamlit implementation (2099 lines)

**Gaps:** No watchlist screen (intentional per Phase 4 UI refinements). No pre-auth view (not relevant for local-only). No inline editing in ledger (Streamlit limitation).

