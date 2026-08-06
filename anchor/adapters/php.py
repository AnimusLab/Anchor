from anchor.adapters.base import LanguageAdapter
from typing import List

class PHPAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "php"

    @property
    def extensions(self) -> List[str]:
        return [".php"]

    def get_grammar(self):
        return None


    def build_import_query(self, modules: List[str]) -> str:
        names_str = " ".join([f'"{m}"' for m in modules])
        return f"""
        (namespace_use_clause
          name: (qualified_name) @import_name (#match? @import_name "({names_str})")) @violation
        """

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        names_str = " ".join([f'"{name}"' for name in function_names])
        return f"""
        (function_call_expression
          function: (name) @func_name (#match? @func_name "^({names_str})$")) @violation
        """

    def build_inheritance_query(self, parent_classes: List[str]) -> str:
        names_str = " ".join([f'"{p}"' for p in parent_classes])
        return f"""
        (class_declaration
          base_clause: (base_clause (name) @parent_name (#match? @parent_name "^({names_str})$"))) @violation
        """
