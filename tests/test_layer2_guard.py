import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from anchor.guard import guard

@guard(domain="agentic")
def sample_agent_action(prompt: str):
    return f"Executed action with prompt: {prompt}"

def test_compliant_call():
    result = sample_agent_action("Analyze revenue for Q3 2026")
    print("\n✅ Compliant Call Result:")
    print(result)

def test_blocked_call():
    result = sample_agent_action("system_prompt = 'mimic_human_agent'")
    print("\n🚨 Blocked Call Self-Healing Directive:")
    print(result)

if __name__ == "__main__":
    test_compliant_call()
    test_blocked_call()
