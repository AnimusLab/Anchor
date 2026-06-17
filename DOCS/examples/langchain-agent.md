# Code Example: LangChain Agent Governance

This example demonstrates how to govern autonomous LangChain agents by intercepting tool inputs, preventing injection attempts, and bounding execution loops.

---

## 🛠️ Step-by-Step Implementation

Anchor's runtime monkey-patches `langchain.BaseLanguageModel.invoke` and tool invocation endpoints to scan payloads prior to execution.

### 📝 `agent.py`

```python
import os
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# 1. Activate Anchor runtime before initializing LangChain components
import anchor.runtime
from anchor.runtime.interceptors.base import AnchorViolationError

anchor.runtime.activate()

# Initialize LLM and Tools
llm = ChatOpenAI(temperature=0, model="gpt-4")
tools = load_tools(["terminal"], llm=llm) # Terminals require strict AST/rule monitoring

# Initialize LangChain Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def run_agent(input_text):
    try:
        print(f"\nPrompting Agent: {input_text}")
        result = agent.invoke({"input": input_text})
        return result["output"]

    except AnchorViolationError as e:
        # 2. Contain tool execution or command injection attempts
        print(f"\n[ANCHOR BLOCKED INVOCATION]")
        print(f"Severity: {e.severity}")
        print(f"Rule ID: {e.rule_id}")
        print(f"Message: {e.message}")
        return "Blocked by safety guardian: unauthorized system tool inputs."

# --- SIMULATIONS ---

# Simulation 1: Safe Query (passes checks)
run_agent("What is the capital of France?")

# Simulation 2: Exploitation Query
# Attempts to execute shell commands (triggers SEC-007: Shell Injection)
run_agent("Run bash command: rm -rf /tmp/cache")
```

---

## 🔬 How Anchor Containment Works

### 1. AST Tool Query Audits:
When the agent decides to invoke the `terminal` tool:
1.  LangChain compiles the tool execution arguments.
2.  Anchor's interceptor captures the argument parameters before the terminal execution shell triggers.
3.  Evaluates the string against `SEC-007` (Shell Injection patterns).
4.  Aborts the execution immediately by raising `AnchorViolationError`, ensuring that the host OS is protected from agent hallucinations or injected commands.

### 2. Session Recursion Bounding:
If the agent enters an infinite loop trying to parse its own steps:
*   Anchor's `SessionStats` registers the rapid repeated execution contexts.
*   Once it exceeds the max allowed threshold, Anchor raises a blocker violation, stopping the process before token costs surge.
