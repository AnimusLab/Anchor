from .base import LanguageAdapter
import tree_sitter_java as tsjava
from tree_sitter import Language
from typing import List

class JavaAdapter(LanguageAdapter):
    @property
    def language_id(self) -> str:
        return "java"

    @property
    def extensions(self) -> List[str]:
        return [".java"]

    def get_grammar(self):
        return Language(tsjava.language())

    def build_dangerous_call_query(self, function_names: List[str]) -> str:
        """
        Query for Java method invocations like:
        Runtime.getRuntime().exec(...)
        System.exit(...)
        """
        funcs_regex = "|".join(function_names)
        return f"""
        (method_invocation
            name: (identifier) @func_name
            (#match? @func_name "^({funcs_regex})$")
        ) @violation
        """

    def build_import_query(self, module_names: List[str]) -> str:
        """
        Query for Java imports like:
        import java.util.Scanner;
        import java.io.*;
        """
        modules_regex = "|".join(module_names)
        return f"""
        (import_declaration
            (scoped_identifier) @import_name
            (#match? @import_name "^({modules_regex})")
        ) @violation
        """

    def build_inheritance_query(self, class_names: List[str]) -> str:
        """
        Query for Java class inheritance:
        public class Admin extends User { ... }
        """
        class_regex = "|".join(class_names)
        return f"""
        (class_declaration
            superclass: (superclass
                (type_identifier) @parent_name
                (#match? @parent_name "^({class_regex})$")
            )
        ) @violation
        """
