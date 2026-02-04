# Anchor
**The Federated Governance Engine for AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Federated](https://img.shields.io/badge/Status-Federated-green.svg)]()

> "Code drifts. Intent shouldn't. Governance must scale."

Anchor is an autonomous governance platform designed for the AI-Native era. It ensures that both your **Code** and your **AI Models** comply with universal standards (like FINOS) and local company policies.

---

## 🏛️ The Federated Model
Anchor operates on a unique "Constitution + State Law" architecture:
1. **The Constitution (`finos-master.anchor`):** Downloaded from the cloud. Contains universal security and AI governance rules.
2. **The State Law (`policy.anchor`):** Local overrides. Banks/projects can add specific rules or change the severity of universal ones.

---

## 🚀 Key Capabilities

### 1. Code Enforcement (v2)
Turns GenAI Threat Models into executable CI/CD blockers. It uses AST analysis (`tree-sitter`) to detect semantic violations.
* **Bridge Mode:** Parse Markdown Threat Models and activate related rules.
* **Deep Analysis:** Detects unsafe imports, dangerous function calls, and improper inheritance.

### 2. Model Auditing (New)
A vendor-agnostic plugin system to validate LLM model weights (GGUF, SafeTensors, etc.) before deployment.
* **Verify Provenance:** Ensure training data sources are license-compliant.
* **Analyze Weights:** Detect potential backdoors or corruption in model files.
* **Multi-Platform:** Support for LM Studio, AnchorGrid, HuggingFace, and generic systems.

### 3. The Historian (v1)
Prevents "Architectural Drift" by analyzing Git history to find the original intent of a symbol, stopping AI agents from creating "Zombie Abstractions."

---

## 🛠️ Quick Start

### 1. Installation
```bash
git clone https://github.com/Tanishq1030/anchor
cd anchor
pip install -e .
```

### 2. Initialize Policies
Downloads the FINOS Master Constitution and creates a local project policy.
```bash
anchor init
```

### 3. Run a Code Scan
```bash
anchor check --dir ./src --verbose
```

### 4. Audit a Model
```bash
anchor check --model ./my-model.gguf --metadata ./metadata.json
```

---

## 🤖 CI/CD Integration
Anchor is designed to be the "Gatekeeper" in your GitHub Actions. If a pull request violates the FINOS constitution, Anchor blocks the merge and provides a detailed violation report.

```yaml
- name: Run Governance Check
  run: anchor check --dir ./anchor --json-report
```

---

## 📁 Project Structure
* `anchor/core/`: The enforcement engine and policy merger.
* `anchor/plugins/`: Vendor-agnostic readers for model formats.
* `finos-master.anchor`: The master governance laws.
* `policy.anchor`: Local project-specific rules.

---

## ⚖️ License
MIT License. Built for the era of AI-Assisted Engineering and Automated Governance.
