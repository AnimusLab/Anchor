# Anchor Usage Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/anchor.git
cd anchor

# Install dependencies
pip install -r requirements.txt

# Install Anchor
pip install -e .

# Verify installation
anchor validate
```

---

## Quick Start

### Audit a Single Symbol

```bash
anchor audit django/contrib/auth/__init__.py::authenticate
```

**Output:**
```
⚠ authenticate

Anchored to:
  If the given credentials are valid, return a User object.
  (commit 7cc4068c, 2012-10-01)

Current roles:
  - Role in django.contrib.auth (33%)
  - Role in rest_framework (33%)
  - Role in allauth (33%)

Verdict: semantic_overload
Confidence: high

Rationale:
  authenticate now serves 3 distinct roles: django.contrib.auth,
  rest_framework, allauth. While each role relates to the original
  domain, their coexistence within a single abstraction exceeds
  the responsibility implied by the original design.
```

---

## Command Reference

### `anchor audit`

Audit a single symbol for intent drift.

**Syntax:**
```bash
anchor audit FILE_PATH::SYMBOL_NAME [OPTIONS]
```

**Options:**
- `--repo PATH` - Repository path (default: current directory)
- `--type TYPE` - Symbol type: `function` or `class` (default: function)

**Examples:**
```bash
# Audit a function
anchor audit myapp/views.py::process_user

# Audit a class
anchor audit myapp/models.py::User --type class

# Audit in different repository
anchor audit django/forms/forms.py::Form --repo ~/django
```

---

### `anchor batch`

Audit multiple symbols from a file.

**Syntax:**
```bash
anchor batch SYMBOLS_FILE [OPTIONS]
```

**File format:**
```
# symbols.txt
django/contrib/auth/__init__.py::authenticate
django/contrib/auth/__init__.py::login
django/forms/forms.py::Form
django/db/models/manager.py::Manager
```

**Example:**
```bash
anchor batch symbols.txt --repo ~/django
```

---

### `anchor validate`

Validate Anchor installation.

**Syntax:**
```bash
anchor validate [OPTIONS]
```

**Example:**
```bash
anchor validate --repo ~/django
```

---

## Python API

### Basic Usage

```python
from anchor import RepositoryAnalyzer

# Initialize analyzer
analyzer = RepositoryAnalyzer('/path/to/repo')

# Audit a symbol
result = analyzer.audit_symbol(
    'django/contrib/auth/__init__.py',
    'authenticate'
)

# Check verdict
print(result.verdict)  # semantic_overload
print(result.confidence)  # high

# Access details
print(f"Roles: {len(result.roles)}")
print(f"Intent alignment: {result.metrics.intent_alignment_percentage:.1%}")
```

---

### Advanced Usage

```python
from anchor import (
    RepositoryAnalyzer,
    ReportFormatter,
    DriftDetector
)

# Initialize components
analyzer = RepositoryAnalyzer('/path/to/repo')
formatter = ReportFormatter()

# Audit symbol
result = analyzer.audit_symbol('path/to/file.py', 'function_name')

# Generate report
if result:
    report = formatter.format(result)
    print(report)
    
    # Access metrics
    print(f"Role count: {result.metrics.role_count}")
    print(f"Changes (5y): {result.metrics.changes_in_5_years}")
    print(f"Violated assumptions: {result.metrics.violated_assumptions_count}")
    
    # Access roles
    for role in result.roles:
        print(f"Role: {role.description} ({role.percentage:.1%})")
```

---

### Batch Processing

```python
from anchor import RepositoryAnalyzer, ReportFormatter

analyzer = RepositoryAnalyzer('/path/to/repo')
formatter = ReportFormatter()

symbols = [
    ('auth/__init__.py', 'authenticate'),
    ('auth/__init__.py', 'login'),
    ('forms/forms.py', 'Form'),
]

results = []
for file_path, symbol_name in symbols:
    result = analyzer.audit_symbol(file_path, symbol_name)
    if result:
        results.append(result)

# Generate summary
summary = formatter.format_summary(results)
print(summary)
```

---

## Understanding Verdicts

### ✓ aligned

**Meaning:** Current usage matches original intent

**Characteristics:**
- Single semantic role
- 90%+ usage aligns with original intent
- No violated assumptions
- Appropriate evolution

**Example:** `login()` - Session creation only, exactly as designed

---

### ⚠ semantic_overload

**Meaning:** Multiple distinct roles coexist

**Characteristics:**
- 2+ semantic roles
- No single role dominates (≤60%)
- Original intent still present (>20%)
- Roles could be separate abstractions

**Example:** `authenticate()` - Session auth + API tokens + OAuth

**What to do:**
- Acknowledge the overload
- Consider splitting into focused functions
- Document each role clearly

---

### ⚠ intent_violation

**Meaning:** Primary usage displaces original intent

**Characteristics:**
- Primary role >50% differs from original
- Original role now minority (<50%)
- Original features unused
- Name/structure implies original intent

**Example:** `Form` - Designed for HTML, now 70% API validation

**What to do:**
- Explicit redefinition with `@intent:` marker
- Separate abstraction for new use case
- Rename to match reality

---

### ⚠ dependency_inertia

**Meaning:** Frozen by compatibility despite known limitations

**Characteristics:**
- Structurally unchanged 5+ years
- Documented alternatives exist
- 40%+ usage involves workarounds
- High dependent count (>1000)

**Example:** `User` - Limited model, AbstractUser exists, persists for compatibility

**What to do:**
- Guide new projects to alternatives
- Document limitations
- Plan migration for major version

---

## Interpreting Metrics

### Role Metrics

```python
result.metrics.role_count  # Number of semantic roles
result.metrics.max_role_percentage  # Primary role percentage
result.metrics.pairwise_role_similarity  # How distinct are roles?
```

### Intent Alignment

```python
result.metrics.intent_alignment_percentage  # Overall alignment
result.metrics.original_intent_role_percentage  # Original role %
result.metrics.primary_role_is_original  # True if primary = original
```

### Evolution

```python
result.metrics.changes_in_5_years  # Meaningful changes
result.metrics.violated_assumptions_count  # Design violations
result.metrics.git_history_depth  # Total commits
```

### Confidence Factors

```python
result.confidence  # high | medium | low
result.metrics.call_site_count  # Number of samples
result.metrics.clustering_quality  # Role separation quality
```

---

## Testing Against Django

```bash
# Clone Django
git clone https://github.com/django/django.git ~/django

# Run validation tests
pytest tests/test_django_validation.py -v

# Expected: 80%+ agreement (9/11 or better)
```

**Manual audit comparison:**
- ✓ `login()` → aligned
- ⚠ `authenticate()` → semantic_overload
- ⚠ `Form` → intent_violation
- ⚠ `User` → dependency_inertia
- ... (11 total symbols)

---

## Troubleshooting

### "Could not find intent anchor"

**Cause:** Symbol not found in git history or shallow history

**Solutions:**
- Ensure symbol exists in specified file
- Check git history depth: `git log --oneline path/to/file.py | wc -l`
- Unshallow repository: `git fetch --unshallow`

---

### "Insufficient call contexts"

**Cause:** Fewer than 20 call sites found

**Solutions:**
- Symbol may be internal/private
- Repository might be too small
- Symbol name might be too common (e.g., `get`)

---

### Low clustering quality

**Cause:** Call contexts don't cluster well

**Solutions:**
- This is normal for truly aligned symbols (only 1 role)
- For multi-role symbols, check if contexts are too similar
- May indicate borderline case

---

## Performance Optimization

### Caching Embeddings

```python
# Embeddings are expensive - cache them
from anchor.contexts import RoleClusterer

clusterer = RoleClusterer()
# Model loads once, reused for all calls
```

### Limiting Call Sites

```python
# Extract fewer contexts for faster analysis
contexts = extractor.extract_call_contexts(
    symbol_name,
    max_contexts=50  # Default: 100
)
```

### Batch Processing

```python
# Reuse analyzer instance
analyzer = RepositoryAnalyzer(repo_path)

for symbol in symbols:
    result = analyzer.audit_symbol(...)
    # History analyzer is reused
```

---

## Next Steps

1. **Audit your codebase:** Start with core abstractions
2. **Compare to manual analysis:** Validate automated verdicts
3. **Tune thresholds:** Adjust in `docs/internal/invariants.md`
4. **Integrate with CI:** Add as non-blocking check
5. **Track over time:** Monitor drift accumulation

---

## Support

- **Issues:** https://github.com/yourusername/anchor/issues
- **Discussions:** https://github.com/yourusername/anchor/discussions
- **Docs:** See `docs/` directory

---

## Philosophy

> "The code still works. Tests still pass. But meaning erodes."

Anchor makes that erosion visible.

See `philosophy.md` for full design principles.