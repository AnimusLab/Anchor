from .base import LanguageAdapter
import tree_sitter_rust as tsrust
from tree_sitter import Language
from typing import List

class RustAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "rust"

    @property
    def extensions(self) -> List[str]:
        return [".rs"]

    def get_grammar(self):
        return Language(tsrust.language())

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """
        Query for Rust function calls.
        Supports:
        - function_item() -> captured as identifier
        - std::process::Command::new() -> captured as scoped_identifier or field_expression
        """
        funcs_regex = "|".join(function_names)
        return f"""
        (call_expression
            function: [
                (identifier) @func_name
                (scoped_identifier) @func_name
                (field_expression) @func_name
            ]
            (#match? @func_name "({funcs_regex})")
        ) @violation
        """

    def build_import_query(self, module_names: List[str]) -> str:
        """
        Query for Rust use statements:
        use std::process::Command;
        use std::fs;
        """
        modules_regex = "|".join(module_names)
        return f"""
        (use_declaration
            argument: [
                (scoped_identifier) @import_name
                (identifier) @import_name
            ]
            (#match? @import_name "({modules_regex})")
        ) @violation
        """

    def build_inheritance_query(self, class_names: List[str]) -> str:
        """
        Rust doesn't have class inheritance, but it has Trait implementation.
        impl MyTrait for MyStruct { ... }
        This query captures the Trait name being implemented.
        """
        class_regex = "|".join(class_names)
        return f"""
        (impl_item
            trait: (type_identifier) @parent_name
            (#match? @parent_name "^({class_regex})$")
        ) @violation
        """
