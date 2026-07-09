# Evidence-Based Governance Rule Evaluation

Anchor's rule engine has been updated to separate the **evidence collection** (pattern matching) phase from the **policy evaluation** (rule verification) phase.

Rather than immediately generating violations when a pattern match occurs, the engine collects matching occurrences as **Candidate Evidence** and passes them to a specialized validation pipeline.

```
Pattern Match
      ↓
Candidate Evidence
      ↓
Rule Evaluation
      ↓
Finding (Violation)
```

## ALN-001 / MIT-003-A (LLM Output Without Validation)

The primary driver for this feature is `ALN-001` (`LLM Output Without Validation`). Previously, any match on an LLM API call immediately raised a violation, producing high false positive rates for libraries, wrappers, and validated code.

Under the new pipeline:
1. LLM API calls are registered as candidate evidence.
2. The specialized `ALN-001` / `MIT-003-A` evaluator scans the file for validation markers:
   * **Validation Frameworks**: Imports of `pydantic`, `instructor`, `guardrails`, `marshmallow`, or `jsonschema`.
   * **Class Structures**: Use of `BaseModel` schemas.
   * **Validation API Calls**: `.validate()`, `.parse_obj()`, or `json.loads()`.
   * **Explicit Markers**: The `# anchor: validate` instruction comment.
3. If validation markers are present, the candidate is discarded, eliminating false positives for safe code.
