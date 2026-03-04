# Governance Audits

Compliance, policy, and qualitative analysis of Anchor's findings — how drift verdicts
translate into real organizational risk, remediation cost, and governance decisions.

---

## Structure

```
governance_audits/
└── perspective/          ← Qualitative perspective study on a real violation report
    ├── audit_summary.md
    └── violation_report.txt
```

---

## Studies

### [Perspective](./perspective/)

A qualitative analysis of an Anchor audit from the lens of a governance and compliance team.
Examines how drift verdicts map to:

- Organizational risk exposure
- Remediation cost estimation
- Policy enforcement decisions
- Escalation paths for critical violations

---

## Adding a New Governance Study

1. Create a new subdirectory (e.g. `governance_audits/financial_compliance/`)
2. Document the policy context and relevant regulations
3. Map each Anchor verdict to a policy risk level
4. Estimate remediation cost and effort
5. Add a `README.md` in the subdirectory summarizing findings
