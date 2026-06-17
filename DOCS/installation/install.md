# Installation

This guide explains how to install and initialize Anchor.

---

# Requirements

Anchor currently supports:

* Python 3.8+
* Git (required for architectural drift analysis)
* Linux, macOS, or Windows
* Access to a repository containing supported source files

Supported languages:

* Python
* TypeScript / JavaScript
* Go
* Java
* Rust

---

# Install Anchor

Install directly from PyPI:

```bash
pip install anchor-audit
```

Verify the installation:

```bash
anchor --version
```

Expected output:

```bash
anchor-audit 5.0.8
```

---

# Initialize Anchor

Navigate to your repository:

```bash
cd your-project
```

Initialize governance rulesets:

```bash
anchor init --all
```

This creates:

```text
.anchor/
policy.anchor
```

and downloads the selected governance packs.

---

# Select Specific Rule Sets

Instead of loading all governance sources, you can initialize specific regulators, frameworks, and domains.

Example:

```bash
anchor init \
  --regulators eu,rbi \
  --frameworks finos,owasp \
  --domains security,privacy
```

Examples:

```bash
anchor init --regulators sec
```

```bash
anchor init --frameworks nist
```

```bash
anchor init --domains ethics,privacy
```

---

# Local Governance Policies

Anchor automatically creates:

```text
policy.anchor
```

This file allows organizations to add stricter governance requirements on top of the selected rule packs.

Local policies may tighten enforcement but cannot weaken authoritative governance requirements.

> [!IMPORTANT]  
> **Enforcement Bounds**: The Policy Engine executes a strict merge where local settings can upgrade warnings to blockers or append internal policies, but any attempt to disable or downgrade a core regulator rule (like the EU AI Act) without proper authority is blocked by the cryptographic verification check.

Example:

```text
RequireHumanApproval:
  enabled: true
```

Custom policy file names can be specified during initialization:

```bash
anchor init --policy-name my_company.anchor
```

Anchor will automatically load the specified file on future scans.

---

# Pre-Provisioning the Sandbox

Anchor can optionally prepare the WASM sandbox environment during initialization.

```bash
anchor init --sandbox
```

This is useful for:

* CI/CD environments
* Docker images
* Air-gapped deployments
* Offline execution scenarios

---

# Synchronize Governance Packs

Update governance rulesets:

```bash
anchor sync
```

Restore modified or tampered rule files:

```bash
anchor sync --restore
```

---

# Verify Installation

Run a repository scan:

```bash
anchor check .
```

A successful scan will:

* Load governance packs
* Parse supported source files
* Evaluate compliance requirements
* Generate findings

---

# Troubleshooting

## Command Not Found

Verify Anchor is installed:

```bash
pip show anchor-audit
```

Ensure the Python scripts directory is available in your PATH.

---

## Git Repository Required

Some capabilities, including architectural drift analysis, require access to Git history.

Verify:

```bash
git status
```

runs successfully inside the target repository.

---

## Unsupported Language

Anchor currently supports:

* Python
* TypeScript / JavaScript
* Go
* Java
* Rust

Files outside these languages will be ignored by the scanning engine.

---

# Next Step

Continue with:

* First Audit Guide
* CLI Reference
* GitHub Actions Integration
* Architecture Overview
