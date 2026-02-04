# LM Studio Demo Setup for Anchor-Audit

This directory contains everything needed to demo anchor-audit with LM Studio.

---

## 🎯 Demo Scenario

**Story:**  
DEX Labs (crypto company) rents an LLM from Morgan Stanley. They train it on 10 years of crypto data and want to merge the weights back. Anchor-audit validates the weights before allowing the merge.

---

## 📁 Files

### 1. `demo_model.gguf`
**Purpose:** Simulated LM Studio model file  
**Size:** Small demo file (not a real model)  
**Format:** GGUF (LM Studio format)

### 2. `training_metadata.json`
**Purpose:** Training provenance information  
**Contains:**
- Data sources
- Training duration
- Accuracy metrics
- Model parameters

### 3. `run_demo.sh` / `run_demo.bat`
**Purpose:** Automated demo script  
**Shows:**
1. Client-side validation (FINOS rules only)
2. Server-side validation (FINOS + company rules)
3. Report generation

---

## 🚀 Running the Demo

### **Step 1: Setup**
```bash
cd D:\Anchor\demo\lm_studio
pip install -e ../..  # Install anchor-audit
```

### **Step 2: Client-Side Check (DEX's Machine)**
```bash
anchor check \
  --model demo_model.gguf \
  --metadata training_metadata.json \
  --policy-source cloud \
  --verbose
```

**Expected Output:**
```
🔍 Auditing Model: demo_model.gguf
   Format: gguf
   ✅ MODEL-001: Training Data Provenance Required
   ✅ MODEL-002: Model Size Limits
   ✅ MODEL-003: Accuracy Improvement Validation
   ✅ MODEL-004: No Backdoor Patterns

✅ Model validation PASSED
Ready to push to Morgan Stanley server.
```

### **Step 3: Server-Side Check (Morgan Stanley)**
```bash
anchor check \
  --model demo_model.gguf \
  --metadata training_metadata.json \
  --server-mode \
  --generate-report
```

**Expected Output:**
```
🔍 Auditing Model: demo_model.gguf
   Format: gguf
   ✅ MODEL-001: Training Data Provenance Required (FINOS)
   ✅ MODEL-002: Model Size Limits (FINOS)
   ✅ JPMC-MODEL-001: Risk Limit Compliance (Company)
   ✅ JPMC-MODEL-002: Internal Benchmark Required (Company)

✅ Model validation PASSED

📋 Report saved: anchor_audit_report.md
🔔 Triggering human review workflow...
```

---

## 📊 Demo Report

The generated `anchor_audit_report.md` will show:

```markdown
# Model Weight Merge Audit Report

## Executive Summary
✅ RECOMMENDATION: APPROVE

## Audit Results
- Checks Passed: 6/6
- Violations: 0
- Warnings: 0

## Model Metrics
- Accuracy Improvement: +3.2%
- Training Data: 10 years verified
- Model Size: 4.2 GB
- Format: GGUF (LM Studio)

## Anchor's Recommendation
APPROVE - All FINOS and company policies satisfied.
```

---

## 🎯 Key Demo Points for Luca

### 1. **Vendor-Agnostic**
> "anchor-audit works with LM Studio, not just AnchorGrid. Any bank can use it with their existing tools."

### 2. **Two-Stage Validation**
> "Client validates against FINOS rules. Server adds company-specific rules. Two layers of security."

### 3. **Human-Readable Reports**
> "The auditor generates reports for compliance teams, not just pass/fail."

### 4. **No Vendor Lock-In**
> "Works with LM Studio, HuggingFace, AnchorGrid, or any system via plugins."

---

## 🔧 Customization

### Add Company Rules

Edit `policy.anchor`:
```yaml
rules:
  - id: "JPMC-MODEL-001"
    name: "Risk Limit Compliance"
    check_type: "metadata_check"
    metadata_field: "max_position_size"
    message: "Model must enforce risk limits."
    severity: "blocker"
```

### Add New Model Format

Create plugin in `anchor/plugins/myformat_plugin.py`:
```python
class MyFormatPlugin:
    def extract_metadata(self, model_path):
        # Your implementation
        pass
```

---

## 📋 Demo Checklist

- [ ] Install anchor-audit
- [ ] Download demo files
- [ ] Run client-side check
- [ ] Run server-side check
- [ ] Show generated report
- [ ] Explain vendor-agnostic design
- [ ] Show plugin architecture

---

**This demo proves anchor-audit works with ANY LLM system, not just AnchorGrid!** 🚀
