# Drift Pattern: Aligned

**Definition:** Current usage matches original intent. Single semantic role maintained. Evolution is appropriate without drift.

---

## Characteristics

### Primary Indicators

1. **Single semantic role**
   - All usage serves one coherent purpose
   - No distinct call context clusters
   - Consistent purpose across all call sites

2. **High intent alignment (>90%)**
   - 90%+ of usage matches original intent
   - Core features used as designed
   - Assumptions remain valid

3. **Clear, narrow purpose**
   - Symbol does one thing well
   - Scope is well-defined and bounded
   - Name accurately reflects behavior

4. **Appropriate evolution**
   - Changes enhance original purpose
   - No scope expansion beyond intent
   - Bug fixes, performance improvements, security patches

5. **Minimal but not absent evolution**
   - Not frozen (that would be inertia)
   - Not exploding (that would be overload)
   - Steady, purposeful refinement

---

## Detection Heuristics

### Quantitative Signals

```python
def is_aligned(symbol_analysis):
    roles = cluster_call_contexts(symbol_analysis.call_sites)
    
    # Single semantic role
    if len(roles) > 1:
        # Check if roles are actually variants of same purpose
        role_similarity = pairwise_similarity(roles)
        if any(sim < 0.8 for sim in role_similarity):
            return False  # Distinct roles, not aligned
    
    # High percentage matches intent
    intent_match_percentage = calculate_intent_match(
        symbol_analysis.call_sites,
        symbol_analysis.intent_anchor
    )
    
    if intent_match_percentage < 0.9:
        return False  # <90% alignment
    
    # Not frozen (some evolution)
    change_count = count_meaningful_changes(
        symbol_analysis.history,
        years=5
    )
    
    if change_count == 0:
        return False  # Might be dependency inertia
    
    # Evolution stayed in scope
    scope_violations = detect_scope_expansion(symbol_analysis)
    
    if scope_violations:
        return False  # Scope expanded beyond intent
    
    return True
```

### Qualitative Checks

**Ask these questions:**

1. Does all usage serve the same core purpose?
   - If yes → Aligned candidate

2. Do 90%+ of call sites match original intent?
   - If yes → Aligned candidate

3. Is the symbol's purpose immediately clear from its name?
   - If yes → Aligned candidate

4. Has evolution stayed within the original scope?
   - If yes → Aligned

5. Are there any workarounds or unused features?
   - If no → Aligned

---

## Django Examples

### Example 1: `login()`

**Anchored to:** Persist user identity in session (2012)

**Why aligned:**

**1. Single semantic role (100%)**
```python
# All usage is session creation
login(request, user)
# That's it. No other purposes.
```

**2. No alternative contexts**
- Traditional login: session creation ✓
- Admin login: session creation ✓
- Post-registration: session creation ✓
- User impersonation: session creation ✓

All contexts do the SAME thing.

**3. All features used**
```python
def login(request, user, backend=None):
    # Stores session keys
    request.session[SESSION_KEY] = user.id
    request.session[BACKEND_SESSION_KEY] = user.backend
    # Fires signal
    user_logged_in.send(...)
```

Every line serves the core purpose. No dead code.

**4. Appropriate evolution**
- Security improvements (session cycling)
- Signal additions (monitoring)
- Bug fixes

No scope expansion. Still just session creation.

---

### Example 2: `logout()`

**Anchored to:** Remove user identity and flush session (2012)

**Why aligned:**

**1. Single purpose: session destruction**
```python
def logout(request):
    request.session.flush()
    request.user = AnonymousUser()
    user_logged_out.send(...)
```

**2. 100% usage alignment**
- All call sites: destroy session
- No API logout (different mechanism)
- No token invalidation (separate concern)
- Pure session cleanup

**3. No drift over time**
- Original implementation: flush session
- Current implementation: flush session
- No expansion, no displacement

---

### Example 3: `AbstractUser`

**Anchored to:** Customizable base for user models (2012)

**Why aligned:**

**1. Intentional redesign (not drift)**
- Created specifically to address User limitations
- Designed from inception to be flexible
- Purpose: "Provide customizable base class"

**2. Used exactly as designed**
```python
class CustomUser(AbstractUser):
    email = EmailField(unique=True)
    USERNAME_FIELD = 'email'
    # Custom fields
```

**3. 100% usage matches intent**
- All usage: extend to create custom user models
- No misuse, no workarounds
- Design goal achieved

**Note:** AbstractUser is aligned because it was DESIGNED for flexibility. User drifted because it was NOT.

---

### Example 4: `UserManager`

**Anchored to:** Factory methods for user creation (2007)

**Why aligned:**

**1. Single purpose: user factory**
```python
class UserManager(Manager):
    def create_user(self, username, email, password=None):
        # Create user with hashed password
        ...
    
    def make_random_password(self, length=10):
        # Generate password
        ...
```

**2. Simple factory pattern**
- create_user(): main method
- make_random_password(): utility
- That's the entire API

**3. No expansion**
- Still just creates users
- No query methods (those are in Manager base)
- Focused responsibility

---

### Example 5: `BaseManager`

**Anchored to:** Manager with QuerySet method generation (2013)

**Why aligned:**

**1. Intentional refactor**
- Created to solve specific problem (from_queryset)
- Designed for dynamic method copying
- Clear architectural improvement

**2. Used exactly as intended**
```python
class CustomManager(BaseManager):
    @classmethod
    def from_queryset(cls, queryset_class):
        # Dynamic method generation
        ...
```

**3. Healthy evolution pattern**
- Not drift, intentional redesign
- Solves known problem
- Improves architecture

---

## When to Apply This Verdict

### Apply "Aligned" when:

✅ Single semantic role (or very similar variants)  
✅ 90%+ usage matches original intent  
✅ Clear, narrow purpose  
✅ Name accurately reflects behavior  
✅ Appropriate evolution within scope  
✅ No workarounds or unused features  
✅ No distinct call context clusters  

### Do NOT apply when:

❌ Multiple distinct semantic roles → "Semantic Overload"  
❌ Primary usage contradicts intent (>50%) → "Intent Violation"  
❌ Frozen for compatibility → "Dependency Inertia"  
❌ Significant unused features → Check other patterns  
❌ Workarounds prevalent → Check other patterns  

---

## Boundary Cases

### Case 1: Multiple Variants vs. Multiple Roles

**Question:** How do we distinguish variants from roles?

**Guideline:**
- Variants: Same core purpose, different contexts
- Roles: Different purposes, unrelated concerns

**Example - Variants (Aligned):**
```python
# login() used in different contexts but same purpose
login(request, user)  # Traditional
login(request, user)  # Admin
login(request, user)  # Post-registration
# All create sessions - ONE role
```

**Example - Roles (Overload):**
```python
# authenticate() serving different purposes
authenticate(username, password)  # Session auth
authenticate(token=token)         # API auth
authenticate(oauth_token=token)   # External auth
# Three distinct roles
```

### Case 2: Intentional Redesigns

**Question:** Is a redesigned symbol "aligned" to old or new intent?

**Guideline:**
- If redesign is explicit (marked, documented) → Aligned to NEW intent
- If redesign is implicit (silent) → Drift from OLD intent

**Example:**
- AbstractUser: Explicit redesign → Aligned to its own intent
- Form: Implicit expansion → Intent Violation from original

### Case 3: Minimal Evolution

**Question:** How much evolution is acceptable for "Aligned"?

**Guideline:**
- Evolution that enhances original purpose → Aligned
- Evolution that expands scope → Drift
- No evolution + alternatives exist → Inertia

**Example:**
- login() added signals, security improvements → Aligned
- authenticate() added OAuth support → Drift (new roles)
- User frozen, AbstractUser exists → Inertia

---

## Evidence Requirements

To support an "Aligned" verdict, collect:

### Required Evidence

1. **Single purpose demonstration**
   - Show all call sites serve same purpose
   - Cluster analysis showing one role
   - No distinct semantic clusters

2. **High alignment percentage**
   - 90%+ usage matches intent
   - Feature usage matches design
   - No significant unused features

3. **Original intent documentation**
   - Show current usage matches original
   - Demonstrate assumptions remain valid
   - No violated assumptions

4. **Evolution analysis**
   - Changes enhance original purpose
   - No scope expansion
   - Appropriate refinement

### Supporting Evidence

5. **Lack of workarounds**
   - No common hacks or extensions
   - Used as designed
   - No "better alternatives" needed

6. **Clear naming**
   - Name accurately reflects behavior
   - No conceptual mismatch
   - Immediately understandable

---

## Verdict Template

```markdown
✓ [symbol_name]

Anchored to:
  [original intent one-liner]

Current usage:
  - [Core purpose]: 100% of usage

Verdict:
  Aligned

Rationale:
  [Symbol] performs [original intent] across all observed usage contexts.
  The implementation, naming, and behavior match the original design.
  Evolution has stayed within scope, enhancing [original purpose] without
  expansion. No drift detected.

Evidence:
  - Single semantic role
  - 90%+ usage matches intent
  - All features used as designed
  - No workarounds or alternatives needed
  - Appropriate evolution: [list improvements]
```

---

## Comparison to Other Patterns

| Aspect | Aligned | Semantic Overload | Intent Violation | Dependency Inertia |
|--------|---------|-------------------|------------------|-------------------|
| Semantic roles | 1 | 2-4 | 1-2 (shifted) | 1 (frozen) |
| Intent match | >90% | Partial (per role) | <50% primary | 100% (outdated) |
| Evolution | Appropriate | Expanded | Displaced | Frozen |
| Workarounds | None | Rare | Medium | Very common |
| Key signal | Consistency | Multiplicity | Displacement | Stagnation |

---

## Automation Strategy

### Step 1: Check Role Count
```python
roles = cluster_call_contexts(symbol.call_sites)

if len(roles) > 1:
    # Multiple roles - check if they're variants or distinct
    similarity = pairwise_similarity(roles)
    if all(sim > 0.8 for sim in similarity):
        # Variants of same role
        roles = [merge_roles(roles)]
    else:
        return "not_aligned"  # Distinct roles
```

### Step 2: Measure Intent Alignment
```python
matches = 0
for call_site in symbol.call_sites:
    intent_similarity = semantic_similarity(
        call_site.context,
        symbol.intent_anchor.description
    )
    if intent_similarity > 0.7:
        matches += 1

alignment_percentage = matches / len(symbol.call_sites)

if alignment_percentage < 0.9:
    return "not_aligned"
```

### Step 3: Check Evolution Pattern
```python
changes = get_meaningful_changes(symbol.history, years=5)

for change in changes:
    if expands_scope(change, symbol.intent_anchor):
        return "not_aligned"  # Scope expansion detected

if len(changes) == 0 and has_alternatives(symbol):
    return "dependency_inertia"  # Frozen with alternatives
```

### Step 4: Verify No Workarounds
```python
workarounds = detect_workaround_patterns(symbol.usages)

if len(workarounds) > 0:
    return "not_aligned"  # Workarounds suggest insufficiency

return "aligned"  # All checks passed
```

---

## What Makes Symbols Drift-Resistant

Aligned symbols share common characteristics:

### Design Factors

1. **Narrow scope**
   - Does one thing
   - Clear boundaries
   - No temptation to expand

2. **Clear naming**
   - Purpose obvious from name
   - No ambiguity
   - Matches behavior exactly

3. **Stable requirements**
   - Problem space hasn't changed
   - Original design still appropriate
   - No new paradigms

4. **Single responsibility**
   - One reason to change
   - One concern
   - Easy to understand

### Examples

- `login()`: Narrow (session creation), clear name, stable requirement
- `logout()`: Narrow (session cleanup), clear name, stable requirement
- `UserManager`: Narrow (user factory), clear purpose, stable pattern

### Contrast with Drift-Prone Symbols

- `authenticate()`: Flexible design enabled multiple paradigms
- `Form`: Broad "form" concept covers HTML and validation
- `Manager`: Comprehensive interface grew complex
- `User`: Rigid design couldn't adapt, became inertia

**Key insight:** Flexibility and breadth enable drift. Narrowness prevents it.

---

## The Value of Aligned Verdicts

### Why Control Cases Matter

1. **Proves Anchor can distinguish**
   - Not everything is drifted
   - Tool isn't just crying wolf
   - Credibility through accuracy

2. **Provides positive examples**
   - Shows what "correct" looks like
   - Design patterns to emulate
   - Aspirational targets

3. **Reduces alert fatigue**
   - Only problematic symbols flagged
   - Aligned symbols pass quietly
   - Focus energy on actual issues

4. **Validates detection logic**
   - If all symbols flagged as drift, logic is wrong
   - Balance of aligned/drifted symbols is healthy

### In Practice

**45% of audited Django symbols were Aligned.**

This shows:
- Django is generally well-designed
- Drift is real but not universal
- Anchor's verdicts are balanced
- Tool has credibility

---

## Common Mistakes

### Mistake 1: Assuming Simplicity = Aligned

❌ "This function is 10 lines, must be aligned"  
✅ "This function does one thing consistently"

**Length doesn't determine alignment. Purpose consistency does.**

### Mistake 2: Ignoring Evolution

❌ "Hasn't changed in 5 years, must be aligned"  
✅ "Evolution enhanced original purpose appropriately"

**Lack of change might be inertia, not alignment.**

### Mistake 3: Accepting Feature Creep

❌ "Added OAuth support, still aligned to authentication"  
✅ "OAuth is a distinct auth paradigm, not just an enhancement"

**Scope expansion is drift, even if related to core domain.**

---

## Recommended Actions (When Aligned Detected)

This is the easy one:

1. **Leave it alone** ✅
   - It's working correctly
   - Intent is maintained
   - No drift detected

2. **Use as example**
   - Document why it's well-designed
   - Reference in architecture reviews
   - Model new code after it

3. **Protect from drift**
   - Monitor for scope expansion
   - Resist feature additions
   - Keep it narrow and focused

4. **Celebrate**
   - Acknowledge good design
   - Recognize maintainers
   - This is what success looks like

**Aligned symbols are the goal. Don't fix what isn't broken.**

---

## References

- **Django `login()` audit** - Primary example
- **Django `logout()` audit** - Control case
- **Django `AbstractUser` audit** - Intentional redesign example
- **Philosophy.md** - Core principles
- **Complete Findings Report** - Full context

---

**Key Takeaway:**

Aligned = Current usage matches original intent, single purpose maintained, appropriate evolution.

It's the "everything is fine problem" - which isn't a problem at all.

**Identifying aligned symbols proves:**
- Anchor isn't biased toward finding problems
- Good design exists and can be measured
- The tool has credibility

**45% aligned rate in Django shows balanced, fair detection.**