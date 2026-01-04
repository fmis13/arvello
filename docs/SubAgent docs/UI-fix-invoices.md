# UI Fix: Invoices List (Spec & Analysis)

## Summary

This document scopes, analyzes, and proposes minimal fixes for UI issues affecting the Invoices list view and related list/table views. Focus areas: empty value handling, table layout and overflow, spacing & icon sizing, row status styling, date formatting, accessibility (contrast and keyboard), and consistency across list views.

---

## Key visual issues observed ✅

1. **Inconsistent empty-value display**
   - In `invoices.html` the invoice title fallback shows the glyph `∅` (line ~36). Other places (history helpers and history view) use `(prazno)` or omit the value, resulting in inconsistent UX.
   - File: `arvello/arvelloapp/templates/invoices.html` (around the `<td>{% if invoice.title %}...` line).

2. **Inline styles for overdue row highlight**
   - Overdue status is applied via `style="background-color: ..."` directly in the `<tr>` (lines ~25-33), which is hard to theme and inconsistent with design tokens.
   - File: `arvello/arvelloapp/templates/invoices.html` (inside the `{% for invoice in invoices %}` row tag).

3. **Unformatted dates**
   - `{{ invoice.dueDate }}` prints the ISO date (`YYYY-MM-DD`) instead of locale-friendly `DD.MM.YYYY`.
   - File: `arvello/arvelloapp/templates/invoices.html` (dueDate column), and similar patterns in other list templates (e.g., `offers.html`, `clients.html` where dates appear).

4. **Action buttons and icons use inline styles & are crowded**
   - `style="font-size: 16px;"` used on icon spans inside action buttons and many small inline classes lead to inconsistent sizing and spacing.
   - File: `arvello/arvelloapp/templates/invoices.html` (action buttons column).

5. **Potential table overflow & responsiveness issues**
   - Long client or subject names cause table cells to grow and can cause awkward horizontal scrolling or wrapping; there are no rules to `min-width` the action column or to clamp/word-break long strings.
   - File: `arvello/arvelloapp/templates/invoices.html` and other table-based list templates (`clients.html`, `offers.html`, `salaries.html`).

6. **Missing descriptive title/tooltip for truncated content**
   - `{{ invoice.notes|truncatechars:50 }}` truncates notes but has no `title` attribute to show full content on hover.
   - File: `arvello/arvelloapp/templates/invoices.html` (notes column).

7. **Accessibility & color contrast concerns**
   - Overdue background colors (`rgba(217, 119, 6, 0.1)` and `rgba(220, 38, 38, 0.1)`) provide low contrast for text; prefer using border or stronger contrast or a label (and test with contrast tools).
   - Focus styles are applied inline in JS (focus outline), but some interactive elements lack explicit keyboard affordances in narrow viewports.

---

## Root causes with file references and snippets 🔍

1. Inconsistent empty-value indicator (invoices):

File: `arvello/arvelloapp/templates/invoices.html` (snippet)
```django
<td>{% if invoice.title %}{{ invoice.title }}{% else %}∅{% endif %}</td>
```
Cause: Template-level fallback using Unicode symbol rather than site-wide formatting function or consistent mark-up.

2. Inline overdue styles:

File: `arvello/arvelloapp/templates/invoices.html` (snippet)
```django
<tr
  {% if invoice.get_overdue_status == "warning" %}
    style="background-color: rgba(217, 119, 6, 0.1);"
  {% elif invoice.get_overdue_status == "danger" %}
    style="background-color: rgba(220, 38, 38, 0.1);"
  {% endif %}
>
```
Cause: Inline styles make changing colors, contrast, and theming harder and bypass design tokens in `ui.css`.

3. Unformatted dates:

File: `arvello/arvelloapp/templates/invoices.html` (snippet)
```django
<td>{{ invoice.dueDate }}</td>
```
Cause: Using object field directly instead of Django `date` filter or a helper filter.

4. Action icons inline font-size & styling:

File: `arvello/arvelloapp/templates/invoices.html` (snippet)
```django
<span class="material-symbols-outlined" style="font-size: 16px;">download</span>
```
Cause: Inline styling instead of centralized CSS rule.

5. Note truncation without title attribute:

File: `arvello/arvelloapp/templates/invoices.html` (snippet)
```django
<td>{{ invoice.notes|truncatechars:50 }}</td>
```
Cause: Truncate used, but UX would benefit from full-value tooltip or accessible expansion.

6. Table column sizing & responsive behavior:

Files: `arvello/arvelloapp/templates/*.html` — pattern: tables are inside `.table-responsive` but have no guidance for column min-widths or action-column fixed width.

---

## Proposed minimal and safe changes (code snippets and exact files) 🔧

Goal: Minimal, low-risk CSS + template tweaks that don't change data model or backend.

1. Replace `∅` fallback with consistent `empty-value` markup and accessible label

File: `arvello/arvelloapp/templates/invoices.html` — around the Title cell (approx. line where current fallback is used)

Replace:
```django
<td>{% if invoice.title %}{{ invoice.title }}{% else %}∅{% endif %}</td>
```
With:
```django
<td>
  {% if invoice.title %}
    {{ invoice.title }}
  {% else %}
    <span class="empty-value" aria-hidden="true">—</span>
    <span class="sr-only">(prazno)</span>
  {% endif %}
</td>
```

Add CSS to `arvello/static/css/ui.css` (near table styles, e.g. after `.table tbody td`):
```css
/* Empty value style */
.empty-value {
  color: var(--color-text-tertiary);
  font-style: italic;
}
```
Rationale: Uses accessible SR-only text for screen readers and consistent visual indicator; `—` is more conventional than `∅`.

Risk: Very low.

Estimated dev time: 10–20 minutes.

---

2. Replace inline overdue styles with classes

File: `arvello/arvelloapp/templates/invoices.html` — change the `<tr>` condition

Replace inline style logic:
```django
<tr
  {% if invoice.get_overdue_status == "warning" %}
    style="background-color: rgba(217, 119, 6, 0.1);"
  {% elif invoice.get_overdue_status == "danger" %}
    style="background-color: rgba(220, 38, 38, 0.1);"
  {% endif %}
>
```
With:
```django
<tr class="{% if invoice.get_overdue_status == 'warning' %}row-overdue-warning{% elif invoice.get_overdue_status == 'danger' %}row-overdue-danger{% endif %}">
```

Add CSS to `arvello/static/css/ui.css` (near Alerts section):
```css
/* Overdue row highlights */
.row-overdue-warning { background-color: rgba(217, 119, 6, 0.08); }
.row-overdue-warning td { border-left: 4px solid rgba(217, 119, 6, 0.3); }
.row-overdue-danger { background-color: rgba(220, 38, 38, 0.08); }
.row-overdue-danger td { border-left: 4px solid rgba(220, 38, 38, 0.4); }
```
Rationale: Uses classes and subtle left border to improve contrast; easy to change design tokens later.

Risk: Low.

Estimated dev time: 15–30 minutes.

---

3. Format dates with Django `date` filter (or adopt a site-wide `format_date` filter)

Option A (quick): Use Django date filter directly in template.

File: `arvello/arvelloapp/templates/invoices.html` — change dueDate cell

Replace:
```django
<td>{{ invoice.dueDate }}</td>
```
With:
```django
<td>{{ invoice.dueDate|date:"d.m.Y." }}</td>
```

Option B (preferred for consistency): Create a small template filter `format_date` in `history_extras.py` (or a new `formatting_filters.py`) and use it across templates.

Filter (add to `arvello/arvelloapp/templatetags/history_extras.py`):
```python
from django import template
register = template.Library()

@register.filter
def format_date(value, fmt="d.m.Y."):
    if not value:
        return ''
    try:
        return value.strftime('%d.%m.%Y') if hasattr(value, 'strftime') else str(value)
    except Exception:
        return str(value)
```

Then update template to:
```django
<td>{{ invoice.dueDate|format_date }}</td>
```

Risk: Low (adding a simple filter). Ensure tests for date display updated.

Estimated dev time: 20–40 minutes (including adding small unit test).

---

4. Add tooltip/title to truncated notes and show full notes on hover

File: `arvello/arvelloapp/templates/invoices.html` — notes cell

Replace:
```django
<td>{{ invoice.notes|truncatechars:50 }}</td>
```
With:
```django
<td title="{{ invoice.notes|escape }}">{{ invoice.notes|truncatechars:50 }}</td>
```

Rationale: Non-invasive UX improvement for discovery without JS.

Risk: Very low.

Estimated dev time: 5–10 minutes.

---

5. Centralize icon sizing, remove inline styles

File: `arvello/arvelloapp/templates/invoices.html` (and other templates where inline font-size specified)

Replace inline `style="font-size: 16px;"` or similar on icon spans with a utility class, e.g. `action-icon`:
```django
<span class="material-symbols-outlined action-icon">download</span>
```

Add CSS to `arvello/static/css/ui.css` (near icons decorations):
```css
/* Action icons in small buttons */
.action-icon { font-size: 16px; vertical-align: middle; }
.btn-sm .action-icon { font-size: 14px; }
```

Rationale: Consistent icon sizing & maintainable.

Risk: Very low.

Estimated dev time: 10–20 minutes.

---

6. Prevent column collapse and allow safe wrapping for long content; fix action column width

Add CSS to `arvello/static/css/ui.css` (near Tables section):
```css
/* Make action column narrower and fixed, allow other cells to wrap */
.table { table-layout: auto; }
.table td, .table th { overflow-wrap: break-word; word-break: break-word; }
.table .actions-col { white-space: nowrap; width: 120px; }
```

Template: mark actions column with class on `<th>` and `<td>`:

File: `arvello/arvelloapp/templates/invoices.html` — header & cell

Header:
```django
<th scope="col" class="text-center actions-col">Akcije</th>
```
Cell (same file):
```django
<td class="text-center actions-col"> ... </td>
```

Rationale: Keeps action buttons visible and consistent; avoids entire table flowing horizontally.

Risk: Low (CSS only). Test across viewport sizes.

Estimated dev time: 20–30 minutes.

---

7. Accessibility: Fix contrast and add ARIA labels

- Add `aria-label` to empty value span for screen readers (we already added `sr-only`).
- For overdue rows, add `aria-describedby` pointing to a hidden label (or add an extra column with a visually hidden status label) if needed.
- Use a color contrast check rule in QA steps.

Files: `arvello/arvelloapp/templates/invoices.html`, `arvello/static/css/ui.css` (CSS changes previously listed)

Risk: Low; improves accessibility.

Estimated dev time: 15–30 minutes.

---

## QA steps (browsers, viewports, accessibility) ✅

1. Manual visual testing
   - Browser matrix: Chrome (latest), Firefox (latest), Edge (latest), Safari (macOS & iOS latest if available)
   - Viewports: 1440 (desktop), 1024 (tablet), 768, 480 (mobile)
   - Steps:
     - Load /invoices/, verify table header alignment and actions width.
     - Confirm empty invoice title shows `—` and screen-reader reads “(prazno)”.
     - Confirm overdue rows show left border + background and that color contrast is acceptable.
     - Hover over truncated notes and confirm full notes appear in tooltip.
     - Confirm icons have consistent size and buttons don't wrap poorly.

2. Accessibility checks
   - Use Lighthouse accessibility audit and axe (browser extension)
   - Check color contrast for overdue rows and action buttons (WCAG AA minimum)
   - Tab through table rows and action buttons — ensure keyboard focus visible and in logical order

3. Automated tests to add
   - Template test: render invoices list with an invoice missing a title and assert that output contains the `empty-value` element and `sr-only` text.
   - Unit test for date filter if added: pass date and assert formatted result.

4. Snapshot/screenshots
   - Take before/after screenshots at 1024 and 480 widths of invoices list (instructions below for local generation).

---

## Roll-back plan & risk assessment ⚠️

All recommended changes are low-risk (CSS and small template changes). Rollback is trivial by reverting the commit(s) or applying a revert PR.

- Risk: Visual regressions in other list views if CSS selectors are too broad. Mitigation: Scope CSS rules to `.table` inside `.table-responsive` or use `.invoices-list .table` if needed.
- Risk: Small template changes might affect tests; mitigation: add/adjust unit tests.

---

## Implementation tasks for follow-up implementation subagent (self-contained) 🧩

Task 1 — Standardize empty values (Easy, 15m)
- Files to modify:
  - `arvello/arvelloapp/templates/invoices.html` — replace `∅` fallback with `empty-value` markup.
  - `arvello/static/css/ui.css` — add `.empty-value` style.
- Tests: Template test asserting fallback represented with `.empty-value` and SR-only text.

Task 2 — Replace inline overdue styles with classes (Easy, 30m)
- Files to modify:
  - `arvello/arvelloapp/templates/invoices.html` — replace inline style with conditional class.
  - `arvello/static/css/ui.css` — add `.row-overdue-warning` and `.row-overdue-danger` rules.
- Tests: Smoke test the rendered `<tr>` contains the class when `get_overdue_status` returns warning/danger.

Task 3 — Date formatting (Easy - Medium, 30–45m)
- Files to modify:
  - Add `format_date` filter to `arvello/arvelloapp/templatetags/history_extras.py` OR create `formatting_filters.py` file in `templatetags`.
  - Update `invoices.html` to use filter for `dueDate` and other templates using raw dates.
- Tests: Add a small unit test that asserts date format.

Task 4 — Action column & icon sizing (Easy, 20–30m)
- Files to modify:
  - `arvello/arvelloapp/templates/invoices.html` — add `actions-col` class to `<th>` and action `<td>`; replace inline icon styles with class `action-icon`.
  - `arvello/static/css/ui.css` — add `.action-icon` and `.actions-col` rules.
- Tests: Visual/DOM test asserting class exists.

Task 5 — Tooltip for truncated notes (Tiny, 10m)
- Files to modify:
  - `arvello/arvelloapp/templates/invoices.html` — add `title` attribute containing escaped notes.
- Tests: Template test verifying `title` attribute for notes column.

Task 6 — QA, screenshots & regression tests (Medium, 60m)
- Run visual verification and add basic snapshot tests if project has visual regression tooling.

---

## Screenshots & how to generate locally 📸

1. Start app locally (assuming venv activated):

```bash
# from project root
python manage.py runserver
# open http://127.0.0.1:8000/invoices/
```

2. Generate screenshots (example using puppeteer or manual):
- Manual: Open Chrome DevTools Device Toolbar and capture screenshots at widths 1440, 1024, 768, 480.
- Automated (if you have `puppeteer` or `playwright`): write a small script capturing the URL at desired widths.

3. For before/after diffs: capture screenshots before changes and after changes and compare via any image-diff tool.

---

## Asset/build & settings notes

- CSS changes are static; if `collectstatic` is used in deployment, run:

```bash
python manage.py collectstatic --noinput
```

- There’s no webpack/npm step needed for these CSS and template edits, since project uses static CSS files.

---

## Estimated time & difficulty summary

- Standardize empty values: 15 minutes — Very easy
- Replace inline overdue styles: 30 minutes — Easy
- Date formatting filter and template updates: 30–45 minutes — Easy/Medium
- Action column & icon sizing: 20–30 minutes — Easy
- Tooltip for truncated notes: 10 minutes — Very easy
- QA, tests, screenshots: 60 minutes — Medium

Total estimated time: ~3 hours (including QA and tests)

---

## Notes & Recommendations

- Apply changes incrementally in small PRs so design regressions are easy to review.
- Use the new `format_date` filter in other templates to ensure consistent date display.
- Consider adding a small visual regression (snapshot) check to the CI pipeline to prevent accidental regressions to tables and list views.

---

## Appendices

- Files scanned (non-exhaustive):
  - `arvello/arvelloapp/templates/invoices.html`
  - `arvello/arvelloapp/templates/clients.html`
  - `arvello/arvelloapp/templates/offers.html`
  - `arvello/arvelloapp/templates/salaries.html`
  - `arvello/arvelloapp/templatetags/history_extras.py`
  - `arvello/static/css/ui.css`



---

## QA Checklist (added by implementation)

- [ ] Visual check: invoices list at widths 1440, 1024, 768, 480 — confirm truncation and action column behavior ✅
- [ ] Accessibility: run Lighthouse / axe and confirm no new a11y regressions (empty-value announced via screen reader) ✅
- [ ] Cross-browser: spot-check Chrome, Firefox, and Edge for table layout ✅
- [ ] Regression: run full test suite locally and in CI ✅
- [ ] Deploy: run `python manage.py collectstatic --noinput` during deployment step if needed ✅

End of spec
