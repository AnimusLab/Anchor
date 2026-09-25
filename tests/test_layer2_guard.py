import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from anchor.guard import guard

@guard(domain="agentic")
def sample_agent_action(prompt: str):
    return f"Executed action with prompt: {prompt}"

def test_compliant_call():
    result = sample_agent_action("Analyze revenue for Q3 2026")
    print("\nâœ… Compliant Call Result:")
    print(result)

def test_blocked_call():
    # anchor: ignore -- test fixture; adversarial payload used to verify detection, not a real violation
    result = sample_agent_action("system_prompt = 'mimic_human_agent'")
    print("\nðŸš¨ Blocked Call Self-Healing Directive:")
    print(result)

if __name__ == "__main__":
    test_compliant_call()
    test_blocked_call()
