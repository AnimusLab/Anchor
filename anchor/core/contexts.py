import ast
import os
from typing import List, Set
from anchor.core.models import CallContext

class UsageAnalyzer(ast.NodeVisitor):
    def __init__(self, target_name: str, file_path: str):
        self.target_name = target_name
        self.file_path = file_path
        self.contexts: List[CallContext] = []
        
        # Tracking scope
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
        
        # Restore scope
        self.current_scope_vars = old_vars

    def visit_Assign(self, node):
        # 2. Track Instantiations: form = Form(...)
        if not isinstance(node.value, (ast.Call)):
            return

        is_target = False
        if isinstance(node.value.func, ast.Name) and node.value.func.id == self.target_name:
            is_target = True
        elif isinstance(node.value.func, ast.Attribute) and node.value.func.attr == self.target_name:
            is_target = True
            
        if is_target:
            # Capture variable name (e.g., 'form')
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    self.current_scope_vars.add(var_name)
                    
                    # Create context and attach it to scope so we can update it
                    self.current_context = self._add_context(node, "Instantiation")
    
    def visit_Call(self, node):
        # 3. Track Method Calls on tracked variables
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id
            method_name = node.func.attr
            
            # If we are tracking this variable, check what method is called
            if var_name in self.current_scope_vars and self.current_context:
                if method_name in {'as_p', 'as_table', 'as_ul', 'render'}:
                    self.current_context.uses_html_methods = True
                
                # We assume validation is always used if instantiated
                self.current_context.uses_validation_only = True # default
                
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

def extract_usages(root_path: str, target_symbol: str) -> List[CallContext]:
    simple_name = target_symbol.split(":")[-1].split(".")[-1]
    print(f"DEBUG: Scanning for usages of '{simple_name}'...")
    
    all_contexts = []
    skipped_dirs = {'.git', '__pycache__', 'venv', 'migrations'} 
    
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in skipped_dirs]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    visitor = UsageAnalyzer(simple_name, rel_path)
                    visitor.visit(tree)
                    all_contexts.extend(visitor.contexts)
                except Exception:
                    continue
    return all_contexts