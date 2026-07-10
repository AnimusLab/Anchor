# Mitigation-Aware Rule Evaluation

Anchor's rule engine supports evaluating mitigation status before generating findings. This enables rules to define a required number of mitigations that must be satisfied in the implementation.

Mitigation requirements are declared at the rule level:
```yaml
rules:
  - id: "SEC-007"
    name: "Shell Command Execution"
    min_mitigations: 1
```

## Declaring Mitigations in Source Code

Developers can declare implemented mitigations using inline comments matching one of the following formats:
* `# anchor: mitigate <id>`
* `# anchor: mitigation <id>`
* `# anchor: mitigated <id>`

Where `<id>` is the rule ID (e.g. `SEC-007`) or the mitigation ID (e.g. `MIT-014-A`).

### Example

```python
import subprocess

# anchor: mitigate SEC-007
def run_command(args):
    # This call is safe because args are not shell-evaluated
    subprocess.run(args, shell=False)
```

## Engine Evaluation Flow

```
Evidence Collection (Pattern Matches)
         ↓
Parse inline mitigations in target file
         ↓
Verify if count of mitigations for rule ID meets min_mitigations
         ↓
         ├─ [YES] ── Discard Candidate (Compliant)
         └─ [NO]  ── Generate Violation (Non-Compliant)
```
