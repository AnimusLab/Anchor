# Anchor Audit — `login()`

---

## Symbol

- **Name:** `login`
- **Type:** Function
- **Module:** `django.contrib.auth`
- **File:** `django/contrib/auth/__init__.py`
- **Anchor commit:** `7cc4068c4470876c526830778cbdac2fdfd6dc26`
- **Anchor date:** 2012-10-01
- **Anchor confidence:** High (inferred)

---

## Intent Anchor (Frozen)

**Original intent:**  
**Persist an authenticated user’s identity in the session for the duration of a browser session.**

**Anchor evidence:**
- Docstring explicitly describes persisting user ID and backend in session
- Stores `SESSION_KEY` and `BACKEND_SESSION_KEY` in `request.session`
- Manages session lifecycle (`flush`, `cycle_key`)
- Emits `user_logged_in` signal
- Performs no credential validation

---

## Original Assumptions (2012)

The original implementation assumes that:

1. The user has already been authenticated prior to invocation.
2. Authentication state is persisted via server-side session storage.
3. The request object has session middleware enabled.
4. Session mutation is synchronous and immediate.
5. Authentication state is browser-session–scoped, not token-based.

These assumptions define a narrow, session-based responsibility.

---

## Present-Day Usage (Observed)

### Identified Roles

1. **Session-Based Authentication State Creation**
   - Traditional web login flows
   - Django Admin authentication
   - Post-registration auto-login
   - User impersonation for support/admin tooling
   - Session expiry customization (e.g. “remember me”)
   - **Estimated usage:** ~100%

All observed usage creates or replaces session-based authentication state.

---

## Drift Analysis

- No additional authentication paradigms introduced.
- No token, API, or stateless usage observed.
- Function signature and behavior remain unchanged.
- All usage aligns with original assumptions.

No responsibility expansion detected.

---

## Verdict

**Verdict:** ✓ **Aligned**

### Justification

- `login()` was designed to persist authenticated user identity in the session.
- The function continues to do exactly this and nothing more.
- All observed usage invokes `login()` solely to create or update session-based authentication state.
- No semantic role proliferation or intent displacement exists.

---

## Canonical Anchor Output

✓ login()

Anchored to:
Persist an authenticated user’s identity in the session (2012)

Current roles:

Session-based authentication state creation (~100%)

Verdict:
Aligned

Rationale:
login() creates and manages session-based authentication state by
storing user identity in request.session. All observed usage patterns
match the original design. No drift or responsibility expansion detected.


---

## Audit Confidence

**Confidence:** Very High

**Basis:**
- Explicit, narrow original intent
- Simple and unchanged implementation
- Single semantic role across all usage
- No ecosystem-driven expansion pressure

---

**End of Audit**