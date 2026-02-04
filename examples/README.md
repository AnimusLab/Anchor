# Anchor-Audit Demo Examples

This directory contains demonstration files for the FINOS GSoC 2026 presentation.

---

## 📁 Files

### `threat_model.md`
**Purpose:** Simulates a GenAI-generated threat model (e.g., from Claude, GPT-4)  
**Contains:** Risk IDs (RI-24, AI-20, RI-12) identified for a trading agent

### `bad_agent.py`
**Purpose:** Demonstrates INSECURE code patterns  
**Violations:**
- RI-24: Uses `import requests` (raw network access)
- AI-20: Uses `exec()` on LLM output
- RI-12: Uses `threading.Thread` directly

### `good_agent.py`
**Purpose:** Demonstrates SECURE, FINOS-compliant patterns  
**Mitigations:**
- RI-24: Uses MCP Client with certificates
- AI-20: Uses AST validation instead of exec
- RI-12: Uses managed TaskQueue

---

## 🚀 Demo Script for Luca Borella

### Step 1: Show the Threat Model
```bash
cat examples/threat_model.md
```

**Talking Point:** "This is what an LLM generates when analyzing agent security. Notice the Risk IDs: RI-24, AI-20, RI-12."

---

### Step 2: Show the Insecure Code
```bash
cat examples/bad_agent.py
```

**Talking Point:** "This trading agent violates all three risks. Let's see anchor-audit block it."

---

### Step 3: Run Enforcement (The "Wow" Moment)
```bash
anchor check --context examples/threat_model.md --dir examples/ --verbose
```

**Expected Output:**
```
🤖 [BRIDGE] Parsing GenAI Threat Model: examples/threat_model.md
   Detected Risks: RI-24, AI-20, RI-12
   ✅ Activated 3 dynamic enforcement rules

📜 Loading Federation: ['finos-master.anchor', 'policy.anchor', '/tmp/xyz.anchor']
🚀 Scanning 'examples/' with 5 active laws...

🚫 FAILED: Found 3 violations.
   [RI-24] Risk RI-24: Raw network access forbidden. Use MCP Client.
      File: examples/bad_agent.py:15
   [AI-20] Risk AI-20: Dynamic code execution from LLM output is forbidden.
      File: examples/bad_agent.py:28
   [RI-12] Risk RI-12: Direct threading is forbidden. Use managed task queue.
      File: examples/bad_agent.py:37
```

**Talking Point:** "The LLM identified risks in Markdown. Anchor turned them into hard build failures. This is the bridge FINOS Issue #203 needs."

---

### Step 4: Show the Compliant Code
```bash
cat examples/good_agent.py
```

**Talking Point:** "Here's the same agent, rewritten with approved patterns. Let's verify it passes."

---

### Step 5: Verify Compliance
```bash
anchor check --context examples/threat_model.md --dir examples/good_agent.py
```

**Expected Output:**
```
🤖 [BRIDGE] Parsing GenAI Threat Model: examples/threat_model.md
   Detected Risks: RI-24, AI-20, RI-12
   ✅ Activated 3 dynamic enforcement rules

🚀 Scanning 'examples/good_agent.py' with 5 active laws...

✅ PASSED: Compliance Verified.
```

**Talking Point:** "Same threat model, compliant code. This is how we enforce AI governance at scale."

---

## 🎯 Key Messages for FINOS

1. **The Problem:** LLMs identify risks, but can't enforce them
2. **The Solution:** Anchor bridges GenAI analysis → CI/CD blocking
3. **The Innovation:** Dynamic policy generation from Markdown
4. **The Impact:** Banks can enforce FINOS standards automatically

---

## 📋 Next Steps After Demo

1. **Integrate Full FINOS Risk Catalog:** Replace placeholder risks with official taxonomy
2. **Add More Languages:** Extend beyond Python (JavaScript, Go, Rust)
3. **Build Runtime Layer:** AnchorGrid for P2P agent governance
4. **Deploy to FINOS:** Make this the reference implementation for Issue #203

---

**Questions?** Contact: tanishqdasari2004@gmail.com
