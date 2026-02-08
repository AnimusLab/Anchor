from typing import List, Dict, Any
from anchor.core.registry import LanguageRegistry
from anchor.adapters.base import LanguageAdapter


class PolicyEngine:
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        self.config = config
        self.verbose = verbose
        # Flatten rules from all loaded policies
        self.rules = config.get("rules", [])

    def scan_directory(self, dir_path: str) -> Dict[str, Any]:
        import os
        import click
        all_violations = []
        
        total_files_encountered = 0
        ignored_files = 0
        total_dirs = 0
        
        # Collect files first for progress bar
        target_files = []
        for root, dirs, files in os.walk(dir_path):
            total_dirs += 1
            prune_list = ["build", "dist", "__pycache__", ".git", "node_modules", "target", "venv", ".venv", ".cache", "docs", "artifacts", ".anchor"]
            
            # Count directories being ignored
            for d in dirs:
                if d in prune_list:
                    # We don't recurse into these, so they are ignored
                    pass
            
            dirs[:] = [d for d in dirs if d not in prune_list]
            
            for file in files:
                total_files_encountered += 1
                if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.gz', '.map')):
                    ignored_files += 1
                    continue
                full_path = os.path.join(root, file)
                target_files.append(full_path)

        # Run Scan with Progress Bar
        scanned_count = 0
        with click.progressbar(target_files, label="⚓ Analyzing Security Posture", fill_char="█", empty_char="░") as bar:
            for full_path in bar:
                adapter = LanguageRegistry.get_adapter_for_file(full_path)
                if adapter:
                    try:
                        with open(full_path, "rb") as f:
                            content = f.read()
                            if len(content) > 2 * 1024 * 1024:
                                ignored_files += 1
                                continue
                            violations = self.scan_file(content, full_path, adapter)
                            all_violations.extend(violations)
                            scanned_count += 1
                    except Exception as e:
                        if self.verbose: click.echo(f"⚠️  Error scanning {full_path}: {e}")
                else:
                    ignored_files += 1

        return {
            "violations": all_violations,
            "metrics": {
                "scanned_files": scanned_count,
                "ignored_files": ignored_files,
                "total_files": total_files_encountered,
                "total_dirs": total_dirs
            }
        }

    def scan_file(self, content: bytes, file_path: str, adapter: LanguageAdapter) -> List[Dict]:
        violations = []
        try:
            tree = adapter.parse(content)
        except Exception as e:
            return []

        for rule in self.rules:
            if rule.get("severity") == "ignore":
                continue

            # --- MODE A: The "Rosetta Stone" (Smart AST) ---
            if "match" in rule:
                try:
                    match_config = rule["match"]
                    rule_type = match_config.get("type")
                    s_expr = ""

                    # Map High-Level Intent to Adapter Implementation
                    if rule_type == "function_call":
                        s_expr = adapter.build_dangerous_call_query([match_config.get("name")])
                    elif rule_type == "import":
                        s_expr = adapter.build_import_query([match_config.get("module")])
                    elif rule_type == "inheritance":
                        s_expr = adapter.build_inheritance_query([match_config.get("parent")])
                    else:
                        s_expr = rule.get("raw_query", "")

                    if s_expr:
                        if self.verbose:
                            import click
                            click.secho(f"    🔍 Running Query: {s_expr.strip()}", fg="white", dim=True)
                        
                        matches = self._execute_query(tree.root_node, adapter, s_expr)
                        if self.verbose:
                            click.secho(f"    🔢 Raw Matches: {len(matches)}", fg="white", dim=True)
                        
                        if self.verbose and not matches:
                             # Silence this usually, but helpful for debugging specific rule failures
                             # click.secho(f"    ℹ️  No AST matches for rule {rule['id']}", fg="white", dim=True)
                             pass

                        for match_data in matches:
                            if self.verbose:
                                caps = ", ".join([f"{k}:({v[0].type if isinstance(v, list) else v.type})" for k, v in match_data.items()])
                                click.secho(f"    🔬 Query Match: Captures=[{caps}]", fg="white", dim=True)

                            # --- VERIFICATION LAYER ---
                            # We verify that the captured nodes actually match the rule requirements.
                            # Adapters must use: @module_name, @func_name, or @parent_name
                            
                            is_valid = True
                            
                            # 1. Verify Module Name (Imports)
                            m_nodes = match_data.get("module_name") or match_data.get("import_name")
                            if m_nodes and rule_type == "import":
                                m_node = m_nodes[0]
                                m_text = m_node.text
                                if hasattr(m_text, "decode"): m_text = m_text.decode('utf-8', errors='ignore')
                                if m_text != match_config.get("module"):
                                    is_valid = False

                            # 2. Verify Function Name (Calls)
                            f_nodes = match_data.get("func_name")
                            if f_nodes and rule_type == "function_call":
                                f_node = f_nodes[0]
                                f_text = f_node.text
                                if hasattr(f_text, "decode"): f_text = f_text.decode('utf-8', errors='ignore')
                                
                                # Check against the exact name or list of names
                                expected_names = [match_config.get("name")] if "name" in match_config else []
                                if f_text not in expected_names:
                                    is_valid = False

                            if not is_valid:
                                if self.verbose: 
                                    click.echo(f"    ⏩ [FILTERED] False positive match for {rule['id']}")
                                continue

                            # 3. RECORD VIOLATION
                            v_raw = match_data.get("violation")
                            v_node = v_raw[0] if isinstance(v_raw, list) else v_raw
                            
                            violations.append({
                                "id": rule["id"],
                                "name": rule.get("name", "Unnamed Rule"),
                                "description": rule.get("description", "No description provided."),
                                "message": rule.get("message", "Policy Violation"),
                                "mitigation": rule.get("mitigation", "No mitigation provided."),
                                "file": file_path,
                                "line": v_node.start_point[0] + 1,
                                "severity": rule.get("severity", "error")
                            })
                except Exception as e:
                    if self.verbose:
                        import click
                        click.secho(f"    ⚠️  Rule Error ({rule.get('id', 'unknown')}): {e}", fg="yellow", dim=True)
                    pass

            # --- MODE B: Regex (Fallback) ---
            elif "pattern" in rule:
                found = self._check_regex(content.decode('utf-8', errors='ignore'), rule["pattern"])
                for line_num, match_text in found:
                    violations.append({
                        "id": rule["id"],
                        "name": rule.get("name", "Unnamed Rule"),
                        "message": rule.get("message"),
                        "mitigation": rule.get("mitigation", "No mitigation provided."),
                        "file": file_path,
                        "line": line_num,
                        "severity": rule.get("severity", "error")
                    })

        return violations

    def _execute_query(self, root_node, adapter: LanguageAdapter, s_expr: str) -> List[Dict]:
        """Standardized query execution returning all capture groups for verification."""
        import tree_sitter
        from tree_sitter import Query
        
        language = adapter.get_grammar()
        query_obj = None
        
        # 1. Try to create the query object
        try:
            # Modern language-bound query creation
            try:
                query_obj = language.query(s_expr)
            except:
                query_obj = Query(language, s_expr)
        except Exception as e:
            if self.verbose: print(f"    ❗ Query Syntax Error: {e}")
            return []

        results = []
        matches = []
        
        # 2. Try the "HYDRA" Execution strategy (Broad Spectrum)
        executed = False
        try:
            # Pattern A: query.matches(node) [Standard 0.20-0.21, and some 0.22]
            if not executed:
                try:
                    matches = query_obj.matches(root_node)
                    executed = True
                except: pass

            # Pattern B: QueryCursor(query_obj).matches(node) [Some 0.22+ bindings]
            if not executed:
                try:
                    from tree_sitter import QueryCursor
                    cursor = QueryCursor(query_obj)
                    matches = cursor.matches(root_node)
                    executed = True
                except: pass

            # Pattern C: QueryCursor().matches(query, node) [Other 0.22+ bindings]
            if not executed:
                try:
                    from tree_sitter import QueryCursor
                    cursor = QueryCursor()
                    matches = cursor.matches(query_obj, root_node)
                    executed = True
                except: pass

            # Pattern D: query.captures(node) fallback
            if not executed:
                try:
                    matches = query_obj.captures(root_node)
                    # If this worked, wrap it if it's raw captures
                    if matches and not hasattr(matches[0], 'captures'):
                        pseudo_results = {}
                        for node, c_name in matches:
                            name = query_obj.capture_name(c_name) if isinstance(c_name, int) else c_name
                            if name not in pseudo_results: pseudo_results[name] = []
                            pseudo_results[name].append(node)
                        if pseudo_results: results.append(pseudo_results)
                    return results # Exit early as captures() format is different
                except: pass

            # Process grouped matches if we found any with Pattern A/B/C
            for m in matches:
                match_data = {}
                captures = getattr(m, 'captures', None)
                if captures is not None:
                    if hasattr(captures, 'items'):
                        for name, nodes in captures.items():
                            name_str = query_obj.capture_name(name) if isinstance(name, int) else name
                            match_data[name_str] = nodes if isinstance(nodes, list) else [nodes]
                    else:
                        for entry in captures:
                            if isinstance(entry, (tuple, list)) and len(entry) == 2:
                                name_val, node = entry
                                name_str = query_obj.capture_name(name_val) if isinstance(name_val, int) else name_val
                                if name_str not in match_data: match_data[name_str] = []
                                match_data[name_str].append(node)
                else:
                    # Legacy fallback (m is a tuple)
                    if isinstance(m, (list, tuple)) and len(m) >= 2:
                        captures_dict = m[1]
                        for key, nodes in captures_dict.items():
                            name = query_obj.capture_name(key) if isinstance(key, int) else key
                            match_data[name] = nodes if isinstance(nodes, list) else [nodes]
                
                if match_data:
                    results.append(match_data)
        except Exception as e:
            if self.verbose: 
                print(f"    ❗ Execution Error: {e}")
                import traceback
                traceback.print_exc()
        
        return results

    def _check_regex(self, content: str, pattern: str) -> List[tuple]:
        import re
        results = []
        lines = content.split('\n')
        # Limit regex lines for performance
        for i, line in enumerate(lines[:5000]): 
            if re.search(pattern, line):
                results.append((i + 1, line.strip()))
        return results
