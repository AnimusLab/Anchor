"""Call context extraction and semantic role clustering."""

import ast
import numpy as np
from pathlib import Path
from typing import List, Tuple
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer

from .symbols import CallContext, Role


class ContextExtractor:
    """Extract call contexts from a codebase."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def extract_call_contexts(
        self,
        symbol_name: str,
        max_contexts: int = 100,
        include_tests: bool = True
    ) -> List[CallContext]:
        """
        Find all call sites for a symbol in the repository.

        Extracts ~20 lines of surrounding code for each call.

        Args:
            symbol_name: Name of the symbol to find
            max_contexts: Maximum number of contexts to extract
            include_tests: Whether to include test files (default: True)
        """
        contexts = []

        # Search all Python files
        for py_file in self.repo_path.rglob("*.py"):
            # Skip test files if requested
            if not include_tests and self._is_test_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_contexts = self._extract_from_file(
                    content,
                    symbol_name,
                    str(py_file.relative_to(self.repo_path))
                )
                contexts.extend(file_contexts)

                if len(contexts) >= max_contexts:
                    break

            except (UnicodeDecodeError, PermissionError):
                continue

        return contexts[:max_contexts]

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        path_str = str(file_path).lower()
        return (
            'test' in path_str or
            'tests' in path_str or
            file_path.name.startswith('test_')
        )

    def _extract_from_file(
        self,
        content: str,
        symbol_name: str,
        file_path: str
    ) -> List[CallContext]:
        """Extract call contexts from a single file."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        contexts = []
        lines = content.split('\n')

        # Find all function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if this is a call to our symbol
                if self._is_call_to_symbol(node, symbol_name):
                    # Get surrounding context
                    context = self._extract_surrounding_code(
                        lines,
                        node.lineno,
                        context_lines=10
                    )

                    # Get caller information
                    caller_func = self._find_enclosing_function(tree, node)
                    caller_module = file_path.replace(
                        '/', '.').replace('\\', '.').replace('.py', '')

                    contexts.append(CallContext(
                        caller_module=caller_module,
                        caller_function=caller_func or '<module>',
                        surrounding_code=context,
                        line_number=node.lineno,
                        file_path=file_path
                    ))

        return contexts

    def _is_call_to_symbol(self, node: ast.Call, symbol_name: str) -> bool:
        """Check if a Call node calls the target symbol."""
        # Direct call: symbol_name()
        if isinstance(node.func, ast.Name) and node.func.id == symbol_name:
            return True

        # Attribute call: obj.symbol_name()
        if isinstance(node.func, ast.Attribute) and node.func.attr == symbol_name:
            return True

        return False

    def _extract_surrounding_code(
        self,
        lines: List[str],
        line_number: int,
        context_lines: int = 10
    ) -> str:
        """Extract surrounding code around a line."""
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        return '\n'.join(lines[start:end])

    def _find_enclosing_function(self, tree: ast.AST, target_node: ast.AST) -> str:
        """Find the function containing a node."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if target is inside this function
                if hasattr(node, 'body'):
                    for child in ast.walk(node):
                        if child == target_node:
                            return node.name
        return None


class RoleClusterer:
    """Cluster call contexts into semantic roles."""

    def __init__(self):
        # Use lightweight sentence transformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def cluster_roles(
        self,
        contexts: List[CallContext],
        eps: float = 0.3,
        min_samples: int = 5
    ) -> Tuple[List[Role], float]:
        """
        Cluster call contexts into semantic roles using DBSCAN.

        Returns:
            (roles, clustering_quality)
        """
        if len(contexts) < min_samples:
            # Not enough data for clustering
            return [Role(
                contexts=contexts,
                percentage=1.0,
                description="insufficient_data",
                embedding_centroid=None
            )], 0.0

        # Embed contexts
        embeddings = self._embed_contexts(contexts)

        # Cluster
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(embeddings)

        # Assess quality
        quality = self._assess_clustering_quality(
            embeddings, clustering.labels_)

        # Build roles
        roles = []
        unique_labels = set(clustering.labels_)

        for label in unique_labels:
            if label == -1:  # Noise cluster
                continue

            mask = clustering.labels_ == label
            role_contexts = [c for c, m in zip(contexts, mask) if m]
            percentage = sum(mask) / len(contexts)

            # Get centroid for similarity calculations
            role_embeddings = embeddings[mask]
            centroid = np.mean(role_embeddings, axis=0).tolist()

            roles.append(Role(
                contexts=role_contexts,
                percentage=percentage,
                description=self._describe_role(role_contexts),
                embedding_centroid=centroid
            ))

        # If no clusters found (all noise), treat as single role
        if len(roles) == 0:
            # Calculate centroid of all embeddings
            centroid = np.mean(embeddings, axis=0).tolist()

            roles = [Role(
                contexts=contexts,
                percentage=1.0,
                description=self._describe_role(contexts),
                embedding_centroid=centroid
            )]
            quality = 1.0  # High confidence - all contexts are similar

        # Sort by percentage (descending)
        roles.sort(key=lambda r: r.percentage, reverse=True)

        return roles, quality

    def calculate_pairwise_similarity(self, roles: List[Role]) -> List[float]:
        """Calculate pairwise cosine similarity between roles."""
        if len(roles) < 2:
            return []

        similarities = []

        for i in range(len(roles)):
            for j in range(i + 1, len(roles)):
                if roles[i].embedding_centroid and roles[j].embedding_centroid:
                    sim = self._cosine_similarity(
                        roles[i].embedding_centroid,
                        roles[j].embedding_centroid
                    )
                    similarities.append(sim)

        return similarities

    def calculate_intent_alignment(
        self,
        intent_description: str,
        role: Role
    ) -> float:
        """Calculate how well a role aligns with original intent."""
        # Embed intent
        intent_embedding = self.model.encode([intent_description])[0]

        # Compare with role centroid
        if role.embedding_centroid:
            return self._cosine_similarity(
                intent_embedding.tolist(),
                role.embedding_centroid
            )

        return 0.0

    def _embed_contexts(self, contexts: List[CallContext]) -> np.ndarray:
        """Embed call contexts using sentence transformer."""
        texts = [c.surrounding_code for c in contexts]
        return self.model.encode(texts)

    def _assess_clustering_quality(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> float:
        """Assess clustering quality using silhouette score."""
        # Need at least 2 clusters for silhouette score
        unique_labels = set(labels)
        if len(unique_labels) < 2:
            return 0.0

        # Filter out noise points (-1 label)
        mask = labels != -1
        if sum(mask) < 2:
            return 0.0

        try:
            score = silhouette_score(embeddings[mask], labels[mask])
            # Normalize to 0-1 range (silhouette is -1 to 1)
            return (score + 1) / 2
        except Exception:
            return 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _describe_role(self, contexts: List[CallContext]) -> str:
        """Generate a brief description of a role from its contexts."""
        # Simple heuristic: use most common caller module
        modules = [c.caller_module for c in contexts]
        most_common = max(set(modules), key=modules.count)
        return f"Role in {most_common}"
