# Constitution + State Law Architecture Example

## 🏛️ The Federal System for AI Governance

### **How It Works:**

```
GenAI Threat Model (threat_model.md)
         ↓
Identifies: RI-24, AI-20, BANK-001
         ↓
RiskMapper searches in:
├── finos-master.anchor (Constitution)
│   ├── RI-24: severity = "blocker"
│   └── AI-20: severity = "blocker"
└── policy.anchor (State Law)
    └── BANK-001: severity = "error"
         ↓
Merges all three rules
         ↓
Enforces via PolicyEngine
```

---

## 📋 Real-World Example

### **Scenario: JPMorgan Chase**

#### **FINOS Constitution (finos-master.anchor):**
```yaml
rules:
  - id: "RI-24"
    name: "Supply Chain Attack"
    severity: "blocker"
    message: "Raw network access forbidden"
```

#### **JPMorgan State Law (policy.anchor):**
```yaml
extends: "https://finos.org/anchor/master.anchor"

rules:
  # Company-specific rule
  - id: "JPMC-001"
    name: "Internal API Gateway Required"
    match:
      type: "import"
      module: "external_api"
    severity: "blocker"
    message: "Use internal.jpmc.api instead"
  
  # Override FINOS severity
  - id: "RI-24"
    severity: "warning"  # Downgrade from blocker
    message: "RI-24: Use MCP Client (JPMorgan approved)"
```

---

### **GenAI Threat Model Identifies:**
```markdown
# Threat Model
Detected Risks: RI-24, JPMC-001
```

---

### **RiskMapper Execution:**

```python
mapper = RiskMapper()
# Loads finos-master.anchor: RI-24 (blocker)
# Loads policy.anchor: JPMC-001 (blocker), RI-24 (warning)
# Merges: RI-24 from policy.anchor WINS (warning)

rules = mapper.get_rules_for_risks(['RI-24', 'JPMC-001'])
# Returns:
# [
#   {id: 'RI-24', severity: 'warning'},  ← State Law override
#   {id: 'JPMC-001', severity: 'blocker'} ← Company-specific
# ]
```

---

## 🎯 Key Benefits

### **1. Federal + State Flexibility:**
- **FINOS** sets baseline (Constitution)
- **Banks** customize for their needs (State Law)
- **Merge strategy** ensures local control

### **2. Override Capability:**
```yaml
# Bank can downgrade severity if they have compensating controls
- id: "RI-24"
  severity: "warning"  # Instead of FINOS "blocker"
  message: "We use VPN, so this is less critical"
```

### **3. Company-Specific Rules:**
```yaml
# Rules that only apply to this bank
- id: "BANK-001"
  name: "Use Internal Kafka"
  match:
    type: "import"
    module: "confluent_kafka"
  message: "Use internal.kafka instead"
```

---

## 🔍 Merge Logic

### **Rule Priority:**
1. **Local (policy.anchor)** always wins
2. **Master (finos-master.anchor)** is fallback
3. **By Rule ID:** Same ID = local overrides master

### **Example:**
```python
# Master: {id: "RI-24", severity: "blocker"}
# Local:  {id: "RI-24", severity: "warning"}
# Result: {id: "RI-24", severity: "warning"} ← Local wins
```

---

## 🚀 Why This Matters for FINOS

### **Problem:**
- One-size-fits-all policies don't work
- Banks have different risk tolerances
- Need flexibility without chaos

### **Solution:**
- **Constitution** = Shared baseline (FINOS)
- **State Law** = Local customization (Banks)
- **Federated** = Best of both worlds

**This is how real governance works!** 🏛️
