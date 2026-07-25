from abc import ABC, abstractmethod
from typing import List
from tree_sitter import Parser

class LanguageAdapter(ABC):
    """
    The Rosetta Stone: Translates Universal Rules into Language-Specific AST Queries.
    """

    @property
    @abstractmethod
    def language_id(self) -> str:
        """e.g., 'python', 'typescript', 'java'"""
        pass

    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """File extensions this adapter claims. e.g., ['.ts', '.tsx']"""
        pass

    @abstractmethod
    def get_grammar(self):
        """Returns the compiled Tree-sitter language object."""
        pass

    @abstractmethod
    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """S-expression for function calls."""
        pass

    @abstractmethod
    def build_import_query(self, module_names: List[str]) -> str:
        """S-expression for module imports."""
        pass

    @abstractmethod
    def build_inheritance_query(self, class_names: List[str]) -> str:
        """S-expression for class inheritance."""
        pass

    def get_parser(self) -> Parser:
        """Standard wrapper to get a parser for this language."""
        return Parser(self.get_grammar())

    def parse(self, source_code: bytes):
        """Common parsing logic using Tree-sitter."""
        parser = self.get_parser()
        return parser.parse(source_code)

    def extract_symbols(self, source_code: bytes) -> List[dict]:
        """
        Walks the tree-sitter AST and extracts symbols (classes/functions).
        Each symbol is a dict: {'name': str, 'type': 'class'|'function', 'line_number': int}
        """
        import re
        IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        KEYWORDS = {
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
            'break', 'continue', 'return', 'function', 'class', 'const', 'let',
            'var', 'import', 'export', 'try', 'catch', 'finally', 'throw',
            'new', 'this', 'super', 'typeof', 'instanceof', 'in', 'of',
            'struct', 'enum', 'fn', 'pub', 'use', 'impl', 'trait', 'type',
            'interface', 'package', 'go', 'select', 'defer', 'chan', 'map',
            'ts', 'js', 'as', 'from', 'package', 'public', 'private', 'protected'
        }

        class_types = getattr(self, 'class_types', set())  # anchor: ignore SEC-010
        function_types = getattr(self, 'function_types', set())  # anchor: ignore SEC-010
        if not class_types and not function_types:
            return []

        tree = self.parse(source_code)
        symbols = []
        
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if not node:
                continue
            
            node_type = node.type
            is_class = node_type in class_types
            is_func = node_type in function_types
            
            if is_class or is_func:
                sym_type = 'class' if is_class else 'function'
                name_node = node.child_by_field_name('name')
                if not name_node:
                    for child in node.children:
                        if child.type in ('identifier', 'type_identifier', 'field_identifier'):
                            name_node = child
                            break
                if name_node:
                    name_text = name_node.text
                    if hasattr(name_text, 'decode'):
                        name_text = name_text.decode('utf-8', errors='ignore')
                    name_str = str(name_text).strip()
                    
                    if IDENTIFIER_RE.match(name_str) and name_str not in KEYWORDS:
                        symbols.append({
                            'name': name_str,
                            'type': sym_type,
                            'line_number': node.start_point[0] + 1
                        })
            
            for child in reversed(node.children):
                stack.append(child)
                
        return symbols
