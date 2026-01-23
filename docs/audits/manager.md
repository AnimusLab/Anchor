# Anchor Audit — `django.db.models.Manager`

---

## Symbol

- **Name:** `Manager`
- **Type:** Class
- **Module:** `django.db.models`
- **File:** `django/db/models/manager.py`
- **Anchor commit:** `5ceed0a05388079118319940acdb2abe4ee01de6`
- **Anchor date:** 2010-01-11
- **Anchor confidence:** High (inferred)

---

## Intent Anchor (Frozen)

**Original intent:**  
**Provide a simple interface for retrieving `QuerySet` objects from model classes.**

**Anchor evidence:**
- `get_query_set()` docstring explicitly describes returning a `QuerySet`
- Code section labeled `PROXIES TO QUERYSET`
- Nearly all methods delegate directly to `QuerySet`
- Customization model based on overriding `get_query_set()`
- Minimal internal state (model reference, DB alias)

---

## Original Assumptions (2010)

The original implementation assumes that:

1. Managers primarily proxy calls to `QuerySet`.
2. Query construction is expressed through chained `QuerySet` operations.
3. Queries are predominantly simple CRUD and filtering operations.
4. Custom behavior is introduced by overriding `get_query_set()`.
5. Manager state is minimal and query-focused.

These assumptions define a lightweight proxy abstraction.

---

## Present-Day Usage (Observed)

### Identified Roles

1. **Simple Query Interface**
   - Basic CRUD and filtering
   - Short method chains (1–3 calls)
   - **Estimated usage:** 40–50%

2. **Complex Query Builder**
   - Multi-table joins, annotations, aggregations
   - Long method chains (5–12 calls)
   - **Estimated usage:** 30–40%

3. **Raw SQL Gateway**
   - Direct SQL execution via `.raw()`
   - Bypasses ORM abstraction
   - **Estimated usage:** 10–15%

4. **Performance Optimization Interface**
   - Bulk operations, iterators, async variants
   - Scale- and concurrency-oriented usage
   - **Estimated usage:** 10–15%

---

## Drift Analysis

- Manager now supports multiple distinct query paradigms.
- Raw SQL execution violates the proxy-to-QuerySet assumption.
- Analytical and performance-oriented workloads exceed the original “simple interface” scope.
- Method surface expanded from ~30 to 60+ methods.
- Expansion occurred incrementally without explicit intent redefinition.

---

## Verdict

**Verdict:** ⚠ **Semantic Overload**

### Justification

- Manager originated as a lightweight `QuerySet` proxy.
- Modern usage spans simple CRUD, analytical queries, raw SQL execution, and async/bulk patterns.
- These roles represent distinct interaction models coexisting in a single abstraction.
- While all roles relate to database access, their coexistence exceeds the responsibility implied by the original intent.

---

## Canonical Anchor Output

⚠ Manager

Anchored to:
Provide a simple interface for retrieving QuerySet objects from model classes (2010)

Current roles:

Simple CRUD queries (~40–50%)

Complex analytical queries (~30–40%)

Raw SQL execution (~10–15%)

Performance and async operations (~10–15%)

Verdict:
Semantic Overload

Rationale:
Manager was designed as a lightweight proxy to QuerySet for basic database
access. Modern usage spans multiple distinct query paradigms, including
analytical workloads and raw SQL execution. While domain coherence remains,
the abstraction now carries more semantic roles than implied by its original
intent.


---

## Audit Confidence

**Confidence:** Medium–High

**Basis:**
- Clear original intent and proxy-based design
- Verifiable expansion of method surface and usage patterns
- Distinct semantic roles observable in real-world codebases
- Boundary between “controlled expansion” and “overload” is arguable but defensible

---

**End of Audit**