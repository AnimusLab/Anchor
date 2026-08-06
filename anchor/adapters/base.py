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
