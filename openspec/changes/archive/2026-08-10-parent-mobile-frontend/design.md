## Context

The parent backend API (`chemai-backend/app/api/v1/parent.py`) is complete with 16 endpoints covering bind-code management, child queries, weekly reports, notifications, and Agent SSE chat. Two static HTML prototypes exist (`parent-login.html`, 183 lines; `parent.html`, 550 lines) with hardcoded demo data and no JS business logic. Shared JS infrastructure (`auth.js`, `api-client.js`, `sse-client.js`) provides JWT auth, HTTP wrappers, and SSE streaming — all used by existing student-side pages.

See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Transform the two static HTML prototypes into fully interactive pages by adding JavaScript logic, without changing the existing HTML structure or CSS
- Reuse all existing shared JS modules (ChemAuth, ChemAPI, ChemSSE) without modification
- Match the UX patterns already established by the student-side mobile pages (e.g., practice.html, review.html)
- Keep the implementation as vanilla JS — no build tools, no npm dependencies, no framework migration

**Non-Goals:**
- New backend endpoints or schema changes (existing API is sufficient)
- Student-side pages or teacher-side pages
- New CSS framework or design system migration
- Offline support or PWA
- WeChat/DingTalk mini-program variants
- Backend bind-code lookup fix (`POST /parent/bind` requiring student_id) — tracked separately

## Decisions

### D1: Vanilla JS, single-file scripts

**Decision**: All JS logic lives inline in `<script>` blocks at the bottom of each HTML file. No separate `.js` files, no module bundlers.

**Rationale**: Matches the existing pattern of student-side pages (practice.html uses inline state management and API calls). Keeps the deployment model simple — one HTML file = one page. The two pages are independent enough that a shared parent-specific JS module would be premature.

**Alternatives considered**:
- Separate `parent.js` module → rejected: only 2 pages share logic (child selector state), not worth the indirection
- Vue 3 CDN SFC → rejected: overkill for 2 pages, mismatches existing pattern

### D2: Direct API consumption, no BFF layer

**Decision**: Pages call the REST API directly via `ChemAPI.apiGet/apiPost`. The SSE agent chat uses `ChemSSE.connect()` directly.

**Rationale**: The backend API is already designed for direct consumption. Field names in API responses match what the UI needs to render. No data transformation layer needed.

### D3: State as plain JS objects

**Decision**: Page state (selected child, active tab, active thread_id, notification page, etc.) stored in plain mutable objects (e.g., `var state = { currentChild: null, activeTab: 'tab1' }`). State changes trigger targeted DOM updates (not full re-renders).

**Rationale**: Matches existing student-side pages. For 2 pages with limited interactivity, a reactive framework or virtual DOM is unnecessary.

### D4: Lazy tab loading

**Decision**: Tab content loads API data only when the tab is first opened. Subsequent switches re-render from cached data unless the selected child changes.

**Rationale**: Reduces API calls on page load. The Overview tab (default active) loads immediately; Report and Messages load on first activation.

### D5: Child switcher as single source of truth

**Decision**: The `currentChild` state variable drives all data fetching. Every API call that takes `student_id` reads it from `state.currentChild.id`. The child selector component, tabs, and AI panel all share this one variable.

**Rationale**: Ensures data consistency — switching children refreshes everything visible, and the AI panel always targets the currently selected child.

## Risks / Trade-offs

- **[Risk] SSE reconnection not implemented** → The sse-client.js has no auto-reconnect. If the connection drops mid-stream, the parent must close and reopen the AI panel. **Mitigation**: Acceptable for MVP; can add reconnect in a follow-up.
- **[Risk] No test coverage for JS** → Vanilla JS inline scripts are not covered by the existing pytest suite. **Mitigation**: Manual testing on the 2 pages; backlog a Playwright/Cypress task for the next cycle.
- **[Trade-off] Inline scripts vs separate files** → Inline scripts make the HTML files longer (~800–1000 lines each) but keep deployment dead simple (no build step). Given 2 pages, this is the right trade-off for now.
- **[Trade-off] No i18n** → All UI text is hardcoded Chinese. Acceptable for a domestic-market product.
