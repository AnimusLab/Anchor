from .base import LanguageAdapter
import tree_sitter_python as tspy
from tree_sitter import Language, Parser
from typing import List

class PythonAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "python"

    @property
    def extensions(self) -> List[str]:
        return [".py"]

    def get_grammar(self):
        return Language(tspy.language())

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """
        Query for Python function calls like:
        eval(...)
        subprocess.run(...)  # anchor: ignore ANC-018
        """
        funcs_regex = "|".join(function_names)
        return f"""
        (call
            function: (identifier) @func_name
            (#match? @func_name "^({funcs_regex})$")
        ) @violation
        """

    def build_import_query(self, module_names: List[str]) -> str:
        """
        Query for Python imports like:
        import module
        from module import name
        """
        modules_regex = "|".join(module_names)
        return f"""
        [
            (import_statement
                name: (dotted_name) @import_name)
            (import_from_statement
                module_name: (dotted_name) @import_name)
        ] @violation
        (#match? @import_name "^({modules_regex})$")
        """

    def build_inheritance_query(self, class_names: List[str]) -> str:
        """
        Query for Python class inheritance:
        class MyThread(Thread):
        """
        class_regex = "|".join(class_names)
        return f"""
        (class_definition
            superclasses: (argument_list 
                (identifier) @parent_name
                (#match? @parent_name "^({class_regex})$")
            )
        ) @violation
        """
