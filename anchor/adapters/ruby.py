from anchor.adapters.base import LanguageAdapter
from typing import List

class RubyAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "ruby"

    @property
    def extensions(self) -> List[str]:
        return [".rb"]

    def get_grammar(self):
        return None


    def build_import_query(self, modules: List[str]) -> str:
        names_str = " ".join([f'"{m}"' for m in modules])
        return f"""
        (call
          method: (identifier) @method (#match? @method "^(require|require_relative)$")
          arguments: (argument_list (string) @import_name (#match? @import_name "({names_str})"))) @violation
        """

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        names_str = " ".join([f'"{name}"' for name in function_names])
        return f"""
        (call
          method: (identifier) @func_name (#match? @func_name "^({names_str})$")) @violation
        """

    def build_inheritance_query(self, parent_classes: List[str]) -> str:
        names_str = " ".join([f'"{p}"' for p in parent_classes])
        return f"""
        (class
          superclass: (constant) @parent_name (#match? @parent_name "^({names_str})$")) @violation
        """
