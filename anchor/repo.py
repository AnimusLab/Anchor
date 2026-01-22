"""Repository analysis orchestration."""

from pathlib import Path
from typing import Optional

from .symbols import Symbol, AuditResult
from .history import HistoryAnalyzer
from .contexts import ContextExtractor, RoleClusterer
from .metrics import MetricsCalculator
from .verdicts import DriftDetector


class RepositoryAnalyzer:
    """
    Orchestrates the complete audit process for a repository.

    Workflow:
    1. Extract intent anchor from git history
    2. Extract call contexts from codebase
    3. Cluster contexts into semantic roles
    4. Calculate metrics
    5. Detect drift
    6. Generate audit result
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

        # Initialize components
        self.history = HistoryAnalyzer(str(self.repo_path))
        self.context_extractor = ContextExtractor(str(self.repo_path))
        self.clusterer = RoleClusterer()
        self.metrics_calculator = MetricsCalculator()
        self.detector = DriftDetector()

    def audit_symbol(
        self,
        file_path: str,
        symbol_name: str,
        symbol_type: str = "function",
        include_tests: bool = True
    ) -> Optional[AuditResult]:
        """
        Perform complete audit of a single symbol.

        Args:
            file_path: Relative path to file containing symbol
            symbol_name: Name of function/class to audit
            symbol_type: 'function' or 'class'
            include_tests: Include test files in call context analysis

        Returns:
            AuditResult or None if insufficient data
        """

        print(f"Auditing {symbol_name} from {file_path}...")

        # Step 1: Extract intent anchor
        print("  [1/5] Extracting intent anchor...")
        intent_anchor = self.history.find_intent_anchor(file_path, symbol_name)

        if not intent_anchor:
            print(f"  ✗ Could not find intent anchor for {symbol_name}")
            return None

        print(f"  ✓ Found anchor at commit {intent_anchor.commit_sha[:8]}")

        # Step 2: Extract call contexts
        print("  [2/5] Extracting call contexts...")
        call_contexts = self.context_extractor.extract_call_contexts(
            symbol_name,
            include_tests=False
        )

        if len(call_contexts) < 10:
            print(
                f"  ✗ Insufficient call contexts ({len(call_contexts)} < 10)")
            return None

        print(f"  ✓ Found {len(call_contexts)} call contexts")

        # Create symbol
        symbol = Symbol(
            name=symbol_name,
            type=symbol_type,
            file_path=file_path,
            repo_path=str(self.repo_path),
            intent_anchor=intent_anchor,
            call_contexts=call_contexts
        )

        # Step 3: Cluster roles
        print("  [3/5] Clustering semantic roles...")
        roles, clustering_quality = self.clusterer.cluster_roles(call_contexts)
        print(f"  ✓ Identified {len(roles)} semantic roles")

        # Step 4: Calculate metrics
        print("  [4/5] Calculating metrics...")
        metrics = self.metrics_calculator.calculate(
            symbol,
            roles,
            clustering_quality
        )

        # Add history-based metrics
        metrics.changes_in_5_years = self.history.count_meaningful_changes(
            file_path,
            symbol_name,
            years=5
        )
        metrics.git_history_depth = self.history.get_history_depth(file_path)

        print(f"  ✓ Calculated {len(roles)} roles, "
              f"{metrics.intent_alignment_percentage:.0%} alignment")

        # Step 5: Detect drift
        print("  [5/5] Detecting drift...")
        verdict, confidence = self.detector.detect(symbol, roles, metrics)
        print(f"  ✓ Verdict: {verdict} (confidence: {confidence})")

        # Build evidence
        evidence = self._build_evidence(symbol, roles, metrics)

        return AuditResult(
            symbol=symbol,
            roles=roles,
            metrics=metrics,
            verdict=verdict,
            confidence=confidence,
            evidence=evidence
        )

    def _build_evidence(self, symbol, roles, metrics) -> dict:
        """Build evidence dictionary for audit result."""
        return {
            "role_count": metrics.role_count,
            "intent_alignment": f"{metrics.intent_alignment_percentage:.1%}",
            "original_role_percentage": f"{metrics.original_intent_role_percentage:.1%}",
            "call_site_count": len(symbol.call_contexts),
            "changes_5y": metrics.changes_in_5_years,
            "violated_assumptions": metrics.violated_assumptions_count,
            "clustering_quality": f"{metrics.clustering_quality:.2f}",
        }
