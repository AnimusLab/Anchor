"""
scripts/inspect_python.py

Debug tool: dumps the tree-sitter parse tree for a sample Python snippet
and exercises the PythonAdapter's query builders.

Usage:  python scripts/inspect_python.py
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query
from anchor.adapters.python import PythonAdapter


def walk(node, depth=0):
    print(f"{'  ' * depth}{node.type} [{node.start_point}-{node.end_point}]")
    for child in node.children:
        walk(child, depth + 1)


def inspect():
    adapter = PythonAdapter()
    grammar = adapter.get_grammar()
    parser  = Parser(Language(tspython.language()))

    py_code = b"""
import subprocess
import os

def run_shell(cmd):
    subprocess.run(cmd, shell=True)          # dangerous: shell=True
    result = eval(input(">>> "))             # dangerous: eval(input)
    os.system("rm -rf /tmp/data")           # dangerous: os.system

class AuthManager:
    SECRET_KEY = "hardcoded-secret-abc123"  # hardcoded secret
    def login(self, user, pwd):
        return f"SELECT * FROM users WHERE user='{user}'"  # SQL injection
"""

    print("=== Parse Tree ===")
    tree = parser.parse(py_code)
    walk(tree.root_node)

    print("\n=== Dangerous Call Query (subprocess.run, eval, os.system) ===")
    q_str = adapter.build_dangerous_call_query(["subprocess.run", "eval", "os.system"])
    print(f"  S-expr: {q_str!r}")

    print("\n=== Import Query (subprocess) ===")
    q_str = adapter.build_import_query(["subprocess"])
    print(f"  S-expr: {q_str!r}")


if __name__ == "__main__":
    inspect()
