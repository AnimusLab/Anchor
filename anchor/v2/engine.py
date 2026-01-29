import os
from typing import List, Dict, Any
# 1. Import all required classes for v0.25+
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython


class PolicyEngine:
    def __init__(self):
        self.parsers = {}
        self.languages = {}

        try:
            # Load Language & Parser
            py_lang = Language(tspython.language())
            self.languages["python"] = py_lang
            self.parsers["python"] = Parser(py_lang)

        except Exception as e:
            print(f"[ERROR] Could not load Tree-sitter Python: {e}")

        # 2. The Registry (Using Robust Structure-Based Queries)
        self.query_registry = {
            "RI-24": {
                "language": "python",
                "severity": "error",
                "message": "Direct network access is forbidden. Use MCP Client.",
                "query": """
                (import_statement 
                    (dotted_name) @mod_name
                    (#match? @mod_name "^(requests|urllib|socket|http)"))
                
                (import_from_statement 
                    (dotted_name) @mod_name
                    (#match? @mod_name "^(requests|urllib|socket|http)"))
                """
            },
            "AI-20": {
                "language": "python",
                "severity": "error",
                "message": "MCP Client usage requires explicit 'quantgrid' import.",
                "query": """
                (call 
                    function: (attribute object: (identifier) @obj attribute: (identifier) @meth) 
                    (#match? @meth "^(get|post|request)$"))
                """
            }
        }

    def scan_file(self, content: str, file_path: str, policy: Dict[str, Any]) -> List[Dict]:
        violations = []
        active_rules = policy.get("active_rules", {})

        if not file_path.endswith(".py") or "python" not in self.parsers:
            return []

        # 1. Parse
        parser = self.parsers["python"]
        tree = parser.parse(bytes(content, "utf8"))

        # 2. Query Loop
        for rule_id, rule_state in active_rules.items():
            if rule_state == "off":
                continue

            rule_def = self.query_registry.get(rule_id)
            if not rule_def or rule_def["language"] != "python":
                continue

            try:
                # NEW API v0.25+:
                # A. Create Query
                query_obj = Query(self.languages["python"], rule_def["query"])

                # B. Create Cursor WITH Query (Required!)
                cursor = QueryCursor(query_obj)

                # C. Execute Matches
                # Returns an iterator of TUPLES: (match_id, captures_dict)
                matches = cursor.matches(tree.root_node)

                for match_id, captures_dict in matches:
                    # captures_dict maps 'capture_name' -> list[Node]
                    for capture_name, nodes in captures_dict.items():

                        # Normalize to list (just in case)
                        if not isinstance(nodes, list):
                            nodes = [nodes]

                        for node in nodes:
                            violations.append({
                                "rule_id": rule_id,
                                "file": file_path,
                                "line": node.start_point[0] + 1,
                                "message": rule_def["message"],
                                "severity": rule_state,
                                "code_snippet": content[node.start_byte:node.end_byte]
                            })

            except Exception as e:
                print(f"[WARN] Query failed for {rule_id}: {e}")

        return violations
