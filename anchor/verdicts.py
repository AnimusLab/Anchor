"""Drift detection engine - implements invariants.md contract."""

from typing import Optional, List
from .symbols import Symbol, Role, Metrics, Verdict, Confidence


class DriftDetector:
    """
    Deterministic drift detector.

    Implements the contract defined in docs/internal/invariants.md.
    Every check maps directly to a line in that document.
    """

    def detect(
        self,
        symbol: Symbol,
        roles: List[Role],
        metrics: Metrics
    ) -> tuple[Verdict, Confidence]:
        """
        Apply invariants.md detection rules.

        Returns: (verdict, confidence)
        """

        # Check preconditions (common to all verdicts)
        if not self._check_basic_preconditions(symbol, metrics):
            return ("confidence_too_low", "low")

        # Try each verdict in order (order matters!)
        # aligned first (most specific)
        if verdict := self._check_aligned(roles, metrics):
            return verdict

        # semantic_overload (requires multiple roles)
        if verdict := self._check_semantic_overload(roles, metrics):
            return verdict

        # intent_violation (requires role displacement)
        if verdict := self._check_intent_violation(roles, metrics):
            return verdict

        # dependency_inertia (requires stagnation)
        if verdict := self._check_dependency_inertia(metrics):
            return verdict

        # No verdict matched
        return ("confidence_too_low", "low")

    def _check_basic_preconditions(self, symbol: Symbol, metrics: Metrics) -> bool:
        """Check if we have enough data to make any verdict."""
        return (
            len(symbol.call_contexts) >= 10 and
            symbol.intent_anchor is not None and
            metrics.git_history_depth > 0
        )

    def _check_aligned(
        self,
        roles: List[Role],
        metrics: Metrics
    ) -> Optional[tuple[Verdict, Confidence]]:
        """
        aligned verdict from invariants.md.

        Required signals (ALL must be true):
        - role_count == 1 OR (role_count > 1 AND min(similarity) > 0.8)
        - intent_alignment_percentage >= 0.90
        - violated_assumptions_count == 0
        - changes_in_5_years > 0
        """

        # Disqualifying signals (ANY triggers rejection)
        disqualified = (
            (metrics.role_count >= 2 and
             min(metrics.pairwise_role_similarity) <= 0.8 if metrics.pairwise_role_similarity else False) or
            metrics.intent_alignment_percentage < 0.90 or
            metrics.violated_assumptions_count > 0 or
            metrics.workaround_percentage >= 0.40 or
            metrics.has_documented_alternatives
        )

        if disqualified:
            return None

        # Required signals (ALL must be true)
        required = (
            (metrics.role_count == 1 or
             (metrics.role_count > 1 and
              min(metrics.pairwise_role_similarity) > 0.8 if metrics.pairwise_role_similarity else False)) and
            metrics.intent_alignment_percentage >= 0.90 and
            metrics.violated_assumptions_count == 0 and
            metrics.changes_in_5_years > 0
        )

        if not required:
            return None

        # Confidence downgrades
        confidence: Confidence = "high"
        if (metrics.call_site_count < 20 or
            metrics.git_history_depth < 50 or
                metrics.intent_anchor_confidence == "low"):
            confidence = "medium"

        return ("aligned", confidence)

    def _check_semantic_overload(
        self,
        roles: List[Role],
        metrics: Metrics
    ) -> Optional[tuple[Verdict, Confidence]]:
        """
        semantic_overload verdict from invariants.md.

        Required signals:
        - role_count >= 2
        - max(role_percentages) <= 0.60
        - min(pairwise_role_similarity) < 0.7
        - original_intent_role_percentage > 0.20
        """

        # Disqualifying signals
        disqualified = (
            metrics.role_count == 1 or
            metrics.max_role_percentage > 0.60 or
            (min(metrics.pairwise_role_similarity) >= 0.7 if metrics.pairwise_role_similarity else True) or
            metrics.original_intent_role_percentage <= 0.20 or
            metrics.original_intent_role_percentage == 0
        )

        if disqualified:
            return None

        # Required signals
        required = (
            metrics.role_count >= 2 and
            metrics.max_role_percentage <= 0.60 and
            (min(metrics.pairwise_role_similarity) < 0.7 if metrics.pairwise_role_similarity else False) and
            metrics.original_intent_role_percentage > 0.20
        )

        if not required:
            return None

        # Confidence downgrades
        confidence: Confidence = "high"

        # Boundary cases
        if (metrics.role_count == 2 and
                metrics.max_role_percentage in [0.58, 0.59, 0.60]):
            confidence = "medium"

        if metrics.call_site_count < 30:
            confidence = "medium"

        if metrics.clustering_quality < 0.3:
            confidence = "medium"

        if metrics.original_intent_role_percentage < 0.25:
            confidence = "medium"

        return ("semantic_overload", confidence)

    def _check_intent_violation(
        self,
        roles: List[Role],
        metrics: Metrics
    ) -> Optional[tuple[Verdict, Confidence]]:
        """
        intent_violation verdict from invariants.md.

        Required signals:
        - primary_role_percentage > 0.50
        - primary_role != original_intent_role
        - original_intent_role_percentage > 0 AND < 0.50
        - unused_original_features_percentage > 0.50
        """

        # Disqualifying signals
        disqualified = (
            metrics.max_role_percentage <= 0.50 or
            metrics.primary_role_is_original or
            metrics.original_intent_role_percentage >= 0.50 or
            metrics.original_intent_role_percentage == 0 or
            metrics.unused_original_features_percentage <= 0.50
        )

        if disqualified:
            return None

        # Required signals
        required = (
            metrics.max_role_percentage > 0.50 and
            not metrics.primary_role_is_original and
            metrics.original_intent_role_percentage > 0 and
            metrics.original_intent_role_percentage < 0.50 and
            metrics.unused_original_features_percentage > 0.50
        )

        if not required:
            return None

        # Confidence downgrades
        confidence: Confidence = "high"

        # Boundary cases
        if metrics.max_role_percentage in [0.50, 0.51, 0.52, 0.53, 0.54, 0.55]:
            confidence = "medium"

        if metrics.original_intent_role_percentage in [0.45, 0.46, 0.47, 0.48, 0.49]:
            confidence = "medium"

        if metrics.call_site_count < 30:
            confidence = "medium"

        if metrics.unused_original_features_percentage in [0.48, 0.49, 0.50, 0.51, 0.52]:
            confidence = "medium"

        return ("intent_violation", confidence)

    def _check_dependency_inertia(
        self,
        metrics: Metrics
    ) -> Optional[tuple[Verdict, Confidence]]:
        """
        dependency_inertia verdict from invariants.md.

        Required signals:
        - meaningful_changes_in_5_years < 10
        - has_documented_alternatives == True
        - workaround_percentage >= 0.40
        - dependent_count > 1000
        """

        # Disqualifying signals
        disqualified = (
            metrics.changes_in_5_years >= 10 or
            not metrics.has_documented_alternatives or
            metrics.workaround_percentage < 0.40 or
            metrics.dependent_count <= 1000
        )

        if disqualified:
            return None

        # Required signals
        required = (
            metrics.changes_in_5_years < 10 and
            metrics.has_documented_alternatives and
            metrics.workaround_percentage >= 0.40 and
            metrics.dependent_count > 1000
        )

        if not required:
            return None

        # Confidence downgrades
        confidence: Confidence = "high"

        # Boundary cases
        if metrics.workaround_percentage in [0.38, 0.39, 0.40, 0.41, 0.42]:
            confidence = "medium"

        if metrics.changes_in_5_years in [8, 9, 10, 11, 12]:
            confidence = "medium"

        return ("dependency_inertia", confidence)
