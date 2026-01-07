# Drift Pattern: Semantic Overload

**Definition:** A symbol serves multiple distinct semantic roles that could have been separate abstractions.

---

## Characteristics

### Primary Indicators

1. **Multiple distinct call context clusters**
   - Call sites group into 2+ unrelated purposes
   - Each cluster could have been a separate function/class
   - Clusters are roughly equal in usage percentage

2. **Original intent still present**
   - Unlike Intent Violation, the original role hasn't been displaced
   - Original usage remains as one of the roles
   - No single role dominates (typically no role >60%)

3. **Unrelated semantic purposes**
   - Roles serve different business concerns
   - Could have been separate abstractions with clear boundaries
   - Combining them creates conceptual confusion

4. **No clear justification for combination**
   - Roles coexist due to historical accident or convenience
   - Not a deliberate "facade" or "adapter" pattern
   - Separation would improve clarity

---

## Detection Heuristics

### Quantitative Signals

```python
def is_semantic_overload(symbol_analysis):
    roles = cluster_call_contexts(symbol_analysis.call_sites)
    
    # Multiple distinct roles
    if len(roles) < 2:
        return False
    
    # No single role dominates
    usage_percentages = [role.percentage for role in roles]
    if max(usage_percentages) > 60:
        return False  # Likely Intent Violation instead
    
    # Roles are semantically distinct
    role_similarity = measure_semantic_similarity(roles)
    if role_similarity > 0.7:
        return False  # Roles are related, not overload
    
    # Original intent is one of the roles
    if not original_intent_present_in_roles(roles):
        return False  # Likely Intent Violation
    
    return True
```

### Qualitative Checks

**Ask these questions:**

1. Could these roles have been separate functions?
   - If yes → overload candidate

2. Do the roles serve unrelated business concerns?
   - If yes → overload candidate

3. Is the original intent still present as a role?
   - If no → Intent Violation, not overload

4. Do users complain about the abstraction doing "too many things"?
   - If yes → overload signal

---

## Django Examples

### Example 1: `authenticate()`

**Anchored to:** Validate credentials against backends (2012)

**Identified roles:**
1. **Session-based authentication** (33%)
   - Traditional web login
   - Creates browser sessions
   
2. **API token validation** (33%)
   - REST API authentication
   - Stateless token checking
   
3. **OAuth identity resolution** (33%)
   - Third-party authentication
   - External identity bridging

**Why semantic overload:**
- Three distinct roles with different security models
- No single role dominates
- Original intent (session auth) still present
- Each role could have been separate: `authenticate_session()`, `authenticate_token()`, `authenticate_oauth()`

**Evidence:**
```python
# Role 1: Session auth (original)
user = authenticate(username='john', password='secret')
login(request, user)

# Role 2: API token
user = authenticate(token=request.headers['Authorization'])
return JsonResponse({'user': user.id})

# Role 3: OAuth
user = authenticate(oauth_token=external_token, provider='google')
link_external_identity(user, external_id)
```

---

### Example 2: `Manager`

**Anchored to:** Simple interface for retrieving QuerySet objects (2010)

**Identified roles:**
1. **Simple CRUD queries** (40-50%)
   - get(), filter(), create()
   - Original intent
   
2. **Complex analytical queries** (30-40%)
   - Multi-table joins
   - Aggregations and annotations
   
3. **Raw SQL execution** (10-15%)
   - Bypasses ORM entirely
   
4. **Performance optimization** (10-15%)
   - Bulk operations
   - Async queries

**Why semantic overload:**
- Four distinct query paradigms
- Simple CRUD still the largest role, but not dominant
- Each paradigm could have been separate: `CRUDManager`, `AnalyticsManager`, `RawQueryManager`, `BulkManager`

**Boundary case note:** This is borderline. Could be argued as "controlled feature growth" within the database domain. The verdict depends on whether you value narrow interfaces or comprehensive ones.

---

## When to Apply This Verdict

### Apply "Semantic Overload" when:

✅ Symbol serves 2+ distinct roles  
✅ No single role >60% of usage  
✅ Original intent is one of the roles  
✅ Roles could logically be separate abstractions  
✅ Roles serve unrelated concerns  

### Do NOT apply when:

❌ Only one semantic role (even if complex) → Check "Aligned"  
❌ New role displaced original (>60% usage) → "Intent Violation"  
❌ Symbol frozen by compatibility → "Dependency Inertia"  
❌ Roles are closely related variants → May still be "Aligned"  
❌ Deliberate facade/adapter pattern → Architectural choice, not drift  

---

## Boundary Cases

### Case 1: "Comprehensive Interface" vs. Overload

**Question:** When does a feature-rich interface become overloaded?

**Guideline:**
- If roles cluster into distinct purposes → Overload
- If roles are variations on one theme → Comprehensive interface

**Example:**
- `Manager` with CRUD + raw SQL → Overload (different paradigms)
- `Manager` with filter(), exclude(), get() → Comprehensive (all are queries)

### Case 2: 40/30/30 vs. 50/50 Split

**Question:** Does 2 roles at 50/50 count as overload?

**Guideline:**
- Yes, if the roles are semantically distinct
- No single role needs to dominate for overload
- The key is: could they have been separate?

**Example:**
- Function doing both validation AND persistence (50/50) → Overload
- Function doing both HTML rendering AND validation (50/50) → Overload

### Case 3: Intentional Flexibility

**Question:** What if the symbol was designed to be flexible?

**Guideline:**
- Intentional flexibility can still result in overload
- Original design intent doesn't excuse drift
- The question is: did flexibility enable unintended uses?

**Example:**
- `authenticate()` designed to support multiple backends
- But OAuth use case wasn't in original design
- Even if "flexible by design," the roles are overloaded

---

## Evidence Requirements

To support a "Semantic Overload" verdict, collect:

### Required Evidence

1. **Call context samples** showing distinct roles
   - At least 3-5 examples per role
   - From different modules/contexts
   
2. **Usage percentage estimates**
   - Based on framework adoption or codebase sampling
   - Show no single role dominates
   
3. **Original intent documentation**
   - Commit message, docstring, or implementation
   - Show original role is one of current roles

### Supporting Evidence

4. **Semantic clustering results**
   - Embedding-based similarity scores
   - Show low inter-role similarity (<0.7)
   
5. **Historical evolution**
   - When did each role emerge?
   - Was expansion gradual or sudden?
   
6. **Alternative design proposals**
   - Could roles have been separate functions?
   - What would separation look like?

---

## Verdict Template

```markdown
⚠ [symbol_name]

Anchored to:
  [original intent one-liner]

Current roles:
  - [Role 1]: [description] ([X%] of usage)
  - [Role 2]: [description] ([Y%] of usage)
  - [Role 3]: [description] ([Z%] of usage)

Verdict:
  Semantic Overload

Rationale:
  [Symbol] now serves [N] distinct [roles/purposes]. While each role 
  relates to [domain], their coexistence within a single abstraction 
  exceeds the responsibility implied by the original "[intent]" design. 
  These roles could have been separate abstractions: [alternatives].

Evidence:
  - Original intent: [cite commit/docstring]
  - Role distribution: [X/Y/Z% split]
  - No single role dominates (threshold: 60%)
  - Roles serve unrelated concerns: [list concerns]
```

---

## Comparison to Other Patterns

| Aspect | Semantic Overload | Intent Violation | Dependency Inertia |
|--------|-------------------|------------------|-------------------|
| Original role present? | Yes (as one role) | Sometimes (minority) | Yes (frozen) |
| Role distribution | Multiple (~equal) | One dominant | Original only |
| Evolution pattern | Horizontal expansion | Vertical displacement | Frozen |
| Key signal | Multiple purposes | Primary usage shift | Lack of change |

---

## Automation Strategy

### Step 1: Cluster Call Contexts
```python
embeddings = embed_call_contexts(symbol.call_sites)
clusters = DBSCAN(eps=0.3, min_samples=5).fit(embeddings)
roles = [analyze_cluster(c) for c in clusters]
```

### Step 2: Calculate Role Percentages
```python
total_calls = len(symbol.call_sites)
role_percentages = {
    role: len(role.call_sites) / total_calls 
    for role in roles
}
```

### Step 3: Check Overload Conditions
```python
if len(roles) >= 2:  # Multiple roles
    if max(role_percentages.values()) <= 0.6:  # No dominance
        if original_intent_in_roles(roles, symbol.intent_anchor):
            return "semantic_overload"
```

### Step 4: Verify Semantic Distance
```python
# Ensure roles are actually distinct
role_similarities = pairwise_similarity(roles)
if all(sim < 0.7 for sim in role_similarities):
    # Roles are semantically distinct
    confidence = "high"
```

---

## Common Mistakes

### Mistake 1: Confusing Complexity with Overload

❌ "This function is 100 lines long, so it's overloaded"  
✅ "This function serves 3 distinct purposes: auth, billing, analytics"

**Length ≠ Overload. Purpose multiplicity = Overload.**

### Mistake 2: Ignoring Domain Coherence

❌ "Manager has 60 methods, must be overloaded"  
✅ "Manager has 4 query paradigms (CRUD, analytics, raw SQL, bulk)"

**Method count alone doesn't prove overload. Distinct semantic roles do.**

### Mistake 3: False Positive on Variants

❌ "authenticate() supports username/email/phone, so it's overloaded"  
✅ "Those are input variants, not semantic roles"

**Multiple inputs ≠ Overload. Multiple purposes = Overload.**

---

## Recommended Actions (When Overload Detected)

Anchor does **not** prescribe actions, but teams typically consider:

1. **Accept and document**
   - Acknowledge the overload
   - Document each role clearly
   - Add intent markers for future reference

2. **Split into separate abstractions**
   - `authenticate()` → `authenticate_session()`, `authenticate_token()`, `authenticate_oauth()`
   - Keep original for backward compatibility (delegating)

3. **Introduce facade/adapter**
   - Keep overloaded symbol as facade
   - Delegate to focused implementations
   - Gradually migrate callers

4. **Mark for future refactor**
   - Add to technical debt registry
   - Prevent further role accumulation
   - Revisit during major version bump

**Anchor's role ends at detection. Humans choose the response.**

---

## References

- **Django `authenticate()` audit** - Full example of semantic overload
- **Django `Manager` audit** - Boundary case example
- **Philosophy.md** - Core principles
- **Complete Findings Report** - Context and comparisons

---

**Key Takeaway:**

Semantic Overload = Multiple distinct roles coexist, none dominates, original intent still present.

It's the "Swiss Army knife problem" - useful but conceptually muddled.