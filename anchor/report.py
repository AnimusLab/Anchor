"""Output formatting for Anchor verdicts."""

from typing import List
from .symbols import AuditResult, Role


class ReportFormatter:
    """
    Format audit results in Anchor's opinionated style.

    No charts. No scores. No gamification.
    Only discrete verdicts with evidence.
    """

    def format(self, result: AuditResult) -> str:
        """Format a complete audit result."""

        # Choose symbol marker
        if result.verdict == "aligned":
            marker = "✓"
        else:
            marker = "⚠"

        # Build report sections
        output = []

        # Header
        output.append(f"{marker} {result.symbol.name}")
        output.append("")

        # Intent anchor
        output.append("Anchored to:")
        intent_desc = result.symbol.intent_anchor.docstring or "No docstring"
        output.append(f"  {intent_desc}")
        output.append(f"  (commit {result.symbol.intent_anchor.commit_sha[:8]}, "
                      f"{result.symbol.intent_anchor.commit_date.date()})")
        output.append("")

        # Current roles
        if result.roles:
            output.append("Current roles:")
            for role in result.roles:
                output.append(
                    f"  - {role.description} ({role.percentage:.1%})")
            output.append("")

        # Verdict
        output.append(f"Verdict: {result.verdict}")
        output.append(f"Confidence: {result.confidence}")
        output.append("")

        # Rationale
        output.append("Rationale:")
        rationale = self._generate_rationale(result)
        output.append(f"  {rationale}")
        output.append("")

        # Evidence
        if result.evidence:
            output.append("Evidence:")
            for key, value in result.evidence.items():
                output.append(f"  - {key}: {value}")
            output.append("")

        return "\n".join(output)

    def _generate_rationale(self, result: AuditResult) -> str:
        """Generate verdict-specific rationale."""

        if result.verdict == "aligned":
            return self._rationale_aligned(result)
        elif result.verdict == "semantic_overload":
            return self._rationale_semantic_overload(result)
        elif result.verdict == "intent_violation":
            return self._rationale_intent_violation(result)
        elif result.verdict == "dependency_inertia":
            return self._rationale_dependency_inertia(result)
        else:
            return "Insufficient data for confident verdict."

    def _rationale_aligned(self, result: AuditResult) -> str:
        """Rationale for aligned verdict."""
        intent = result.symbol.intent_anchor.docstring or "original intent"
        alignment = result.metrics.intent_alignment_percentage

        return (
            f"{result.symbol.name} performs {intent} across all observed "
            f"usage contexts ({alignment:.0%} intent alignment). "
            f"The implementation and behavior match the original design. "
            f"No drift detected."
        )

    def _rationale_semantic_overload(self, result: AuditResult) -> str:
        """Rationale for semantic_overload verdict."""
        role_count = result.metrics.role_count
        roles_desc = ", ".join(r.description for r in result.roles[:3])

        return (
            f"{result.symbol.name} now serves {role_count} distinct roles: "
            f"{roles_desc}. While each role relates to the original domain, "
            f"their coexistence within a single abstraction exceeds the "
            f"responsibility implied by the original design."
        )

    def _rationale_intent_violation(self, result: AuditResult) -> str:
        """Rationale for intent_violation verdict."""
        intent = result.symbol.intent_anchor.docstring or "original intent"
        primary_pct = result.metrics.max_role_percentage
        original_pct = result.metrics.original_intent_role_percentage

        primary_role = result.roles[0] if result.roles else None
        primary_desc = primary_role.description if primary_role else "new usage"

        return (
            f"{result.symbol.name} was designed for {intent}. "
            f"Current usage is dominated by {primary_desc} ({primary_pct:.0%}) "
            f"while original usage represents only {original_pct:.0%}. "
            f"This represents a primary usage shift that violates the symbol's "
            f"original intent."
        )

    def _rationale_dependency_inertia(self, result: AuditResult) -> str:
        """Rationale for dependency_inertia verdict."""
        changes = result.metrics.changes_in_5_years
        workarounds = result.metrics.workaround_percentage

        return (
            f"{result.symbol.name} has remained structurally unchanged "
            f"({changes} meaningful changes in 5 years) despite known limitations. "
            f"Approximately {workarounds:.0%} of usage involves workarounds. "
            f"Alternative abstractions exist but the original persists due to "
            f"backward compatibility concerns."
        )

    def format_summary(self, results: List[AuditResult]) -> str:
        """Format a summary of multiple audit results."""
        output = []

        output.append("=" * 80)
        output.append("ANCHOR AUDIT SUMMARY")
        output.append("=" * 80)
        output.append("")

        # Count verdicts
        verdicts = {}
        for result in results:
            verdicts[result.verdict] = verdicts.get(result.verdict, 0) + 1

        output.append(f"Total symbols audited: {len(results)}")
        output.append("")
        output.append("Verdict distribution:")
        for verdict, count in verdicts.items():
            pct = count / len(results) * 100
            output.append(f"  {verdict}: {count} ({pct:.0f}%)")

        output.append("")
        output.append("=" * 80)
        output.append("")

        # Individual results
        for result in results:
            output.append(self.format(result))
            output.append("-" * 80)
            output.append("")

        return "\n".join(output)
