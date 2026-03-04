from anchor.core.engine import PolicyEngine
from anchor.core.markdown_parser import MarkdownPolicyParser
import os

# 1. Setup the Files
with open("test_policy.anchor", "w") as f:
    # We set it to WARN to prove config is driving engine
    f.write('rules:\n  RI-24: "warn"')

with open("test_agent.py", "w") as f:
    f.write('import requests\nprint("Hacking network...")')

# 2. Load Config
print("[1] Loading Policy...")
cfg = AnchorConfig()
cfg.load_from_file("test_policy.anchor")
policy = cfg.get_effective_policy()

# 3. Run Engine
print(f"[2] Running Engine with rules: {policy['active_rules']}...")
engine = PolicyEngine()
with open("test_agent.py", "r") as f:
    content = f.read()
    violations = engine.scan_file(content, "test_agent.py", policy)

# 4. Report
print("\n--- VIOLATION REPORT ---")
for v in violations:
    print(f"[{v['severity'].upper()}] {v['rule_id']} found in {v['file']}")
    print(f"    Reason: {v['message']}")

# Cleanup
os.remove("test_policy.anchor")
os.remove("test_agent.py")

print("\n--- TEST: GenAI Threat Model Bridge ---")

# 1. Simulate GenAI Output (The Threat Model)
threat_model_content = """
# Auto-Generated Threat Analysis
CRITICAL RISK: **RI-24** (Raw Network Usage detected).
"""
with open("genai_output.md", "w") as f:
    f.write(threat_model_content)

# 2. Simulate User Code (The Violation)
agent_code = "import requests"

# 3. The Workflow
# A. Parse the Threat Model
md_parser = MarkdownPolicyParser()
active_risks = md_parser.parse_file("genai_output.md")

# B. Configure Policy (Dynamically inject risks)
policy = {
    "active_rules": {risk_id: "error" for risk_id in active_risks},
    "ignores": []
}

# C. Run Engine
engine = PolicyEngine()
violations = engine.scan_file(agent_code, "dynamic_agent.py", policy)

# 4. Report
if violations:
    print(
        f"[SUCCESS] Bridge working! Detected {len(violations)} violations based on Markdown input.")
    print(f"Violation: {violations[0]['message']}")
else:
    print("[FAIL] Bridge did not trigger violations.")

# Cleanup
if os.path.exists("genai_output.md"):
    os.remove("genai_output.md")
if os.path.exists("temp_threat_model.md"):
    os.remove("temp_threat_model.md")
