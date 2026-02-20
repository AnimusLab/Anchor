from .base import LanguageAdapter
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser
from typing import List

class TypeScriptAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "typescript"

    @property
    def extensions(self) -> List[str]:
        return [".ts", ".tsx"]

    def get_grammar(self):
        # Load the compiled Typescript grammar
        return Language(tsts.language_typescript())

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """
        Constructs a query to find calls like:
        - eval('code')
        - child_process.exec('cmd')
        """
        # Create a regex that matches ANY of the banned functions
        # e.g., "eval|exec|spawn"
        # Escape special characters just in case, though usually function names are simple
        funcs_regex = "|".join(function_names)
        
        # Predicate-Less Query: We capture ALL calls and filter in Python for 100% reliability
        return """
        (call_expression
            (_) @func_name
        ) @violation
        """

    def build_import_query(self, module_names: List[str]) -> str:
        """
        Query for TS imports like:
        import { x } from 'module';
        import x from 'module';
        require('module');
        """
        modules_regex = "|".join(module_names)
        return f"""
        [
            (import_statement source: (string (string_fragment) @import_name))
            (call_expression
                function: (identifier) @func (#eq? @func "require")
                arguments: (arguments (string (string_fragment) @import_name)))
        ] @violation
        (#match? @import_name "^({modules_regex})$")
        """

    def build_inheritance_query(self, class_names: List[str]) -> str:
        """S-expression for class inheritance (e.g. extends)."""
        # Placeholder for now
        return ""
