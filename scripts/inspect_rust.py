"""
scripts/inspect_rust.py

Debug tool: dumps the tree-sitter parse tree for a sample Rust snippet
and exercises the RustAdapter's query builders.

Usage:  python scripts/inspect_rust.py
"""

import tree_sitter_rust as tsrust
from tree_sitter import Language, Parser
from anchor.adapters.rust import RustAdapter


def walk(node, depth=0):
    print(f"{'  ' * depth}{node.type} [{node.start_point}-{node.end_point}]")
    for child in node.children:
        walk(child, depth + 1)


def inspect():
    adapter = RustAdapter()
    grammar = adapter.get_grammar()
    parser  = Parser(Language(tsrust.language()))

    rust_code = b"""
use std::process::Command;

fn dangerous_exec(cmd: &str) {
    Command::new("sh")
        .arg("-c")
        .arg(cmd)          // command injection risk
        .spawn()
        .expect("failed");
}

fn hardcoded() {
    let secret = "sk-prod-abc123XYZ";   // hardcoded API key
    let pw     = "admin:password123";   // hardcoded password
}
"""

    print("=== Parse Tree ===")
    tree = parser.parse(rust_code)
    walk(tree.root_node)

    print("\n=== Dangerous Call Query (Command::new, spawn) ===")
    q_str = adapter.build_dangerous_call_query(["Command::new", "spawn"])
    print(f"  S-expr: {q_str!r}")

    print("\n=== Import Query (std::process) ===")
    q_str = adapter.build_import_query(["std::process"])
    print(f"  S-expr: {q_str!r}")


if __name__ == "__main__":
    inspect()
