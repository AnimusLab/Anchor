# Invariants - Detection Contract

**Status:** Calibrated on Django (11 symbols)

---

## aligned

### Preconditions
- Symbol has git history
- Call sites exist (n ≥ 20)
- Intent anchor extractable

### Required signals
- `role_count == 1` OR `(role_count > 1 AND min(pairwise_role_similarity) > 0.8)`
- `intent_alignment_percentage >= 0.90`
- `violated_assumptions_count == 0`
- `changes_in_5_years > 0`

### Disqualifying signals
- `role_count >= 2 AND max(pairwise_role_similarity) <= 0.8`
- `intent_alignment_percentage < 0.90`
- `violated_assumptions_count > 0`
- `workaround_percentage >= 0.40`
- `has_documented_alternatives == True`

### Confidence downgrade conditions
- `call_site_count < 20`
- `git_history_depth < 50`
- `intent_anchor_confidence == "low"`

---

## semantic_overload

### Preconditions
- Symbol has git history
- Call sites exist (n ≥ 20)
- Intent anchor extractable
- Roles clusterable

### Required signals
- `role_count >= 2`
- `max(role_percentages) <= 0.60`
- `min(pairwise_role_similarity) < 0.7`
- `original_intent_role_percentage > 0.20`

### Disqualifying signals
- `role_count == 1`
- `max(role_percentages) > 0.60`
- `min(pairwise_role_similarity) >= 0.7`
- `original_intent_role_percentage <= 0.20`
- `original_intent_role_percentage == 0`

### Confidence downgrade conditions
- `role_count == 2 AND max(role_percentages) in [0.58, 0.59, 0.60]`
- `call_site_count < 30`
- `role_clustering_silhouette_score < 0.3`
- `original_intent_role_percentage < 0.25`

---

## intent_violation

### Preconditions
- Symbol has git history
- Call sites exist (n ≥ 20)
- Intent anchor extractable
- Roles clusterable

### Required signals
- `primary_role_percentage > 0.50`
- `primary_role != original_intent_role`
- `original_intent_role_percentage > 0` AND `original_intent_role_percentage < 0.50`
- `unused_original_features_percentage > 0.50`

### Disqualifying signals
- `primary_role_percentage <= 0.50`
- `primary_role == original_intent_role`
- `original_intent_role_percentage >= 0.50`
- `original_intent_role_percentage == 0`
- `unused_original_features_percentage <= 0.50`

### Confidence downgrade conditions
- `primary_role_percentage in [0.50, 0.51, 0.52, 0.53, 0.54, 0.55]`
- `original_intent_role_percentage in [0.45, 0.46, 0.47, 0.48, 0.49]`
- `call_site_count < 30`
- `unused_original_features_percentage in [0.48, 0.49, 0.50, 0.51, 0.52]`

---

## dependency_inertia

### Preconditions
- Symbol has git history (≥5 years)
- Usage data available
- Alternative symbols searchable
- Dependent count measurable

### Required signals
- `meaningful_changes_in_5_years < 10`
- `has_documented_alternatives == True`
- `workaround_percentage >= 0.40`
- `dependent_count > 1000`

### Disqualifying signals
- `meaningful_changes_in_5_years >= 10`
- `has_documented_alternatives == False`
- `workaround_percentage < 0.40`
- `dependent_count <= 1000`

### Confidence downgrade conditions
- `git_history_years < 5`
- `workaround_percentage in [0.38, 0.39, 0.40, 0.41, 0.42]`
- `meaningful_changes_in_5_years in [8, 9, 10, 11, 12]`
- `workaround_detection_confidence == "low"`
- `alternative_documentation_ambiguous == True`