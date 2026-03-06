# Case Studies

This directory contains real-world empirical studies conducted using the Anchor framework.
Each study validates a different capability of Anchor's governance and drift detection model.

---

## Structure

```
case-studies/
├── architectural_audits/     ← Multi-symbol drift audits on real open-source projects
│   └── django/               ← Django auth + forms: 6 symbols audited, 2 verdicts
│
└── governance_audits/        ← Compliance, policy, and qualitative governance analysis
    └── perspective/          ← Qualitative & compliance perspective study
        ├── audit_summary.md
        └── violation_report.txt
```

---

## Architectural Audits

Intent-anchored audits run against real, widely-deployed open-source codebases.
These demonstrate that architectural drift is measurable, reproducible, and actionable.

| Project                                  | Symbols Audited | Verdicts                                                      | Highlights                                             |
| ---------------------------------------- | --------------- | ------------------------------------------------------------- | ------------------------------------------------------ |
| [Django](./architectural_audits/django/) | 6               | ✅ 2 Aligned · ⚠️ 2 Semantic Overload · 🛑 2 Intent Violation | `Form` drifted from HTML renderer to generic validator |

---

## Governance Audits

Compliance and policy-oriented studies — how Anchor drift findings map to organizational
risk, remediation costs, and governance decisions.

See [`governance_audits/`](./governance_audits/).

---

## Adding a New Case Study

1. Create a new directory under `architectural_audits/<project>/`
2. Run `anchor check drift <target>` in the repo being audited
3. For each non-ALIGNED symbol, run `anchor check drift path/to/file.py::Symbol`
4. Use `docs/manual_audit_template.md` to write the detailed per-symbol audit
5. Add a `README.md` summarizing the findings
