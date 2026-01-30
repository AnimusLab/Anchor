import re
from typing import List, Dict, Any
from tree_sitter import Language, Parser
from anchor.core.parser import get_parser, get_language, Query, QueryCursor


class QueryGenerator:
    """
    Translates 'Poem' syntax (Human YAML) into Tree-sitter S-expressions (Machine Code).
    """
    @staticmethod
    def generate(rule: Dict[str, Any]) -> str:
        # 1. SIMPLE FUNCTION BAN ("I want to ban specific functions")
        #    Usage in YAML: { type: "function_call", name: "eval" }
        if rule.get("type") == "function_call":
            target = rule.get("name")
            return f"""
            (call
                function: (identifier) @func_name
                (#match? @func_name "^{target}$")
            )
            """

        # 2. SIMPLE IMPORT BAN ("I want to ban specific libraries")
        #    Usage in YAML: { type: "import", module: "requests" }
        if rule.get("type") == "import":
            target = rule.get("module")
            return f"""
            (import_statement
                name: (dotted_name) @import_name
                (#match? @import_name "^{target}$")
            )
            """

        # 3. CLASS INHERITANCE BAN ("I want to ban inheriting from Thread")
        #    Usage in YAML: { type: "inheritance", parent: "Thread" }
        if rule.get("type") == "inheritance":
            target = rule.get("parent")
            return f"""
            (class_definition
                superclasses: (argument_list 
                    (identifier) @parent_name
                    (#match? @parent_name "^{target}$")
                )
            )
            """

        # Fallback: Power users can still write raw S-expressions
        return rule.get("raw_query", "")


class PolicyEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Flatten rules from all loaded policies
        self.rules = config.get("rules", [])
        self.parser = get_parser()
        self.language = get_language()

    def scan_directory(self, dir_path: str) -> Dict[str, Any]:
        import os
        all_violations = []

        for root, _, files in os.walk(dir_path):
            if any(x in root for x in ["build", "dist", "__pycache__", ".git"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            violations = self.scan_file(content, full_path)
                            all_violations.extend(violations)
                    except Exception:
                        pass

        return {"violations": all_violations}

    def scan_file(self, content: str, file_path: str) -> List[Dict]:
        violations = []
        tree = self.parser.parse(bytes(content, "utf8"))

        for rule in self.rules:
            if rule.get("severity") == "ignore":
                continue

            # --- MODE A: The "Poem" (Smart AST) ---
            if "match" in rule:
                try:
                    # Translate the "Poem" into S-expression
                    s_expr = QueryGenerator.generate(rule["match"])

                    if s_expr:
                        query_obj = Query(self.language, s_expr)
                        cursor = QueryCursor(query_obj)
                        matches = cursor.matches(tree.root_node)

                        for match in matches:
                            # Just grab the first captured node for location
                            for _, nodes in match[1].items():
                                if not isinstance(nodes, list):
                                    nodes = [nodes]
                                node = nodes[0]
                                violations.append({
                                    "id": rule["id"],
                                    "message": rule.get("message", "Policy Violation"),
                                    "file": file_path,
                                    "line": node.start_point[0] + 1,
                                    "severity": rule.get("severity", "error")
                                })
                except Exception as e:
                    print(f"⚠️ Rule {rule['id']} error: {e}")

            # --- MODE B: Regex (Legacy) ---
            elif "pattern" in rule:
                found = self._check_regex(content, rule["pattern"])
                for line_num, match_text in found:
                    violations.append({
                        "id": rule["id"],
                        "message": rule.get("message"),
                        "file": file_path,
                        "line": line_num,
                        "severity": rule.get("severity", "error")
                    })

        return violations

    def _check_regex(self, content: str, pattern: str) -> List[tuple]:
        results = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                results.append((i + 1, line.strip()))
        return results
