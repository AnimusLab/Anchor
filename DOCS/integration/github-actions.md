# GitHub Actions Integration Guide

Integrating Anchor into your GitHub Actions workflow ensures compliance audits run automatically on every Pull Request.

---

## 🚀 Simple Out-of-the-Box Workflow

Create a new file named `.github/workflows/anchor.yml` in your repository and paste the following content:

```yaml
name: Anchor Audit

on:
  pull_request:

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Anchor
        run: pip install anchor-audit

      - name: Initialize Policies
        run: anchor init --all

      - name: Run Compliance Scan
        run: anchor check .
```

This workflow runs on every pull request, downloads the mandatory constitutional rules, and blocks the merge if any blocker or error violations are detected.

---

## 🏢 Enterprise Production Workflow

For faster execution (using pip caches) and artifact reports publication:

```yaml
name: Anchor Enterprise Audit

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Required for git history analysis (drift)

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install Anchor
        run: pip install anchor-audit

      - name: Run Scan & Generate Report
        run: |
          anchor check . --severity error --json-report --generate-report

      - name: Upload Compliance Reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: anchor-compliance-report
          path: |
            .anchor/reports/
            .anchor/telemetry/
```
