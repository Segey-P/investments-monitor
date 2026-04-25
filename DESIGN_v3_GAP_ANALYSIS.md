# Design v3 → Implementation Gap Analysis

**Scope:** 10 design changes in v3 vs current Streamlit implementation  
**Date:** 2026-04-24  
**Status:** COMPREHENSIVE — detailed per-change assessment, phases, effort, feasibility, and pushback

---

## The 10 Changes at a Glance

| # | Screen | Change | Current Status | Priority | Effort | Phase |
|---|--------|--------|-----------------|----------|--------|-------|
| 1 | Dashboard | KPI strip reworked (Today's Δ, Biggest mover) | ❌ Not implemented | **High** | 2h | 5a |
| 2 | All screens | Nav screen subtitles | ❌ Not in Streamlit | Medium | 4h | 5b |
| 3 | Net Worth | Inline editing for Cash | ❌ Form-based only | **High** | 3h | 5a |
| 4 | Net Worth | Combined slider + number input | ❌ Slider only | **High** | 4h | 5a |
| 5 | Net Worth | Screen-level privacy legend | ✅ Partial (privacy mode) | Low | 2h | 5a |
| 6 | Settings | Single Save per section | ❌ Not implemented | Medium | 6h | 5b |
| 7 | Leverage | Portfolio drawdown stress test | ❌ Not implemented | **High** | 3h | 5a |
| 8 | Watchlist | Taller, clearer sparkbar | ❌ Watchlist removed | — | — | — |
| 9 | Holdings | Column visibility toggle | ❌ Not implemented | Medium | 5h | 5b |
| 10 | Watchlist | Gap % color-coded | ❌ Watchlist removed | — | — | — |

---

## Detailed Change Breakdown

### CHANGE 1: Dashboard KPI Strip Reworked
**Current state:** 5 cards — Portfolio value, Unrealized P/L, Leverage Ratio, HELOC Drawn, + 1 unused slot  
**Design v3:** 4 cards — Portfolio value, **Today's Δ** (new), **Biggest mover** (new), Leverage Ratio  
**Why:** Better at-a-glance insight into daily moves and what's moving most

**Implementation gap:**
- Missing "Today's Δ" card: Sum of all holdings' (qty × price × daily % change) in dollars
- Missing "Biggest mover" card: Ticker with largest abs % change today
- No "Unrealized P/L" card (currently present but not in v3 design)

**Feasibility:** Easy (math already in calcs.py, just need to compute + display)  
**Effort:** 2 hours (compute + layout)  
**Recommendation:** **Do immediately.** High-value visual improvement.  
**Phase:** 5a

**Implementation sketch:**
```python
# In calcs.py or dashboard.py
def today_delta(holdings, usdcad):
    """Sum of all positions' daily dollar change."""
    return sum(
        h.mkt_value_cad(usdcad) * h.price_change_pct / 100
        for h in holdings
        if h.mkt_value_cad(usdcad) is not None
    )

def biggest_mover(holdings):
    """Ticker with largest abs % change today."""
    if not holdings:
        return None
    return max(holdings, key=lambda h: abs(h.price_change_pct))
```

Then add 2 KPI tiles:
- "Today's Δ" → `today_delta()` value + pct of portfolio
- "Biggest mover" → `biggest_mover().ticker` + abs % change

---

### CHANGE 2: Nav Screen Subtitles
**Current state:** Streamlit tabs (generic, no subtitles)  
**Design v3:** Each active tab shows a one-liner description:
- Dashboard: "Live prices, leverage at a glance"
- Holdings: "All positions, sortable, filterable"
- Leverage: "HELOC & margin tracking"
- Net Worth: "Assets, liabilities, equity"
- Settings: "Security, borrowing, refresh, imports"

**Feasibility:** Low-to-medium (Streamlit's native tabs don't support subtitles)  
**Options:**
1. **Custom CSS + HTML injection** — Hide Streamlit tabs, build custom nav bar with subtitles
2. **Streamlit sidebar nav** — Horizontal buttons in sidebar instead of top tabs
3. **Keep as-is** — Streamlit tabs are sufficient for local app

**Effort:** 6–8 hours (CSS injection + fragile on upgrades)  
**Recommendation:** **Defer or skip.** Not essential for v0.1. Streamlit's native tabs are clear enough. If you want this, wait for v1 (React) where nav is trivial.  
**Phase:** 5b or skip

---

### CHANGE 3: Inline Editing for Cash (Net Worth)
**Current state:** Net Worth screen is read-only; cash would be entered via Settings form  
**Design v3:** Click cash value to inline-edit (click → text input → Enter to commit)

**Implementation gap:**
- Need click-to-edit pattern on the Net Worth screen
- Streamlit doesn't natively support true inline editing in tables (only in `st.data_editor`)

**Options:**
1. **Use `st.data_editor`** — Rebuild Net Worth ledger as DataFrame with editable column
2. **Toggle edit mode** — Button to switch Net Worth to edit mode, then `st.number_input` fields
3. **Modal form** — Click value → opens popup form (current pattern in Settings)

**Feasibility:** Medium (requires refactoring Net Worth from custom HTML to DataFrame)  
**Effort:** 3–4 hours  
**Recommendation:** **Implement via st.data_editor.** Makes the ledger visually consistent with Holdings (which already uses data_editor).

**Phase:** 5a

**Implementation sketch:**
```python
# In net_worth.py
df_ledger = pd.DataFrame([
    {"Item": "Portfolio (auto)", "Value": portfolio_total, "Editable": False},
    {"Item": "Cash / HISA", "Value": cash, "Editable": True},
    {"Item": "Primary residence", "Value": property_value, "Editable": True},
    # ... etc
])

edited_df = st.data_editor(
    df_ledger,
    column_config={
        "Item": st.column_config.TextColumn(disabled=True),
        "Value": st.column_config.NumberColumn(),
    },
    key="nw_ledger",
)
```

---

### CHANGE 4: Combined Slider + Number Input
**Current state:** Net Worth property/mortgage use only sliders  
**Design v3:** For property value and mortgage balance: slider + number input side-by-side  
- Drag slider OR type in number field
- No ceiling limit (can type any value above slider range)
- Sub-label: "type or drag · no ceiling limit"

**Implementation gap:**
- Streamlit sliders have a fixed max value
- No native way to combine slider + number input
- Can't exceed slider max without custom JavaScript

**Options:**
1. **Use st.number_input + st.slider** — Side-by-side in columns, both update same state variable
2. **Custom HTML** — HTML5 range input + number input (CSS injection)
3. **Keep slider-only** — Current approach (slider + separate number input in Settings)

**Feasibility:** Medium (Streamlit can do this, but layout + logic requires careful state management)  
**Effort:** 4 hours (careful state sync between slider and input)  
**Recommendation:** **Implement with st.columns + st.slider + st.number_input.** Don't try ceiling-limit removal (would require major refactor for minimal UX gain).

**Phase:** 5a

**Implementation sketch:**
```python
# In net_worth.py
col1, col2 = st.columns(2)
with col1:
    prop_val = st.slider("Property value", 0, 2_000_000, value=current_val, step=5000)
with col2:
    prop_val = st.number_input("Type value", value=prop_val, step=5000)
# (Note: Streamlit's slider max must be predefined; can't truly exceed it without custom code)
```

Realistic compromise: Slider range up to $3M, number input allows any value. Don't try to make slider dynamically extend.

---

### CHANGE 5: Screen-Level Privacy Legend
**Current state:** No privacy indicator in Net Worth (though privacy mode exists globally)  
**Design v3:** Single legend in panel header showing privacy status:
- 🔒 Local / ☁ Cloud indicator
- Example: "🔒 Values hidden" badge in Net Worth panel header

**Implementation gap:**
- Privacy toggle exists in theme/auth, but not surfaced in Net Worth panel

**Feasibility:** Easy (add conditional badge to panel header)  
**Effort:** 1–2 hours  
**Recommendation:** **Implement.** Low-effort, improves UX clarity.

**Phase:** 5a

**Implementation sketch:**
```python
# In net_worth.py, in the panel header:
if "hide_values" in st.session_state and st.session_state.hide_values:
    st.markdown(
        '<span style="color:#f59e0b; font-size:11px;">🙈 Values hidden</span>',
        unsafe_allow_html=True
    )
```

---

### CHANGE 6: Single Save Per Section (Settings)
**Current state:** Settings has inline save buttons (or none yet, depending on implementation)  
**Design v3:** Each section (Security, Borrowing, Refresh, FX, Imports, About) has **one "Save changes" button** at the bottom of that section  
- Button shows "Save changes" initially
- On click, turns green with "✓ Saved · Settings updated" for 2.2 seconds
- Sections include: Security (password, timeout), Borrowing (HELOC/margin rates), Refresh (toggle + interval), FX (read-only display), Imports (CSV upload), About (read-only)

**Current implementation:** Check what's in `app/views/settings.py`

**Implementation gap:**
- Unknown without reading full Settings code
- Likely has multiple buttons or no save functionality yet

**Feasibility:** Medium (requires UI redesign of Settings layout)  
**Effort:** 6 hours (layout refactor + form handling per section)  
**Recommendation:** **Implement in Phase 5b.** Medium priority — Settings is important but not user-facing daily.

**Phase:** 5b

**Key sections to implement:**
1. **Security** — password change, session timeout (minutes)
2. **Borrowing** — HELOC limit, rate, utilization warning; Margin limit, rate, call threshold
3. **Refresh** — Toggle scheduled refresh, interval minutes
4. **FX** — Display BOC rate + fetch timestamp (read-only)
5. **Imports** — Upload zone (drag-drop CSV), previously imported files table
6. **About** — Version, branch, last commit, stack, storage, remote access (read-only)

---

### CHANGE 7: Portfolio Drawdown Stress Test (Leverage What-If)
**Current state:** Leverage what-if slider for HELOC draw only  
**Design v3:** **Two sliders in what-if panel:**
1. "Draw HELOC" (0 → available credit, step $500, BLUE accent)
2. **"If markets fall…"** (0–50%, step 1%, RED accent) ← **NEW**
   - Sub-label: "Debt stays fixed; portfolio value shrinks → ratio rises"
   - Shows stressed portfolio value in result

**Result display:**
- Label: "Stressed ratio" or "Current ratio"
- Value: `X.XX×` in large DM Mono, color-coded
- Delta vs base: `▲/▼ X.XX× vs current X.XX×`
- Sub-rows: `HELOC balance · Total borrowed · Stressed port. val · Interest delta/mo`
- Warning: `⚠ Ratio exceeds 2.0×` if ratio ≥ 2.0
- Reset button when any slider > 0
- Disclaimer: "Not financial advice"

**Implementation gap:**
- Current leverage screen doesn't have market drawdown slider
- Need to compute: `portfolio_value * (1 - drawdown%)` and recalculate leverage ratio

**Feasibility:** Easy (straightforward math)  
**Effort:** 3 hours  
**Recommendation:** **Implement immediately.** High-value insight for leverage monitoring.

**Phase:** 5a

**Implementation sketch:**
```python
# In leverage.py
drawdown_pct = st.slider("If markets fall", 0, 50, value=0, step=1)
stressed_port_val = portfolio_cad * (1 - drawdown_pct / 100)
stressed_lev = calcs.leverage(conn, stressed_port_val, unreg_value)

st.metric(
    "Stressed ratio" if drawdown_pct > 0 else "Current ratio",
    f"{stressed_lev.leverage_ratio:.2f}×",
    delta=f"{stressed_lev.leverage_ratio - base_lev:.2f}×" if drawdown_pct > 0 else None,
)
```

---

### CHANGE 8: Taller Sparkbar in Watchlist
**Current state:** Watchlist screen removed (per Phase 4 UI refinements)  
**Design v3:** 52-week range bar — 14px tall (was 4px), with better target/current price markers (3px wide with glow effect)

**Status:** Intentional removal. Watchlist DB still exists; can be re-added later if needed for cloud view.

**Recommendation:** **Skip for v0.1.** Watchlist feature is deferred to v0.2+ or cloud public view phase.

---

### CHANGE 9: Column Visibility Toggle (Holdings)
**Current state:** Holdings table shows all columns; no hide/show toggle  
**Design v3:** "Columns ▾" button to toggle optional columns:
- **Required** (always visible): Ticker, Account, Mkt price, Today, Mkt value, % Port
- **Optional** (toggleable): Name, Asset class, Qty, ACB / sh

**Implementation gap:**
- Holdings uses `st.data_editor` which doesn't expose column_order dynamically
- Need to manage which columns to show via session state + conditional column_config

**Feasibility:** Medium (requires state management + conditional column rendering)  
**Effort:** 5 hours  
**Recommendation:** **Implement in Phase 5b.** Nice UX refinement but not critical.

**Phase:** 5b

**Implementation sketch:**
```python
# In holdings.py
if "holdings_visible_cols" not in st.session_state:
    st.session_state.holdings_visible_cols = {
        'name': True, 'assetClass': True, 'qty': False, 'acbPS': False
    }

col1, col2 = st.columns([10, 1])
with col2:
    with st.popover("Columns ▾"):
        for col_name in ['Name', 'Asset class', 'Qty', 'ACB / sh']:
            st.checkbox(col_name, value=st.session_state.holdings_visible_cols.get(col_name.lower(), True),
                       key=f"col_{col_name}")

# Filter dataframe columns based on toggles
visible_cols = ['Ticker', 'Account', ...]
if st.session_state.holdings_visible_cols.get('name'):
    visible_cols.insert(2, 'Name')
# ... etc
```

---

### CHANGE 10: Gap % Color-Coded in Watchlist
**Current state:** Watchlist removed  
**Design v3:** Gap % column shows color-coded indicator:
- 🟢 Green = at or below target
- 🟡 Amber = within 10% away
- 🔴 Red = more than 10% above target
- Format: "● At target" / "▼ X.X%" with color dot indicator

**Status:** Intentional removal. Watchlist deferred.

**Recommendation:** **Skip for v0.1.**

---

## Summary Table: Implementation Roadmap

### Phase 5a — High-Priority (Implement Now)

| Change | Task | Effort | Status | Notes |
|--------|------|--------|--------|-------|
| 1 | Dashboard KPI: Today's Δ + Biggest mover | 2h | 🔴 Not done | New cards for daily change & top mover |
| 3 | Net Worth: Inline editing for Cash | 3h | 🔴 Not done | Convert to st.data_editor row |
| 4 | Net Worth: Slider + number input | 4h | 🔴 Not done | Side-by-side with state sync |
| 5 | Net Worth: Privacy legend badge | 2h | 🔴 Not done | Conditional header badge |
| 7 | Leverage: Portfolio drawdown slider | 3h | 🔴 Not done | Second slider for market stress test |
| **Total** | | **14h** | | ~1.5–2 days of focused work |

### Phase 5b — Medium-Priority (If Time Allows)

| Change | Task | Effort | Status | Notes |
|--------|------|--------|--------|-------|
| 2 | Nav subtitles | 8h | 🟡 Hard | Defer to v1 (React) |
| 6 | Settings: Single Save per section | 6h | 🔴 Not done | Redesign Settings layout |
| 9 | Holdings: Column toggle | 5h | 🔴 Not done | Popover button + state mgmt |
| **Total** | | **19h** | | 2–3 days if doing all |

### Phase 5c / Deferred

| Change | Task | Effort | Status | Notes |
|--------|------|--------|--------|-------|
| 2 | Nav subtitles | 8h | 🟡 Hard | Requires custom CSS nav (fragile) |
| 8 | Watchlist: Sparkbar | — | ⏭️ Deferred | Watchlist removed; re-add if needed v0.2+ |
| 10 | Watchlist: Gap color-coding | — | ⏭️ Deferred | Same as #8 |

---

## Feasibility & Pushback

### What's Realistic to Ship

**Phase 5a (14 hours)** is **achievable in 1.5–2 days** and delivers high-value improvements:
- Dashboard becomes more insightful (daily moves matter)
- Leverage monitoring gets stress-test capability (critical for margin risk)
- Net Worth becomes interactive (feel of modern app)
- Clear privacy indication (compliance + UX)

**Recommendation:** Commit to Phase 5a. It's high-value, low-risk.

### What's Worth Skipping

**Change 2 (Nav subtitles):**
- Requires custom CSS navigation (fragile on Streamlit upgrades)
- Marginal UX gain (current tabs are clear enough)
- 8 hours of effort for 5% UX improvement
- **Skip.** Revisit in v1 (React).

**Changes 8 & 10 (Watchlist):**
- Intentionally removed per Phase 4
- Would need 8–12 hours to rebuild + test
- Email summaries cover the use case
- **Skip for v0.1.** Re-assess in v0.2 if cloud dashboard needed.

### Reality Check on Column Visibility (Change 9)

"Column visibility toggle" sounds modern, but:
- **Local-only app** — you're the only user, you know which columns matter
- **Data editor column_config** is rigid in Streamlit (hard to toggle dynamically)
- **8-hour refactor** for a QoL feature you don't need today
- **Recommendation:** **Skip or defer to Phase 5c.** Not worth it for v0.1.

---

## Phase Execution Plan

### Phase 5a — "Core Improvements" (Start ASAP)

**Days 1–2 (14 hours):**

1. **Dashboard KPI rework** (2h)
   - Add `today_delta()` and `biggest_mover()` functions to calcs.py
   - Replace Unrealized P/L card with Today's Δ
   - Add Biggest mover card
   - Test with live prices

2. **Leverage drawdown slider** (3h)
   - Add portfolio drawdown slider (0–50%, RED)
   - Compute stressed portfolio value
   - Show stressed ratio + delta + warnings
   - Test edge cases (ratio > 2.0)

3. **Net Worth inline editing + privacy legend** (5h)
   - Convert Net Worth ledger to `st.data_editor` layout
   - Implement inline editing for Cash, Property, Mortgage
   - Add privacy legend badge in panel header
   - Sync with existing privacy toggle

4. **Net Worth slider + number input** (4h)
   - Add side-by-side st.slider + st.number_input for Property and Mortgage
   - Ensure both update same state variable
   - Set realistic slider ranges (Property: $0–2M, Mortgage: $0–1M)

**Testing:** Manual QA on all screens, test with various data ranges.  
**Commit message:** `feat: design v3 phase 5a — dashboard KPI overhaul, leverage stress test, inline editing`

### Phase 5b — "Polish" (If Schedule Allows)

**Days 3–4 (11 hours, estimate):**

1. **Settings refactor** (6h)
   - Redesign Settings into sections (Security, Borrowing, Refresh, FX, Imports, About)
   - One "Save changes" button per section
   - Green success feedback (✓ Saved · Settings updated)

2. **Holdings column toggle** (5h)
   - Add Columns popover menu
   - Manage visibility state in session_state
   - Conditional column_config in st.data_editor

**Testing:** Full Settings flow, column toggle on Holdings, all sections.  
**Commit message:** `feat: design v3 phase 5b — settings sections, holdings column toggle`

### Phase 5c — Decision Gate (Post-Ship)

After Phase 5a/5b:
- **Does Streamlit fidelity hold up?** → Yes: maintain. → No: plan v1 (FastAPI+React)
- If v1 planned: watchlist + nav subtitles become React components (trivial in React)

---

## Current Implementation Notes

### Known Gaps (Verified)
- Dashboard missing: Today's Δ, Biggest mover (verified in dashboard.py line 70–94)
- Leverage missing: Portfolio drawdown slider (verified in leverage.py)
- Net Worth: All read-only (verified in net_worth.py)
- Holdings: No column toggle (verified in holdings.py)
- Settings: Unknown (need to verify full Settings screen)

### What Works
- Privacy mode toggle (theme.py + auth.py)
- Basic KPI cards with colored top borders
- Sliders on Leverage screen (HELOC draw works)
- Color palette matches v3 spec exactly

---

## Questions for Clarification

1. **Watchlist comeback?** v3 shows watchlist design. Should I rebuild it as part of Phase 5, or keep it deferred?
   - *Recommendation:* Defer. Keep watchlist DB; re-add screen only if public cloud view planned.

2. **Nav subtitles priority?** Worth the CSS complexity?
   - *Recommendation:* Defer to v1. Streamlit tabs sufficient.

3. **Slider ceiling limits?** Current Streamlit sliders have fixed max. Is removing ceiling a blocker?
   - *Recommendation:* No. Set slider max to $3M and allow number input to exceed it. Good enough.

4. **Email summary alignment?** Should daily email also show Today's Δ and Biggest mover?
   - *Recommendation:* Yes. Update `scripts/email_summary.py` to include new KPIs alongside Phase 5a.

---

## Conclusion

**v3 design is feasible within Streamlit.** The 10 changes break down as:
- **5 high-priority** (14h Phase 5a) → Do immediately
- **3 medium-priority** (19h Phase 5b) → Do if time
- **2 deferred** (watchlist, nav subtitles) → Revisit in v1 or v0.2

**Recommendation:** Ship Phase 5a in next 2 days. It doubles the app's insight (daily moves, stress test, interactivity) without breaking anything. Phase 5b can wait; it's polish.

