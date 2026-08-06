from anchor.adapters.base import LanguageAdapter
from typing import List

class CCppAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "c_cpp"

    @property
    def extensions(self) -> List[str]:
        return [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"]

    def build_import_query(self, modules: List[str]) -> str:
        names_str = " ".join([f'"{m}"' for m in modules])
        return f"""
        (preproc_include
          path: (system_lib_string) @import_name (#match? @import_name "({names_str})")) @violation
        """

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        names_str = " ".join([f'"{name}"' for name in function_names])
        return f"""
        (call_expression
          function: (identifier) @func_name (#match? @func_name "^({names_str})$")) @violation
        """

    def build_inheritance_query(self, parent_classes: List[str]) -> str:
        return ""
