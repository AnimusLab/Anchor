# Drift Pattern: Dependency Inertia

**Definition:** Symbol survives due to backward compatibility and dependency concerns rather than design validity. Alternatives exist but original persists.

---

## Characteristics

### Primary Indicators

1. **Structurally unchanged over many years**
   - Minimal evolution despite evolving requirements
   - Only security fixes or critical patches
   - Core design frozen in time

2. **Documented limitations**
   - Known issues acknowledged in documentation
   - Workarounds widely documented
   - Community discusses limitations openly

3. **Alternative abstractions exist**
   - Framework provides alternatives (e.g., AbstractUser vs User)
   - Alternatives explicitly address original's limitations
   - New projects encouraged to use alternatives

4. **High dependent count**
   - Thousands of projects depend on symbol
   - Removing it would break massive amounts of code
   - Backward compatibility is paramount

5. **Prevalent workaround patterns**
   - Users extend, wrap, or work around symbol
   - Workarounds more common than direct usage
   - Community has "standard hacks"

6. **Survival is inertia, not validity**
   - Symbol persists because removing it is too costly
   - NOT because it's the best design
   - Compatibility trumps quality

---

## Detection Heuristics

### Quantitative Signals

```python
def is_dependency_inertia(symbol_analysis):
    # Check structural stagnation
    change_count = count_meaningful_changes(
        symbol_analysis.history,
        years=5
    )
    
    if change_count > 10:
        return False  # Active evolution, not inertia
    
    # Check for alternatives
    alternatives = find_alternative_symbols(symbol_analysis)
    
    if not alternatives:
        return False  # No alternatives = not inertia
    
    # Check workaround prevalence
    workarounds = detect_workaround_patterns(symbol_analysis.usages)
    workaround_percentage = len(workarounds) / len(symbol_analysis.usages)
    
    if workaround_percentage < 0.4:
        return False  # <40% workarounds
    
    # Check dependent count
    dependents = count_dependents(symbol_analysis)
    
    if dependents < 1000:
        return False  # Not widely used enough for inertia
    
    return True
```

### Qualitative Checks

**Ask these questions:**

1. Has the symbol's design remained frozen for 5+ years?
   - If yes → Inertia candidate

2. Are there documented alternatives that address its limitations?
   - If yes → Inertia candidate

3. Do most users extend or work around the symbol?
   - If yes → Inertia candidate

4. Would removing the symbol break thousands of projects?
   - If yes → Inertia candidate

5. Does the symbol survive due to compatibility, not quality?
   - If yes → Inertia

---

## Django Example

### Example: `User` Model

**Anchored to:** Username/password authentication model (2007)

**Why dependency inertia:**

**1. Structurally frozen (2007-present)**
```python
# 2007 design (mostly unchanged)
class User(models.Model):
    username = CharField(max_length=30, unique=True)  # Fixed length
    password = CharField(max_length=128)
    email = EmailField()
    # ... permissions fields
```

**Key limitation:** 30-character username limit  
**Problem:** Many emails exceed 30 characters  
**Fix timeline:** Django couldn't change to 150 until 2016 (9 years)  
**Reason:** Database migration concerns, backward compatibility

**2. Documented limitations**

Django's official docs (2013+):
> "If you're starting a new project, it's highly recommended to set up a custom user model, even if the default User model is sufficient for you."

Translation: "We know User is limited, please don't use it directly."

**3. Alternative provided: AbstractUser (2013)**

```python
# Django provided this specifically because User was insufficient
class AbstractUser(AbstractBaseUser):
    # Customizable username field
    username = CharField(max_length=150)  # Can override
    USERNAME_FIELD = 'username'  # Can change to email
    # ... more flexible
```

**Why AbstractUser exists:** To address User's limitations without breaking compatibility.

**4. Prevalent workarounds (60-70% of usage)**

**Workaround 1: Email-as-username**
```python
# Store email in username field (hack)
user = User.objects.create_user(
    username=email,  # Email exceeding 30 chars gets truncated!
    email=email
)
```

**Workaround 2: Synthetic usernames**
```python
# OAuth users with unusable passwords
user = User.objects.create_user(
    username=f"google_{oauth_id}",  # Generated, not real username
    email=oauth_email,
    password='!'  # Unusable password marker
)
user.set_unusable_password()
```

**Workaround 3: Profile extensions**
```python
# User is insufficient, extend it
class UserProfile(models.Model):
    user = OneToOneField(User)
    # All the REAL user data here
    bio = TextField()
    avatar = ImageField()
    phone = CharField()
    # ... dozens more fields
```

**5. High dependent count**
- Tens of thousands of Django projects use User
- Third-party packages (allauth, social-auth, etc.) depend on it
- Migrations would break everything

**6. Survival = compatibility, not design**

Django core team knows User is limited (hence AbstractUser).  
User persists because:
- Removing it breaks every Django project
- Changing it requires complex migrations
- Backward compatibility is more important than ideal design

**This is textbook dependency inertia.**

---

## When to Apply This Verdict

### Apply "Dependency Inertia" when:

✅ Symbol structurally unchanged for 5+ years  
✅ Alternative abstractions exist addressing limitations  
✅ Workarounds prevalent (40%+ of usage)  
✅ High dependent count (1000s of projects)  
✅ Documented limitations acknowledged  
✅ Survival is compatibility-driven, not design-driven  

### Do NOT apply when:

❌ Symbol actively evolving → Check other patterns  
❌ No alternatives exist → May be "Aligned" or other drift  
❌ Workarounds rare → Not inertia  
❌ Low dependent count → Easy to change, not inertia  
❌ Limitations not documented → May not be recognized  

---

## Boundary Cases

### Case 1: Stable Design vs. Frozen Design

**Question:** How do we distinguish intentional stability from inertia?

**Guideline:**
- Stable design: Well-suited to requirements, minimal workarounds
- Frozen design: Known limitations, widespread workarounds, alternatives exist

**Example:**
- `login()` is stable (does one thing well, no workarounds)
- `User` is frozen (many workarounds, AbstractUser exists)

### Case 2: High Compatibility Value

**Question:** What if backward compatibility IS a feature?

**Guideline:**
- Compatibility is valuable, but inertia is still inertia
- The verdict doesn't say "remove it immediately"
- It says "persists due to compatibility, not design validity"
- This is useful information, not a condemnation

**Example:**
- User persists for good reasons (compatibility)
- But it's still inertia (design is insufficient)
- Both can be true

### Case 3: Partial Workarounds

**Question:** What if only some users need workarounds?

**Guideline:**
- Threshold: 40%+ usage involves workarounds
- If <40%, might not be inertia
- Consider: Is the symbol insufficient for modern needs?

---

## Evidence Requirements

To support a "Dependency Inertia" verdict, collect:

### Required Evidence

1. **Structural stagnation metrics**
   - Change count over last 5 years
   - Types of changes (features vs. security fixes)
   - Show minimal evolution

2. **Alternative abstractions**
   - List alternatives (AbstractUser, BaseUser, etc.)
   - Document when they were introduced
   - Note explicit acknowledgment of limitations

3. **Workaround patterns**
   - Identify common workarounds
   - Estimate percentage of usage with workarounds
   - Show prevalence across codebases

4. **Dependent count**
   - Number of projects depending on symbol
   - Third-party package dependencies
   - Show removal cost would be high

### Supporting Evidence

5. **Documentation acknowledgment**
   - Official docs mentioning limitations
   - Recommendations to use alternatives
   - Migration guides

6. **Community discussions**
   - Stack Overflow questions about workarounds
   - Blog posts on "better alternatives"
   - Issue tracker discussions

7. **Historical context**
   - Why was the symbol frozen?
   - What would break if changed?
   - Migration complexity

---

## Verdict Template

```markdown
⚠ [symbol_name]

Anchored to:
  [original intent one-liner]

Current state:
  - Structurally unchanged since [year]
  - [X%] of usage involves workarounds
  - Alternative provided: [alternative_name] (since [year])
  - Dependents: [high/very high]

Verdict:
  Dependency Inertia

Rationale:
  [Symbol] was designed for [original intent] with specific constraints:
  [list constraints]. Modern usage requires workarounds: [list workarounds].
  [Framework] acknowledged limitations by introducing [alternative] in [year].
  Despite known insufficiencies, [symbol] cannot be modified due to [X]
  dependent projects and backward compatibility concerns. [Symbol] survives
  due to dependency inertia, not design appropriateness.

Evidence:
  - Unchanged since: [year]
  - Alternative: [alternative_name] (addresses [limitations])
  - Workaround prevalence: [X%]
  - Documentation acknowledges limitations: [cite]
```

---

## Comparison to Other Patterns

| Aspect | Dependency Inertia | Semantic Overload | Intent Violation |
|--------|-------------------|-------------------|------------------|
| Evolution | Frozen | Expanded | Shifted |
| Alternatives exist? | Yes (explicit) | No | No |
| Workarounds | Very common | Rare | Medium |
| Original design valid? | No (outdated) | Questionable | Yes (for original context) |
| Why it persists | Compatibility | Convenience | Adoption |

---

## Automation Strategy

### Step 1: Measure Structural Change
```python
def measure_stagnation(symbol_history, years=5):
    cutoff = now() - timedelta(days=years*365)
    recent_commits = [c for c in symbol_history 
                      if c.date > cutoff]
    
    meaningful_changes = [c for c in recent_commits 
                          if not is_security_fix(c)
                          and not is_doc_only(c)]
    
    return len(meaningful_changes)  # Low count = stagnation
```

### Step 2: Detect Alternatives
```python
def find_alternatives(symbol, codebase):
    # Look for Abstract* versions
    if symbol.name == "User":
        alternatives = search_symbols(["AbstractUser", "AbstractBaseUser"])
    
    # Check documentation
    docs = parse_documentation(codebase)
    mentions = docs.search(f"instead of {symbol.name}, use")
    
    return alternatives
```

### Step 3: Identify Workarounds
```python
def detect_workarounds(symbol_usages):
    patterns = [
        "OneToOneField(User)",  # Profile extension
        "username=email",        # Email-as-username
        "set_unusable_password", # OAuth hack
        # ... more patterns
    ]
    
    workaround_count = sum(
        1 for usage in symbol_usages
        if any(p in usage.code for p in patterns)
    )
    
    return workaround_count / len(symbol_usages)
```

### Step 4: Count Dependents
```python
def count_dependents(symbol, ecosystem):
    # GitHub search
    github_usage = search_github(f"from django.contrib.auth.models import {symbol.name}")
    
    # PyPI package dependencies
    pypi_deps = search_pypi_dependencies(f"django.contrib.auth.models.{symbol.name}")
    
    return len(github_usage) + len(pypi_deps)
```

---

## Common Mistakes

### Mistake 1: Confusing Stability with Inertia

❌ "`login()` hasn't changed in 10 years, must be inertia"  
✅ "`login()` is stable (no workarounds, no alternatives needed)"

**Stability = good design that doesn't need change**  
**Inertia = frozen design with known problems**

### Mistake 2: Ignoring Alternatives

❌ "User is fine, still widely used"  
✅ "Django added AbstractUser because User is insufficient"

**If alternatives exist, ask why.**

### Mistake 3: Dismissing Workarounds

❌ "Extending User with profiles is normal OOP"  
✅ "60% of projects extend User because it's insufficient"

**Widespread workarounds signal design inadequacy.**

---

## The Positive Side of Inertia

Dependency inertia is **not always bad**:

**Pros:**
- ✅ Stability is valuable
- ✅ Not breaking things is important
- ✅ Migrations are costly and risky
- ✅ Backward compatibility enables large ecosystems

**The verdict doesn't say "remove it."**

It says: "This persists for compatibility reasons, not design validity."

**This is useful information for:**
- New projects (use alternatives)
- Existing projects (understand the constraints)
- Framework maintainers (acknowledge the trade-off)
- AI agents (don't suggest changes that break compatibility)

---

## Recommended Actions (When Inertia Detected)

Anchor does **not** prescribe actions, but teams typically consider:

1. **Document the situation**
   - Acknowledge the symbol's limitations
   - Point users to alternatives
   - Explain why it can't change

2. **Guide new projects to alternatives**
   - AbstractUser instead of User
   - Make alternatives the default
   - Deprecate original for new code

3. **Support migration paths**
   - Tools to migrate from old to new
   - Documentation and examples
   - Community support

4. **Accept the trade-off**
   - Stability > ideal design
   - This is a conscious choice
   - Make the choice explicit

5. **Plan for major version**
   - Breaking changes possible in major versions
   - Allows modernization
   - Community preparation time

**Inertia is often the right choice. Making it explicit is the value.**

---

## Historical Examples

### Django User (2007-present)

**Timeline:**
- 2007: User created with 30-char username
- 2008-2012: Email login demand grows
- 2013: AbstractUser added (admission of limitations)
- 2016: Username length increased to 150 (9-year delay)
- Present: User persists for compatibility

**Lesson:** Even small changes (field length) take years due to inertia.

---

## References

- **Django `User` audit** - Primary example
- **Philosophy.md** - Core principles
- **Complete Findings Report** - Full context

---

**Key Takeaway:**

Dependency Inertia = Symbol frozen by compatibility concerns despite known limitations and existing alternatives.

It's the "too big to change problem" - we know it's not ideal, but we can't fix it without breaking everything.

**Identifying inertia helps teams:**
- Choose better alternatives for new projects
- Understand constraints in existing projects
- Make informed migration decisions
- Set realistic expectations