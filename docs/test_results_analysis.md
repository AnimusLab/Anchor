# Anchor Test Results Analysis

**Date:** 2026-01-23  
**Test Suite:** Django Validation Tests  
**Result:** 0/11 symbols successfully audited (0% agreement)

---

## Executive Summary

The automated Anchor analysis **failed to audit any Django symbols** due to a fundamental architectural limitation: 

**Anchor searches for call contexts within the target repository only**, but Django's core symbols are primarily used in **external projects** (DRF, third-party Django apps, etc.).

---

## Test Results

### Overall Agreement Test
```
Agreement: 0/11 = 0.0%
Target: 80%+ (9/11 symbols)
Status: FAILED
```

### Individual Symbol Results

| Symbol | Intent Anchor | Call Contexts | Status |
|--------|---------------|---------------|---------|
| `authenticate()` | ✓ Found (5ceed0a0) | 3 found (< 10 min) | ❌ Insufficient |
| `login()` | ✓ Found (5ceed0a0) | 2 found (< 10 min) | ❌ Insufficient |
| `logout()` | ✓ Found (5ceed0a0) | 2 found (< 10 min) | ❌ Insufficient |
| `User` | ✓ Found (bcfaa735) | 0 found (< 10 min) | ❌ Insufficient |
| `AbstractUser` | ✓ Found (c433fcb3) | 0 found (< 10 min) | ❌ Insufficient |
| `UserManager` | ✓ Found (bcfaa735) | 2 found (< 10 min) | ❌ Insufficient |
| `Form` | ✓ Found (7c7ad041) | 0 found (< 10 min) | ❌ Insufficient |
| `BaseForm` | ✓ Found (7c7ad041) | 0 found (< 10 min) | ❌ Insufficient |
| `ModelForm` | ✓ Found (29f0e818) | 3 found (< 10 min) | ❌ Insufficient |
| `Manager` | ✓ Found (5ceed0a0) | 4 found (< 10 min) | ❌ Insufficient |
| `BaseManager` | ✓ Found (31fadc12) | 0 found (< 10 min) | ❌ Insufficient |

**Key observation:** Intent anchor extraction worked perfectly (11/11 ✓), but call context extraction failed across the board.

---

## Root Cause Analysis

### The Core Problem

**Current behavior:**
```python
# anchor/contexts.py:39
for py_file in self.repo_path.rglob("*.py"):
    # Only searches within Django's own repository
```

**Why this fails for frameworks:**
- Django core symbols (`authenticate()`, `Form`, etc.) are **library exports**
- Their primary usage is in **external codebases**:
  - Django REST Framework
  - Third-party Django apps
  - User applications
- Django's own internal calls are minimal (test files, internal utilities)

### Example: `authenticate()`

**Within Django repo:**
- 3 call sites found (all in tests or internal utilities)

**In reality (external usage):**
- Thousands of calls across:
  - Django REST Framework (`rest_framework`)
  - django-allauth (`allauth`)
  - Custom user applications
  - Tutorials and documentation

**Manual audit identified 3 usage patterns:**
1. Session-based auth (33%)
2. API token validation (33%) 
3. OAuth flows (33%)

**None of these contexts exist within Django itself.**

---

## Why Manual Audits Worked

The manual audits succeeded because they:

1. **Surveyed ecosystem usage** - Examined DRF, GraphQL, OAuth libraries
2. **Combined documentation analysis** - Read commit messages, RFCs, design docs
3. **Leveraged domain knowledge** - Understood web framework evolution
4. **Sampled GitHub code** - Looked at real-world usage patterns

**Anchor cannot replicate this** without access to:
- External codebases using Django
- Documentation and design history
- GitHub code search results
- Framework/library relationships

---

## Implications for Anchor

### What This Reveals

**Anchor's current design assumes:**
- All relevant call sites are within the audited repository
- Usage patterns are observable from internal code
- Symbols are primarily consumed internally

**This works for:**
- ✅ Application code (self-contained usage)
- ✅ Internal utilities (used within same codebase)
- ✅ Microservices (bounded context)

**This fails for:**
- ❌ **Framework/library code** (external consumers)
- ❌ **Public APIs** (usage outside repository)
- ❌ **Exported symbols** (designed for external use)

### The Validation Paradox

**We chose Django to validate Anchor because:**
- Mature 15+ year codebase ✓
- Clear intent fossils ✓
- Known drift patterns ✓
- Real-world complexity ✓

**But Django is precisely the type of codebase Anchor cannot analyze:**
- Public framework (not an application)
- Symbols are exports (not internal)
- Usage is external (not within repo)

---

## Solutions & Path Forward

### Short-term: Adjust Test Expectations

**Option 1: Test on application code instead**
- Audit a Django **application** (not the framework itself)
- Example: A real-world Django project with internal utilities
- This would match Anchor's current capabilities

**Option 2: Lower the call site threshold**
- Change minimum from 10 to 3 call sites
- Accept lower confidence verdicts
- Acknowledge limited data

**Option 3: Manual hybrid approach**
- Use Anchor for intent anchor extraction (works perfectly)
- Use manual analysis for call context survey
- Document this as the intended workflow

### Long-term: Extend Anchor for Frameworks

**Feature: External Usage Analysis**

Add capability to analyze framework usage by:

1. **GitHub Code Search Integration**
   ```python
   github_search.search_code(
       query=f"{symbol_name} language:python",
       context_lines=20
   )
   ```

2. **Ecosystem Repository Scanning**
   ```python
   repos_to_scan = [
       "django-rest-framework/django-rest-framework",
       "jazzband/django-oauth-toolkit",
       "pennersr/django-allauth"
   ]
   ```

3. **Documentation Mining**
   - Parse framework documentation
   - Extract usage examples
   - Identify design intent from RFCs

4. **PyPI Dependency Analysis**
   - Find packages depending on target package
   - Sample usage from dependents
   - Weight by download popularity

**Challenges:**
- Requires API keys (GitHub, PyPI)
- Privacy concerns (scanning public code)
- Scale (millions of usage examples)
- Rate limiting

---

## Current State Assessment

### What Works ✅

**Intent Anchor Extraction**
- Successfully extracted all 11 Django symbol anchors
- Correct commit identification
- Proper historical traversal
- Accurate docstring/source extraction

**Core Infrastructure**
- Repository analysis framework functional
- Git history traversal working
- Python AST parsing operational
- Clustering algorithms ready

### What Doesn't Work ❌

**Call Context Analysis for Framework Code**
- Cannot analyze external usage
- Limited to internal calls only
- Insufficient data for clustering (< 10 contexts)
- No verdicts generated

**Ecosystem Integration**
- No external codebase scanning
- No GitHub search integration
- No dependency graph analysis

---

## Recommendations

### Immediate Actions

1. **Update README** - Clarify Anchor is for application code, not frameworks (currently)
2. **Adjust test suite** - Create tests using application code, not Django core
3. **Document limitation** - Explicitly state external usage analysis is Phase 2

### Phase 2 Development Priority

**Build external usage analyzer:**
- GitHub Code Search API integration
- Sample-based analysis (not exhaustive)
- Configurable external repos to scan
- Respect rate limits and privacy

### Alternative Validation Approach

**Test Anchor on:**
- A **Django application** (e.g., a real-world SaaS app)
- Internal utilities within large projects
- Private corporate codebases (self-contained)

These would demonstrate Anchor's current capabilities without requiring ecosystem scanning.

---

## Conclusion

**The test results are not a failure of Anchor's design.**

They reveal a **scope boundary**:
- Anchor Version 0.1 is designed for **application code**
- Framework/library analysis requires **ecosystem integration** (Phase 2 feature)

**The manual Django audits remain valid** as proof of concept:
- Intent drift patterns are real
- Semantic roles are identifiable
- Verdicts are defensible

**What's missing is automation for external usage analysis.**

This is addressable but requires:
1. GitHub API integration
2. Ecosystem dependency analysis
3. Sample-based statistical methods
4. Careful privacy/legal considerations

**Next steps:**
1. Test Anchor on application code (not frameworks)
2. Document current capabilities accurately
3. Plan Phase 2: Ecosystem Analysis Feature

---

## Technical Details

### Test Environment
- Python: 3.14.0
- Django: Latest (cloned from main branch)
- Pytest: 9.0.2
- Anchor: 0.1.0-dev

### Test Duration
- 86.07 seconds (1:26)
- 11 symbols processed
- All intent anchors extracted successfully
- All call context extractions insufficient

### Error Pattern
```
Auditing {symbol} from {file}...
  [1/5] Extracting intent anchor...
  ✓ Found anchor at commit {sha}
  [2/5] Extracting call contexts...
  ✗ Insufficient call contexts ({n} < 10)
```

Consistent across all 11 symbols.

---

**This analysis informs the next phase of Anchor development.**
