# What is Anchor?

Anchor is an open-source AI governance and compliance engine designed to help organizations detect, audit, and enforce policy requirements across AI systems.

Unlike traditional governance approaches that rely primarily on documentation, manual reviews, or probabilistic monitoring, Anchor focuses on verifiable enforcement and auditable evidence.

Anchor currently provides two governance layers:

## Layer 1: Static Governance Auditing

Layer 1 analyzes source code, AI integrations, and architectural structures before deployment.

It can:

* Scan repositories for governance, security, and compliance violations.
* Evaluate projects against regulatory and framework requirements.
* Detect architectural drift and intent drift across evolving codebases.
* Generate compliance findings suitable for engineering and audit teams.
* Integrate directly into CI/CD pipelines.

Supported governance sources currently include:

* OWASP
* NIST
* FINOS
* EU AI Act
* RBI
* SEC
* Additional framework and domain-specific rulepacks

---

## Layer 2: Runtime Governance (Experimental)

Layer 2 extends governance into runtime environments.

Instead of evaluating code only before deployment, Layer 2 can observe and enforce governance requirements while AI systems are operating.

Capabilities include:

* Runtime policy enforcement
* Prompt and response interception
* Cryptographic audit logging
* Decision Audit Chains (DAC)
* Policy-based execution controls
* Governance telemetry collection

Layer 2 is intended for high-assurance and regulated environments where auditability and enforcement must continue after deployment.

---

# Why Anchor Exists

Modern AI systems increasingly operate in environments subject to:

* Financial regulations
* Data protection requirements
* AI governance frameworks
* Internal enterprise policies
* Security controls

Most governance approaches identify violations after they occur.

Anchor was built around a different assumption:

> Governance should be enforceable, measurable, and auditable.

The project focuses on creating governance infrastructure that can be integrated directly into engineering workflows rather than existing only as documentation or organizational policy.

> [!NOTE]  
> **The Determinism Principle**: Traditional safety checks are probabilistic (relying on secondary classifier models to guess risk). Anchor is entirely deterministic: same input, same compliance verdict. Every decision has an explainable structural AST verification path or network backstop rule, making it legally and mathematically admissible during audits.

---

# Core Capabilities

## Compliance Auditing

Evaluate repositories against governance rulesets and detect violations before deployment.

## Architectural Drift Detection

Anchor can analyze the historical evolution of a repository and identify situations where code behavior has drifted away from its original design intent.

Examples include:

* Semantic Overload
* Intent Violation
* Dependency Inertia

These patterns are documented in the project's drift taxonomy.

## Federated Governance

Organizations can select governance requirements from multiple sources simultaneously.

For example:

* OWASP + EU AI Act
* FINOS + SEC
* RBI + Internal Enterprise Policies

Anchor evaluates repositories against all selected governance sources in a unified audit process.

## CI/CD Integration

Anchor is designed to operate within existing development workflows, including:

* GitHub Actions
* GitLab CI/CD
* Local developer environments
* Pre-deployment validation pipelines

---

# Supported Languages

Anchor currently supports:

* Python
* TypeScript / JavaScript
* Go
* Java
* Rust

Additional language support may be added in future releases.

---

# Who Should Use Anchor?

Anchor is designed for:

* AI engineers
* Platform engineers
* Security teams
* Compliance teams
* AI governance practitioners
* Open-source maintainers
* Regulated organizations deploying AI systems

---

# Next Steps

If you're new to Anchor:

1. Install Anchor.
2. Initialize governance rulesets.
3. Run your first audit.
4. Review the generated findings.
5. Integrate Anchor into your CI/CD workflow.

Continue with:

* [Installation Guide](file:///d:/Anchor/docs/installation.md)
* [Getting Started Guide](file:///d:/Anchor/docs/getting-started.md)
* [CLI Reference](file:///d:/Anchor/docs/cli-reference.md)
* [Architecture Overview](file:///d:/Anchor/docs/ARCHITECTURE.md)
