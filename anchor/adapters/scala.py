from anchor.adapters.base import LanguageAdapter
from typing import List

class ScalaAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "scala"

    @property
    def extensions(self) -> List[str]:
        return [".scala"]

    def build_import_query(self, modules: List[str]) -> str:
        names_str = " ".join([f'"{m}"' for m in modules])
        return f"""
        (import_declaration
          path: (stable_identifier) @import_name (#match? @import_name "({names_str})")) @violation
        """

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        names_str = " ".join([f'"{name}"' for name in function_names])
        return f"""
        (call_expression
          function: (identifier) @func_name (#match? @func_name "^({names_str})$")) @violation
        """

    def build_inheritance_query(self, parent_classes: List[str]) -> str:
        names_str = " ".join([f'"{p}"' for p in parent_classes])
        return f"""
        (class_definition
          extends_clause: (extends_clause (type_identifier) @parent_name (#match? @parent_name "^({names_str})$"))) @violation
        """
