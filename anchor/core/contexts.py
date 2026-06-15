import ast
import os
from typing import List, Set
from anchor.core.models import CallContext


class UsageAnalyzer(ast.NodeVisitor):
    def __init__(self, target_name: str, file_path: str):
        self.target_name = target_name
        self.file_path = file_path
        self.contexts: List[CallContext] = []

        # Tracking scope for variable usage
        self.current_scope_vars: Set[str] = set()
        self.current_context: CallContext = None

    def visit_ClassDef(self, node):
        # 1. Check Inheritance
        is_subclass = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == self.target_name:
                is_subclass = True
            elif isinstance(base, ast.Attribute) and base.attr == self.target_name:
                is_subclass = True

        if is_subclass:
            self._add_context(node, "Inheritance")

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Reset scope for new function
        old_vars = self.current_scope_vars.copy()
        self.current_scope_vars = set()
        self.generic_visit(node)
        self.current_scope_vars = old_vars

    def visit_Assign(self, node):
        # 2. Track Instantiations: form = Form(...)
        if isinstance(node.value, ast.Call):
            is_target = False
            if isinstance(node.value.func, ast.Name) and node.value.func.id == self.target_name:
                is_target = True
            elif isinstance(node.value.func, ast.Attribute) and node.value.func.attr == self.target_name:
                is_target = True

            if is_target:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.current_scope_vars.add(target.id)
                        self.current_context = self._add_context(
                            node, "Instantiation")

        self.generic_visit(node)

    def visit_Call(self, node):
        # 3. Track Function Calls: authenticate(...)
        if isinstance(node.func, ast.Name) and node.func.id == self.target_name:
            self._add_context(node, "Direct Call")
        elif isinstance(node.func, ast.Attribute) and node.func.attr == self.target_name:
            self._add_context(node, "Direct Call")

        # 4. Track Method Calls on tracked variables
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            method_name = node.func.attr

            if var_name in self.current_scope_vars and self.current_context:
                if method_name in {'as_p', 'as_table', 'as_ul', 'render'}:
                    self.current_context.uses_html_methods = True
                self.current_context.uses_validation_only = True

        self.generic_visit(node)

    def _add_context(self, node, usage_type: str) -> CallContext:
        ctx = CallContext(
            file_path=self.file_path,
            line_number=node.lineno,
            caller_symbol=usage_type,
            code_snippet=f"{usage_type} at line {node.lineno}",
            uses_html_methods=False,
            uses_validation_only=True
        )
        self.contexts.append(ctx)
        return ctx


def extract_usages_generic(adapter, source_bytes: bytes, target_name: str, file_path: str) -> List[CallContext]:
    contexts = []
    try:
        tree = adapter.parse(source_bytes)
        
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if not node:
                continue
            
            is_call = node.type in ('call', 'call_expression', 'method_invocation')
            if is_call:
                func_node = node.child_by_field_name('function') or node.child_by_field_name('name')
                if not func_node:
                    for child in node.children:
                        if child.type in ('identifier', 'type_identifier', 'field_identifier'):
                            func_node = child
                            break
                if func_node:
                    func_text = func_node.text
                    if hasattr(func_text, 'decode'):
                        func_text = func_text.decode('utf-8', errors='ignore')
                    if func_text == target_name:
                        contexts.append(CallContext(
                            file_path=file_path,
                            line_number=node.start_point[0] + 1,
                            caller_symbol="Direct Call",
                            code_snippet=f"Direct Call at line {node.start_point[0] + 1}",
                            uses_html_methods=False,
                            uses_validation_only=True
                        ))
            
            is_class_def = node.type in ('class_definition', 'class_declaration', 'type_spec', 'impl_item')
            if is_class_def:
                name_node = node.child_by_field_name('name')
                for child in node.children:
                    if child != name_node and child.type in ('identifier', 'type_identifier', 'superclass', 'heritage'):
                        child_text = child.text
                        if hasattr(child_text, 'decode'):
                            child_text = child_text.decode('utf-8', errors='ignore')
                        if target_name in child_text:
                            contexts.append(CallContext(
                                file_path=file_path,
                                line_number=node.start_point[0] + 1,
                                caller_symbol="Inheritance",
                                code_snippet=f"Inheritance at line {node.start_point[0] + 1}",
                                uses_html_methods=False,
                                uses_validation_only=True
                            ))
                            break
                            
            for child in reversed(node.children):
                stack.append(child)
    except Exception:
        pass
    return contexts


def extract_usages(root_path: str, target_symbol: str) -> List[CallContext]:
    from anchor.core.registry import LanguageRegistry
    supported_extensions = set(LanguageRegistry._ext_map.keys())

    simple_name = target_symbol.split(":")[-1].split(".")[-1]
    print(f"DEBUG: Scanning for usages of '{simple_name}'...")

    all_contexts = []
    skipped_dirs = {'.git', '__pycache__', 'venv', 'migrations', 'node_modules', '.anchor'}

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in skipped_dirs]
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in supported_extensions:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_path)
                
                adapter = LanguageRegistry.get_adapter_for_file(full_path)
                if not adapter:
                    continue
                
                try:
                    with open(full_path, "rb") as f:
                        source_bytes = f.read()
                    
                    if adapter.language_id == 'python':
                        try:
                            tree = ast.parse(source_bytes.decode('utf-8', errors='ignore'))
                            visitor = UsageAnalyzer(simple_name, rel_path)
                            visitor.visit(tree)
                            all_contexts.extend(visitor.contexts)
                        except Exception:
                            all_contexts.extend(extract_usages_generic(adapter, source_bytes, simple_name, rel_path))
                    else:
                        all_contexts.extend(extract_usages_generic(adapter, source_bytes, simple_name, rel_path))
                except Exception:
                    continue
    return all_contexts
