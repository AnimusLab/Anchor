# Anchor Audit — `django.forms.Form`

---

## Symbol

- **Name:** `Form`
- **Type:** Class
- **Module:** `django.forms`
- **File:** `django/forms/forms.py`
- **Anchor commit:** `a92e7f37c4ae84b6b8d8016cc6783211e9047219`
- **Anchor date:** 2012-07-04
- **Anchor confidence:** High (inferred)

---

## Intent Anchor (Frozen)

**Original intent:**  
**Define and render HTML forms for server-side template rendering.**

**Anchor evidence:**
- Dedicated HTML rendering methods: `as_table()`, `as_ul()`, `as_p()`
- Centralized HTML formatter: `_html_output()`
- Explicit template-facing output via `mark_safe()`
- Inline comments describe declarative form definition for rendering
- No serialization or non-HTML output paths in original design

---

## Original Assumptions (2012)

The original implementation assumes that:

1. Forms generate HTML output strings.
2. Validation executes synchronously in a single, blocking pass.
3. Input arrives as complete, form-encoded key–value mappings.
4. All data is available at validation time and validated atomically.
5. Output is consumed as renderable HTML markup in templates.

These assumptions define the symbol’s intent boundary.

---

## Present-Day Usage (Observed)

### Identified Roles

1. **HTML Form Rendering + Validation**
   - Traditional Django views
   - Django Admin
   - Uses rendering (`as_*`) and validation
   - Output: HTML
   - **Estimated usage:** 20–30%

2. **Validation-Only (No HTML)**
   - Django REST Framework
   - GraphQL backends
   - Async API endpoints
   - Uses validation only (`is_valid`, `cleaned_data`)
   - Rendering methods never invoked
   - Output: JSON / exceptions
   - **Estimated usage:** 60–70%

---

## Drift Analysis

- The dominant modern role treats `Form` as a generic data validator.
- HTML rendering functionality remains present but unused in the majority of cases.
- The original primary responsibility is no longer the primary mode of use.
- No explicit redefinition of intent exists in commits or documentation.
- Drift occurred through ecosystem adoption, not deliberate redesign.

---

## Verdict

**Verdict:** ❌ **Intent Violation**

### Justification

- `Form` was designed as an HTML form abstraction with explicit rendering behavior.
- Modern usage is dominated by validation-only contexts where rendering is unused.
- The original intent remains present but is now a minority use case.
- The symbol’s meaning shifted without explicit re-anchoring.

---

## Canonical Anchor Output

⚠ Form

Anchored to:
Define and render HTML forms for server-side template rendering (2012)

Current roles:

HTML form rendering + validation (~20–30%)

Validation-only usage (~60–70%)

Verdict:
Intent Violation

Rationale:
Form was designed as an HTML form abstraction. In modern Django
ecosystems, most Form instances are used exclusively for non-HTML
validation. The original responsibility persists but is no longer primary.


---

## Audit Confidence

**Confidence:** High

**Basis:**
- Explicit HTML-centric original design
- Clear and repeatable usage displacement
- No formal intent redefinition
- Verdict is evidence-based and challengeable

---

**End of Audit**