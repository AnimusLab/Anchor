# Use Case: Governing Autonomous LLM Agents

Autonomous AI agents (built using frameworks like LangChain, Autogen, or CrewAI) are highly vulnerable to prompt injection, recursive execution loops, and tool overreach. This use case covers how Anchor intercepts and governs agent behaviors.

---

## 🛠️ Intercepting Tool Invocations

AI agents execute tools (like databases, shell execution wrappers, or web search APIs) dynamically based on LLM decisions.

```
AI Agent (LangChain / Autogen)
         ↓
Determines: Invoke database query tool
         ↓
Anchor Interceptor intercepts call
         ↓
Scans payload (SQL Injection / shell risk)
         ↓
Pass (Execute query) OR Fail (Raise AnchorViolationError)
```

### Preventing Tool Overreach (`AGT-001`)
*   **The Risk**: An agent receives a prompt injection instructing it to truncate database tables or delete configuration parameters. Because the agent has access to a database execution tool, it carries out the task.
*   **Anchor Solution**: Hooking directly into framework tool invokers (e.g. `langchain.BaseLanguageModel.invoke`), Anchor matches input arguments against static rulesets. If an unauthorized pattern is detected (like dropping tables in a query), the call is blocked, raising an `AnchorViolationError` to contain the action.

---

## 🔄 Containment: Execution Recursion Limits (`AGT-003`)

Agents often operate in loop-based environments, where Agent A prompts Agent B, which prompts Agent A.

*   **The Risk**: If the agents encounter an edge condition or parsing error, they may enter an infinite recursive loop, consuming thousands of dollars in LLM tokens and causing CPU denial-of-service.
*   **Anchor Solution**: The `SessionStats` tracker in `anchor.runtime.interceptors.base` monitors the iteration frequency of agent invocations within a single execution block. If the call loop exceeds configured thresholds, Anchor aborts the session, logging a loop recursion violation.

---

## 🔒 Prompt and Response Verification

Anchor shields agents using double-sided runtime scanning:

### Pre-execution (Outbound Prompt):
1.  **PII Sanitization**: Outbound prompt parameters are checked for raw emails, phone numbers, or credentials before hitting the model.
2.  **Jailbreak Defense**: Scans input texts for injection strings (such as `Developer Mode active`).

### Post-execution (Inbound Completion):
1.  **Code Sandboxing**: If the model outputs code (like Python or SQL) to be executed by an interpreter tool, Anchor intercepts the code block and routes it to the **Diamond Cage WASM container** for safety validation.
2.  **Secrets Interceptor**: Prevents the agent from returning internal API keys or credentials returned by tools to the end user.
