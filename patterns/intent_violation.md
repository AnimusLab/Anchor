# Drift Pattern: Intent Violation

**Definition:** Primary usage no longer matches original intent; new role has displaced the original.

---

## Characteristics

### Primary Indicators

1. **Primary usage contradicts original intent**
   - Majority of usage (>50%) violates original assumptions
   - Most common use case was NOT the design target
   - New role has become dominant

2. **Core features unused in majority contexts**
   - Original methods/features ignored
   - >50% of instances never use original functionality
   - Original features treated as "dead code"

3. **Name/structure implies original intent**
   - Symbol name suggests original purpose
   - Structure/methods reflect original design
   - But actual usage is different

4. **Original intent now minority usage**
   - Original use case still exists but <50%
   - Not absent (that would be abandonment)
   - But no longer primary

---

## Detection Heuristics

### Quantitative Signals

```python
def is_intent_violation(symbol_analysis):
    roles = cluster_call_contexts(symbol_analysis.call_sites)
    
    # Find primary role (>50% usage)
    primary_role = max(roles, key=lambda r: r.percentage)
    
    if primary_role.percentage <= 50:
        return False  # Likely Semantic Overload instead
    
    # Check if primary role matches original intent
    intent_match = semantic_similarity(
        primary_role.description,
        symbol_analysis.intent_anchor.description
    )
    
    if intent_match > 0.7:
        return False  # Primary usage matches intent = Aligned
    
    # Check if original features unused
    original_methods = symbol_analysis.intent_anchor.methods
    unused_count = count_unused_methods(original_methods, symbol_analysis)
    
    if unused_count / len(original_methods) > 0.5:
        return True  # >50% of original features unused
    
    return True  # Primary usage violates intent
```

### Qualitative Checks

**Ask these questions:**

1. Does the primary use case (>50%) match the original intent?
   - If no → Intent violation candidate

2. Are original features unused in majority contexts?
   - If yes → Intent violation candidate

3. Does the symbol name/structure imply the original purpose?
   - If yes (and usage differs) → Intent violation

4. Has a new paradigm displaced the original?
   - If yes → Intent violation

---

## Django Examples

### Example 1: `Form`

**Anchored to:** Define and render HTML forms for templates (2012)

**Primary usage shift:**
- **Original:** HTML form rendering (20-30%)
- **Current dominant:** API validation (60-70%)

**Why intent violation:**
- 60-70% of Form usage is API validation (no HTML)
- HTML rendering methods (as_p, as_table, as_ul) unused in majority contexts
- Name "Form" and structure imply HTML forms
- Primary usage (API validation) was NOT the design target

**Evidence:**
```python
# Original intent (30% usage)
form = ContactForm(request.POST)
if form.is_valid():
    # ...
return render(request, 'form.html', {'form': form})
# Template uses: {{ form.as_p }}

# Current primary usage (70% usage)
form = ContactForm(request.data)  # JSON, not HTML POST
if form.is_valid():
    return Response(form.cleaned_data, status=201)
return Response(form.errors, status=400)
# Never calls as_p(), as_table(), or any HTML method
```

**Key signal:** HTML generation methods are dead code in 70% of contexts.

---

### Example 2: `ModelForm`

**Anchored to:** Auto-generate HTML forms from models (2008)

**Primary usage shift:**
- **Original:** HTML CRUD forms (30-40%)
- **Current dominant:** API validation + persistence (60%)

**Why intent violation:**
- 60% of ModelForm usage is API/programmatic (no HTML)
- Inherits Form's HTML methods but doesn't use them
- save() method became the attraction (not HTML generation)
- Name implies "form" (HTML UI) but used as validator

**Accelerating factor:**
- save() method made it attractive for non-HTML contexts
- DRF, GraphQL adopted ModelForm as validator
- Inherited Form's drift and accelerated it

---

### Example 3: `BaseForm`

**Anchored to:** Core form implementation with HTML output (2012)

**Why intent violation:**
- Same as Form (it IS Form's implementation)
- Contains all the HTML generation logic
- Primary usage doesn't touch HTML methods

**Note:** This is inherited drift, not independent.

---

## When to Apply This Verdict

### Apply "Intent Violation" when:

✅ Primary usage (>50%) contradicts original intent  
✅ Original features unused in majority contexts  
✅ New dominant role was not the design target  
✅ Name/structure implies original intent  
✅ Original use case still exists but minority  

### Do NOT apply when:

❌ Multiple roles with no clear primary (≤50%) → "Semantic Overload"  
❌ Usage matches original intent → "Aligned"  
❌ Symbol frozen with no evolution → "Dependency Inertia"  
❌ Original intent deliberately redefined (with markers) → "Aligned" (new epoch)  
❌ Primary usage IS the original intent → "Aligned"  

---

## Boundary Cases

### Case 1: 55% New Usage vs. 70% New Usage

**Question:** Where's the threshold for "primary" usage?

**Guideline:**
- 50-60%: Borderline, could be either violation or overload
- 60%+: Clear primary usage, likely violation
- Consider: How strongly does usage violate assumptions?

**Example:**
- 55% API validation, 45% HTML → Borderline
- 70% API validation, 30% HTML → Clear violation

### Case 2: Original Intent Preserved in Name

**Question:** What if the name still suggests original intent?

**Guideline:**
- This STRENGTHENS the violation verdict
- Name implies one thing, usage is another
- Creates confusion and misleading expectations

**Example:**
- Class called `Form` but used as `Validator`
- Name suggests HTML forms, reality is data validation

### Case 3: Intentional Expansion

**Question:** What if the expansion was intentional?

**Guideline:**
- Without explicit redefinition marker, it's still violation
- Intent must change EXPLICITLY, not silently
- "We meant to expand it" ≠ documented redefinition

**Example:**
- Form expanded to support APIs (no @intent marker)
- Even if intentional, it's still violation (silent change)

---

## Evidence Requirements

To support an "Intent Violation" verdict, collect:

### Required Evidence

1. **Original intent documentation**
   - Commit message, docstring, method names
   - Show what symbol was designed for
   
2. **Primary usage analysis**
   - Show >50% usage violates original assumptions
   - Call context samples from dominant use case
   
3. **Unused feature analysis**
   - List original features unused in primary context
   - Percentage of methods that are dead code
   
4. **Usage shift timeline**
   - When did the new usage become primary?
   - Was it gradual or sudden?

### Supporting Evidence

5. **Framework adoption data**
   - DRF, GraphQL, etc. adoption correlates with shift
   - External ecosystem drove the change
   
6. **Assumption violation list**
   - Which original assumptions are violated?
   - Be specific and code-level

7. **Name/structure mismatch**
   - Does the name imply original intent?
   - Does structure reflect original design?

---

## Verdict Template

```markdown
⚠ [symbol_name]

Anchored to:
  [original intent one-liner]

Current usage:
  - [Original role]: [X%] of usage
  - [New dominant role]: [Y%] of usage (PRIMARY)

Verdict:
  Intent Violation

Rationale:
  [Symbol] was designed for [original intent] as evidenced by [original features].
  Current usage is dominated by [new role] ([Y%]) where [original features] 
  remain unused. This represents a primary usage shift from [original] to [new], 
  violating the symbol's original intent. The name/structure still implies 
  [original intent], creating conceptual mismatch.

Evidence:
  - Original features: [list methods/behaviors]
  - Primary usage: [Y%] in [contexts]
  - Unused in primary usage: [list original features]
  - Original assumptions violated: [list specific violations]
```

---

## Comparison to Other Patterns

| Aspect | Intent Violation | Semantic Overload | Dependency Inertia |
|--------|------------------|-------------------|-------------------|
| Primary role displaces original? | Yes (>50%) | No (multiple ~equal) | N/A (frozen) |
| Original features used? | Minority contexts | In some roles | Yes (unchanged) |
| Usage distribution | 30/70 or 20/80 | 33/33/33 or 40/30/30 | 100 (original only) |
| Key signal | Displacement | Multiplicity | Stagnation |

---

## Automation Strategy

### Step 1: Identify Primary Usage
```python
roles = cluster_call_contexts(symbol.call_sites)
primary_role = max(roles, key=lambda r: r.percentage)

if primary_role.percentage <= 0.5:
    return "not_intent_violation"  # Check semantic_overload
```

### Step 2: Check Intent Match
```python
intent_similarity = semantic_similarity(
    primary_role.description,
    symbol.intent_anchor.description
)

if intent_similarity > 0.7:
    return "aligned"  # Primary usage matches intent
```

### Step 3: Measure Feature Usage
```python
original_methods = extract_methods(symbol.intent_anchor)
usage_by_method = count_method_calls(symbol.call_sites, original_methods)

unused_percentage = len([m for m in original_methods 
                         if usage_by_method[m] / total_calls < 0.1])
unused_percentage /= len(original_methods)

if unused_percentage > 0.5:
    confidence = "high"  # >50% of original features unused
```

### Step 4: Generate Evidence
```python
return {
    "verdict": "intent_violation",
    "primary_role": primary_role.name,
    "primary_percentage": primary_role.percentage,
    "original_percentage": 1 - primary_role.percentage,
    "unused_features": [m for m in original_methods 
                        if usage_by_method[m] < 0.1],
    "violated_assumptions": identify_violations(symbol)
}
```

---

## Common Mistakes

### Mistake 1: Confusing with Semantic Overload

❌ "Form does both HTML and API, so it's overloaded"  
✅ "Form's PRIMARY usage (70%) is API, violating HTML intent"

**Check primary usage percentage. >50% in one role = violation, not overload.**

### Mistake 2: Ignoring Unused Features

❌ "Form still CAN render HTML, so it's fine"  
✅ "70% of Form instances never call as_p(), it's dead code"

**Capability ≠ Usage. What matters is actual usage patterns.**

### Mistake 3: Accepting Silent Expansion

❌ "Form naturally evolved to support APIs"  
✅ "Form expanded without explicit redefinition"

**Evolution is fine IF it's explicit. Silent shifts are violations.**

---

## Special Case: Inherited Drift

Some symbols inherit drift from their parent:

**Pattern:**
- Parent drifts (e.g., Form → API validation)
- Child extends parent (e.g., ModelForm extends Form)
- Child inherits drift automatically
- Child may ACCELERATE drift with new features

**Example: ModelForm**
- Inherits Form's HTML rendering (unused in 60% of contexts)
- Adds save() method (attracts API usage)
- API usage percentage HIGHER than Form's
- Inherited + accelerated drift

**Detection:**
- Check if parent has intent violation verdict
- If yes, child likely inherits it
- Look for features that accelerated the drift

---

## Recommended Actions (When Violation Detected)

Anchor does **not** prescribe actions, but teams typically consider:

1. **Explicit redefinition**
   ```python
   # @intent: redefine — now serves as API validator
   class Form:
       ...
   ```
   - Acknowledge the shift
   - Create new intent epoch
   - Update documentation

2. **Separation**
   - Create new symbol for new usage: `DataValidator`
   - Keep original for original purpose: `HTMLForm`
   - Gradually migrate API usage to new symbol

3. **Rename to match reality**
   - `Form` → `Validator` (if HTML minority)
   - Update all references
   - Breaking change, requires major version

4. **Accept and document**
   - Acknowledge the mismatch
   - Document both use cases clearly
   - Warn users about conceptual confusion

5. **Deprecate and replace**
   - Mark original as deprecated
   - Provide clear alternatives
   - Migration guide for both use cases

**Anchor's role ends at detection. Humans choose the response.**

---

## Historical Context

Intent violations often arise from:

1. **Ecosystem adoption**
   - External tools (DRF, GraphQL) adopt symbols for unintended purposes
   - Adoption snowballs, becomes dominant
   - Original usage becomes minority

2. **Paradigm shifts**
   - Web moved from server-rendered to API-first
   - Form designed for HTML, used for JSON
   - Technology landscape changed, symbols didn't

3. **Lack of alternatives**
   - No ModelValidator, so people use ModelForm
   - No API validator, so people use Form
   - Symbols used for lack of alternatives

4. **Backward compatibility**
   - Can't change existing symbols (breaking)
   - Can't add alternatives easily
   - Drift accumulates silently

**Understanding context helps predict where violations occur.**

---

## References

- **Django `Form` audit** - Primary example
- **Django `ModelForm` audit** - Inherited drift example
- **Philosophy.md** - Core principles
- **Complete Findings Report** - Full context

---

**Key Takeaway:**

Intent Violation = New dominant role displaces original, original features unused in majority contexts.

It's the "bait and switch problem" - the name promises one thing, reality delivers another.