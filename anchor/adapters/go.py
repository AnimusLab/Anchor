from .base import LanguageAdapter
import tree_sitter_go as tsgo
from tree_sitter import Language
from typing import List

class GoAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "go"

    @property
    def extensions(self) -> List[str]:
        return [".go"]

    def get_grammar(self):
        return Language(tsgo.language())

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """
        Query for Go function calls like:
        exec.Command(...)
        os.Exit(...)
        """
        funcs_regex = "|".join(function_names)
        return f"""
        (call_expression
            function: [
                (identifier) @func_name
                (selector_expression field: (field_identifier) @func_name)
            ]
            (#match? @func_name "^({funcs_regex})$")
        ) @violation
        """

    def build_import_query(self, module_names: List[str]) -> str:
        """
        Query for Go imports like:
        import "os/exec"
        import "net/http"
        """
        # Go imports are string literals, often with quotes
        modules_regex = "|".join(module_names)
        return f"""
        (import_spec
            path: (interpreted_string_literal) @import_name
            (#match? @import_name "{modules_regex.replace('"', '\\"')}")
        ) @violation
        """

    def build_inheritance_query(self, class_names: List[str]) -> str:
        """
        Query for Go struct embedding (closest thing to inheritance):
        type Admin struct {
            User // Embedded struct
        }
        """
        class_regex = "|".join(class_names)
        return f"""
        (field_declaration
            type: (type_identifier) @parent_name
            (#match? @parent_name "^({class_regex})$")
        ) @violation
        """
