# anchor/metrics.py
"""Metrics calculation for drift detection."""

from typing import List
from .symbols import Symbol, Role, Metrics
from .contexts import RoleClusterer


class MetricsCalculator:
    """Calculate all metrics required by invariants.md."""

    def __init__(self):
        self.clusterer = RoleClusterer()

    def calculate(
        self,
        symbol: Symbol,
        roles: List[Role],
        clustering_quality: float
    ) -> Metrics:
        """Calculate all metrics for a symbol."""

        # Role-based metrics
        role_count = len(roles)
        role_percentages = [r.percentage for r in roles]
        max_role_percentage = max(
            role_percentages) if role_percentages else 0.0

        pairwise_similarity = self.clusterer.calculate_pairwise_similarity(
            roles)

        # Intent alignment
        intent_desc = symbol.intent_anchor.docstring or "unknown intent"
        intent_alignment = self._calculate_intent_alignment(
            intent_desc,
            roles
        )

        original_role_pct, primary_is_original = self._find_original_role(
            intent_desc,
            roles
        )

        # Evolution metrics
        violated_assumptions = self._count_violated_assumptions(symbol)

        # Features (stub for now - requires deeper analysis)
        unused_features_pct = self._estimate_unused_features(symbol, roles)

        # Workarounds (stub - requires pattern detection)
        workaround_pct = 0.0  # TODO: Implement workaround detection

        # Alternatives (stub - requires documentation search)
        has_alternatives = False  # TODO: Implement alternative detection

        # Dependents (stub - requires external search)
        dependent_count = 0  # TODO: Implement dependent counting

        return Metrics(
            role_count=role_count,
            role_percentages=role_percentages,
            max_role_percentage=max_role_percentage,
            pairwise_role_similarity=pairwise_similarity,

            intent_alignment_percentage=intent_alignment,
            original_intent_role_percentage=original_role_pct,
            primary_role_is_original=primary_is_original,

            violated_assumptions_count=violated_assumptions,
            changes_in_5_years=0,  # Set by HistoryAnalyzer
            git_history_depth=0,    # Set by HistoryAnalyzer

            unused_original_features_percentage=unused_features_pct,

            workaround_percentage=workaround_pct,
            has_documented_alternatives=has_alternatives,
            dependent_count=dependent_count,

            call_site_count=len(symbol.call_contexts),
            intent_anchor_confidence=symbol.intent_anchor.confidence,
            clustering_quality=clustering_quality
        )

    def _calculate_intent_alignment(
        self,
        intent_description: str,
        roles: List[Role]
    ) -> float:
        """Calculate overall intent alignment across all roles."""
        if not roles:
            return 0.0

        # Weighted average by role percentage
        total_alignment = 0.0

        for role in roles:
            role_alignment = self.clusterer.calculate_intent_alignment(
                intent_description,
                role
            )
            total_alignment += role_alignment * role.percentage

        return total_alignment

    def _find_original_role(
        self,
        intent_description: str,
        roles: List[Role]
    ) -> tuple[float, bool]:
        """
        Find which role best matches original intent.

        Returns:
            (original_role_percentage, primary_role_is_original)
        """
        if not roles:
            return 0.0, False

        # Find role with highest alignment to intent
        best_alignment = 0.0
        best_role_idx = 0

        for i, role in enumerate(roles):
            alignment = self.clusterer.calculate_intent_alignment(
                intent_description,
                role
            )
            if alignment > best_alignment:
                best_alignment = alignment
                best_role_idx = i

        original_role_pct = roles[best_role_idx].percentage

        # Primary role is the one with highest percentage
        primary_role_idx = 0  # Already sorted by percentage
        primary_is_original = (best_role_idx == primary_role_idx)

        return original_role_pct, primary_is_original

    def _count_violated_assumptions(self, symbol: Symbol) -> int:
        """
        Count violated assumptions from original intent.

        Heuristics:
        - If source contains 'async def' but original doesn't → violated
        - If call contexts span very different modules → violated
        - If original is simple (<20 lines) but now complex → violated
        """
        violations = 0

        original_source = symbol.intent_anchor.source

        # Check async assumption
        original_is_async = 'async def' in original_source
        current_has_async = any(
            'await' in c.surrounding_code
            for c in symbol.call_contexts[:10]  # Sample
        )

        if current_has_async and not original_is_async:
            violations += 1

        # Check caller diversity (high diversity = multiple purposes)
        if len(symbol.call_contexts) > 10:
            unique_modules = set(c.caller_module for c in symbol.call_contexts)
            if len(unique_modules) > 20:
                violations += 1

        # Check complexity growth
        original_loc = symbol.intent_anchor.lines_of_code
        if original_loc < 10 and len(symbol.call_contexts) > 100:
            violations += 1

        return violations

    def _estimate_unused_features(
        self,
        symbol: Symbol,
        roles: List[Role]
    ) -> float:
        """
        Estimate percentage of original features that are unused.

        Heuristic:
        - Extract method calls from original source
        - Check if those methods appear in call contexts
        - Unused methods = unused features
        """
        # Simple heuristic: if primary role percentage is low,
        # assume features are unused proportionally
        if not roles:
            return 0.0

        primary_role_pct = roles[0].percentage

        # If primary role is <50%, assume significant features unused
        if primary_role_pct < 0.5:
            return 1.0 - primary_role_pct

        return 0.0
