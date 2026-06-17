# Technical Roadmap: Anchor V2 (Static Foundation)

The V2 lifecycle established the static analysis, AST query engine, and local configuration foundations of Anchor.

---

## 🎯 Milestones

### 1. Abstract Syntax Tree (AST) Parsing Integration
*   Shift away from unstable regex-based parsing to structural syntax trees.
*   Integrate [Tree-sitter](https://github.com/tree-sitter/tree-sitter) bindings.
*   Develop language-specific parsing adapters for **Python** (`adapters/python.py`) and **TypeScript/JavaScript** (`adapters/typescript.py`).

### 2. Core CLI Commands
*   Implement `anchor init` to bootstrap project config files.
*   Implement `anchor check` to evaluate repository files against configurations.
*   Map exit status codes correctly (exit `0` on clean runs, `1` on compliance warnings/errors).

### 3. Local Policy Overrides (`policy.anchor`)
*   Introduce `policy.anchor` allowing developers to customize severity settings.
*   Establish the baseline rule merging algorithm.
*   Enforce the "Raise-Only" mechanism to prevent projects from overriding universal security rules below the CISO baseline.

### 4. Developer Workstation Git Integration
*   Automate pre-commit hooks during `anchor init`.
*   Establish targeted scanning of Git staged files to optimize checking speeds.
*   Provide human-readable terminal output using icons and colors.
