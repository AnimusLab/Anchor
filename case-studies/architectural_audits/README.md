# Architectural Audits

Intent-anchored drift audits conducted against real, widely-deployed open-source codebases.

These studies demonstrate that **architectural drift is measurable, reproducible, and actionable**
using Anchor's history engine + verdict engine pipeline.

---

## Methodology

For each symbol:

1. **Intent Anchor** — git history traced to the symbol's creation commit; original docstring / structure extracted
2. **Usage Analysis** — all call sites in the current codebase collected and clustered by semantic role
3. **Drift Analysis** — cluster compatibility against anchor assumptions determined
4. **Verdict** — one of: ✅ Aligned · ⚠️ Semantic Overload · 🛑 Intent Violation · 📦 Dependency Inertia · 📈 Complexity Drift

See [`docs/manual_audit_template.md`](../../docs/manual_audit_template.md) for the full audit format.

---

## Audited Projects

### [Django](./django/) — `django/contrib/auth` + `django/forms`

> **"Some of the most-used Python code in the world has drifted silently for over a decade."**

| Symbol                                       | Type     | Verdict              | Key Finding                                                      |
| -------------------------------------------- | -------- | -------------------- | ---------------------------------------------------------------- |
| [`Form`](./django/form.md)                   | Class    | 🛑 Intent Violation  | Designed as HTML renderer; 60–70% of usage never renders HTML    |
| [`authenticate()`](./django/authenticate.md) | Function | ⚠️ Semantic Overload | Now spans 3 auth paradigms beyond original credential validation |
| [`ModelForm`](./django/modelform.md)         | Class    | 🛑 Intent Violation  | ORM coupling now used purely for API validation                  |
| [`User`](./django/user.md)                   | Class    | ⚠️ Semantic Overload | Identity model reused as generic permission carrier              |
| [`login()`](./django/login.md)               | Function | ✅ Aligned           | Session persistence: unchanged in 12+ years                      |
| [`UserManager`](./django/manager.md)         | Class    | ✅ Aligned           | User creation intent maintained across versions                  |

**Summary:** 4 of 6 symbols show measurable drift. 2 show Intent Violation — meaning primary usage
has displaced the original purpose entirely.

---

## Reproducing This Audit

```bash
# Clone Django into a local path
git clone https://github.com/django/django D:/django

# Run the full drift scan on django/contrib/auth
anchor check drift django/contrib/auth/ --repo D:/django --only-violations

# Deep-dive on a specific symbol
anchor check drift django/contrib/auth/__init__.py::authenticate --repo D:/django
```
