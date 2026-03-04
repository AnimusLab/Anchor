"""
scripts/inspect_ts.py

Debug tool: dumps the tree-sitter parse tree for a sample TypeScript snippet
and exercises the TypeScriptAdapter's query builders.

Usage:  python scripts/inspect_ts.py
"""

import tree_sitter_typescript
from tree_sitter import Language, Parser
from anchor.adapters.typescript import TypeScriptAdapter


def walk(node, depth=0):
    print(f"{'  ' * depth}{node.type} [{node.start_point}-{node.end_point}]")
    for child in node.children:
        walk(child, depth + 1)


def inspect():
    adapter = TypeScriptAdapter()
    grammar = adapter.get_grammar()
    parser  = Parser(Language(tree_sitter_typescript.language_typescript()))

    ts_code = b"""
import { exec } from 'child_process';
import OpenAI from 'openai';

const client = new OpenAI({ apiKey: process.env.OPENAI_KEY });

function dangerousEval(userInput: string): void {
    eval(userInput);                           // dangerous: eval
    exec(`rm -rf ${userInput}`, (err) => {}); // command injection
}

const SECRET = "ghp_abc123XYZ789";            // hardcoded GitHub token
"""

    print("=== Parse Tree ===")
    tree = parser.parse(ts_code)
    walk(tree.root_node)

    print("\n=== Dangerous Call Query (eval, exec) ===")
    q_str = adapter.build_dangerous_call_query(["eval", "exec"])
    print(f"  S-expr: {q_str!r}")

    print("\n=== Import Query (child_process, openai) ===")
    q_str = adapter.build_import_query(["child_process", "openai"])
    print(f"  S-expr: {q_str!r}")


if __name__ == "__main__":
    inspect()
