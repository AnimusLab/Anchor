# GitLab CI/CD Integration Guide

Integrating Anchor into your GitLab CI/CD pipeline enables automated compliance validation. This guide provides a template and instructions for runner configuration.

---

## 📋 The GitLab CI/CD Pipeline Flow

```
GitLab Runner schedules job
         ↓
Runner spins up a Python environment
         ↓
Installs anchor-audit via pip
         ↓
Runs "anchor check" over repo
         ↓
Publishes HTML and JSON compliance reports as artifacts
```

---

## 🛠️ Configuration Template

Add the following job definition to your `.gitlab-ci.yml` file:

```yaml
stages:
  - test
  - compliance

anchor_compliance_check:
  stage: compliance
  image: python:3.11-slim
  
  variables:
    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

  cache:
    paths:
      - .cache/pip
      - .anchor/cache/

  before_script:
    - python -V
    - pip install --upgrade pip
    - pip install anchor-audit
    
  script:
    # Scan current repository, exit code is non-zero on error/blocker violations
    - anchor check . --severity error --json-report --generate-report
    
  allow_failure: false  # Change to true to log warnings without blocking pipeline
  
  artifacts:
    name: "anchor-compliance-findings-$CI_COMMIT_REF_NAME"
    when: always
    expire_in: 1 week
    paths:
      - .anchor/reports/
      - .anchor/telemetry/
```

---

## 💡 Customizing Runner Settings

### 1. Offline Cache Setup
If your runners operate in air-gapped environments without direct access to PyPI or the internet:
1.  Verify the remote constitution locally in your dev setup.
2.  Commit the `.anchor/` directory (including `.anchor/cache/constitution.anchor` and `mitigation.anchor`) to your git repository.
3.  Instruct the GitLab CI runner to evaluate checks locally:
    ```yaml
    script:
      - anchor check . --severity error --no-sandbox
    ```

### 2. Output Formatting for Merge Requests
If you want to view a JSON summary log parsed directly inside the GitLab Merge Request dashboard, expose the JSON telemetry artifact to your report parser:

```yaml
  artifacts:
    reports:
      junit: junit-compliance-report.xml # Optional conversion to map errors to tests
```
