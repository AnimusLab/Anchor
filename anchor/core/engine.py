from typing import List, Dict, Any
from anchor.core.registry import LanguageRegistry
from anchor.adapters.base import LanguageAdapter


class PolicyEngine:
    def __init__(self, config: Dict[str, Any] = None, verbose: bool = False):
        self.config = config or {}
        self.verbose = verbose
        # Flatten rules from all loaded policies
        self.rules = config.get("rules", []) if config else []
        self.allow_suppressions = self.config.get("allow_suppressions", True)

    def _get_suppression_author(self, file_path: str, line_num: int) -> str:
        """Internal discovery of who authorized a security suppression."""
        import subprocess
        try:
            # Normalize path for git on Windows
            norm_path = file_path.replace("\\", "/")
            cmd = ["git", "blame", "-L", f"{line_num},{line_num}", "--porcelain", norm_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # anchor: ignore ANC-018
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("author "):
                        return line[7:].strip()
        except:
            pass
        return "Unknown"

    def scan_directory(self, dir_path: str, exclude_paths: List[str] = None,
                        cage=None) -> Dict[str, Any]:
        import os
        import click
        from pathlib import Path
        all_violations = []
        
        exclude_paths = exclude_paths or []
        # Support both absolute and relative path matches
        # Load from config if present
        config_ignores = self.config.get("ignore_paths", []) if self.config else []
        combined_excludes = set(exclude_paths + config_ignores)

        total_files_encountered = 0
        ignored_files = 0
        total_dirs = 0
        
        # Collect files first for progress bar
        target_files = []
        
        # Handle single file targets
        if os.path.isfile(dir_path):
            if not dir_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.gz', '.map')):
                target_files.append(dir_path)
                total_files_encountered = 1
        else:
            for root, dirs, files in os.walk(dir_path):
                total_dirs += 1
                prune_list = ["build", "dist", "__pycache__", ".git", "node_modules", "target", "venv", ".venv", ".cache", "docs", "artifacts", ".anchor"]
                
                # 1. Prune hardcoded defaults
                dirs[:] = [d for d in dirs if d not in prune_list]

                # 2. Prune user-defined exclusions
                if combined_excludes:
                    # Check if current root or any child dir matches an exclusion
                    rel_root = os.path.relpath(root, dir_path)
                    
                    # Check dirs for dynamic pruning
                    new_dirs = []
                    for d in dirs:
                        d_rel_path = os.path.normpath(os.path.join(rel_root, d))
                        is_excluded = False
                        for pattern in combined_excludes:
                            if pattern in d_rel_path or d_rel_path.startswith(pattern):
                                is_excluded = True
                                break
                        if not is_excluded:
                            new_dirs.append(d)
                    dirs[:] = new_dirs

                for file in files:
                    total_files_encountered += 1
                    if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.gz', '.map')):
                        ignored_files += 1
                        continue
                    full_path = os.path.join(root, file)
                    target_files.append(full_path)

        scanned_count = 0
        all_suppressed   = []
        behavioral_hits  = []

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
                            results = self.scan_file(content, full_path, adapter)
                            all_violations.extend(results.get("violations", []))
                            all_suppressed.extend(results.get("suppressed", []))
                            scanned_count += 1

                            # --- Diamond Cage: behavioral scan on Python files ---
                            if cage and full_path.endswith(".py"):
                                context_dir = str(Path(full_path).parent)
                                cage_result = cage.behavioral_scan(
                                    target_file=full_path,
                                    context_dir=context_dir,
                                )
                                behavioral_hits.extend(
                                    cage_result.get("behavioral_violations", [])
                                )
                    except Exception as e:
                        if self.verbose: click.echo(f"⚠️  Error scanning {full_path}: {e}")
                else:
                    ignored_files += 1

        return {
            "violations":          all_violations,
            "suppressed":          all_suppressed,
            "behavioral_findings": behavioral_hits,
            "metrics": {
                "scanned_files": scanned_count,
                "ignored_files": ignored_files,
                "total_files":   total_files_encountered,
                "total_dirs":    total_dirs,
                "cage_active":   cage is not None and cage.is_installed(),
            }
        }

    def scan_file(self, content: bytes, file_path: str, adapter: LanguageAdapter) -> Dict[str, List[Dict]]:
        violations = []
        suppressed = []
        try:
            tree = adapter.parse(content)
        except Exception as e:
            return {"violations": [], "suppressed": []}

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
                    elif rule_type == "regex":
                        # Nested regex support inside 'match' block
                        pattern = match_config.get("pattern")
                        found = self._check_regex(content.decode('utf-8', errors='ignore'), pattern, rule_id=rule.get("id"))
                        for line_num, match_text in found:
                            is_suppressed = False
                            if self.allow_suppressions:
                                if f"# anchor: ignore {rule.get('id')}" in match_text or "# anchor: ignore-all" in match_text:
                                    author = self._get_suppression_author(file_path, line_num)
                                    suppressed.append({
                                        "id": rule["id"], "name": rule.get("name"), "file": file_path, "line": line_num, "author": author, "severity": rule.get("severity", "error")
                                    })
                                    is_suppressed = True
                            if not is_suppressed:
                                violations.append({
                                    "id": rule["id"], "name": rule.get("name"), "description": rule.get("description"), "message": rule.get("message"), "mitigation": rule.get("mitigation"), "file": file_path, "line": line_num, "severity": rule.get("severity", "error")
                                })
                        continue # Regex handled, skip AST logic
                    else:
                        s_expr = rule.get("raw_query", "")

                    if s_expr:
                        if self.verbose:
                            import click
                            click.secho(f"    🔍 Running Query: {s_expr.strip()}", fg="white", dim=True)
                        
                        matches = self._execute_query(tree.root_node, adapter, s_expr)
                        if self.verbose:
                            click.secho(f"    🔢 Raw Matches: {len(matches)}", fg="white", dim=True)

                        for match_data in matches:
                            # 1. Selection Layer: Find the violation node
                            v_nodes = match_data.get("violation")
                            if not v_nodes:
                                v_nodes = list(match_data.values())[0] if match_data else []
                            
                            if not v_nodes: continue
                            v_node = v_nodes[0]
                            
                            is_valid = True
                            
                            # 1. Verify Module Name (Imports)
                            m_nodes = match_data.get("import_name")
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

                            # 3. Verify Parent Name (Inheritance)
                            p_nodes = match_data.get("parent_name")
                            if p_nodes and rule_type == "inheritance":
                                p_node = p_nodes[0]
                                p_text = p_node.text
                                if hasattr(p_text, "decode"): p_text = p_text.decode('utf-8', errors='ignore')
                                if p_text != match_config.get("parent"):
                                    is_valid = False

                            if not is_valid:
                                if self.verbose: 
                                    click.echo(f"    ⏩ [FILTERED] False positive match for {rule['id']}")
                                continue

                            line_num = v_node.start_point[0] + 1
                            
                            # --- IN-LINE SUPPRESSION CHECK ---
                            is_suppressed = False
                            if self.allow_suppressions:
                                try:
                                    lines = content.decode('utf-8', errors='ignore').splitlines()
                                    # Check current line and NEXT line for suppression (common in 'with open' blocks)
                                    search_lines = []
                                    if 0 < line_num <= len(lines):
                                        search_lines.append(lines[line_num - 1])
                                    if 0 < (line_num + 1) <= len(lines):
                                        search_lines.append(lines[line_num])
                                    
                                    for l_content in search_lines:
                                        if f"# anchor: ignore {rule['id']}" in l_content or "# anchor: ignore-all" in l_content:
                                            author = self._get_suppression_author(file_path, line_num)
                                            if self.verbose: 
                                                import click
                                                click.echo(f"    🙈 [SUPPRESSED] Rule {rule['id']} at line {line_num} (Author: {author})")
                                            
                                            suppressed.append({
                                                "id": rule["id"],
                                                "name": rule.get("name", "Unnamed Rule"),
                                                "file": file_path,
                                                "line": line_num,
                                                "author": author,
                                                "severity": rule.get("severity", "error")
                                            })
                                            is_suppressed = True
                                            break
                                except: pass
                            
                            if is_suppressed:
                                continue

                            violations.append({
                                "id": rule["id"],
                                "name": rule.get("name", "Unnamed Rule"),
                                "description": rule.get("description", "No description provided."),
                                "message": rule.get("message", "Policy Violation"),
                                "mitigation": rule.get("mitigation", "No mitigation provided."),
                                "file": file_path,
                                "line": line_num,
                                "severity": rule.get("severity", "error")
                            })
                except Exception as e:
                    if self.verbose:
                        import click
                        click.secho(f"    ⚠️  Rule Error ({rule.get('id', 'unknown')}): {e}", fg="yellow", dim=True)
                    pass

            # --- MODE B: Regex (Fallback) ---
            elif "pattern" in rule:
                found = self._check_regex(content.decode('utf-8', errors='ignore'), rule["pattern"], rule_id=rule.get("id"))
                for line_num, match_text in found:
                    is_suppressed = False
                    if self.allow_suppressions:
                        if f"# anchor: ignore {rule.get('id')}" in match_text or "# anchor: ignore-all" in match_text:
                            author = self._get_suppression_author(file_path, line_num)
                            suppressed.append({
                                "id": rule["id"],
                                "name": rule.get("name", "Unnamed Rule"),
                                "file": file_path,
                                "line": line_num,
                                "author": author,
                                "severity": rule.get("severity", "error")
                            })
                            is_suppressed = True
                    
                    if is_suppressed: continue

                    violations.append({
                        "id": rule["id"],
                        "name": rule.get("name", "Unnamed Rule"),
                        "message": rule.get("message"),
                        "mitigation": rule.get("mitigation", "No mitigation provided."),
                        "file": file_path,
                        "line": line_num,
                        "severity": rule.get("severity", "error")
                    })

        return {"violations": violations, "suppressed": suppressed}

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

    def _check_regex(self, content: str, pattern: str, rule_id: str = None) -> List[tuple]:
        import re
        results = []
        if not pattern:
            return results
        lines = content.split('\n')
        for i, line in enumerate(lines[:5000]): 
            if re.search(pattern, line):
                results.append((i + 1, line.strip()))
        return results

    def _get_suppression_author(self, file_path: str, line_num: int) -> str:
        """Use git blame to identify who authorized the suppression."""
        import subprocess
        import os
        
        try:
            # 1. Get the absolute path to ensure git finds the file
            abs_path = os.path.abspath(file_path)
            
            # 2. Run git blame for the specific line
            # -L <start>,<end> : only blame the specified line
            # --porcelain      : machine-readable format
            cmd = ["git", "blame", "-L", f"{line_num},{line_num}", "--porcelain", abs_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # anchor: ignore ANC-018
            
            # 3. Parse author from porcelain output
            for line in result.stdout.splitlines():
                if line.startswith("author "):
                    return line.replace("author ", "").strip()
        except Exception:
            # Fallback for non-git files or errors
            pass
            
        return "Not Committed Yet (Local)"
