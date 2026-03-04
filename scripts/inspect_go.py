
import tree_sitter_go as tsgo
from tree_sitter import Language, Parser

def inspect():
    go_lang = Language(tsgo.language())
    parser = Parser(go_lang)
    
    go_code = b"""
    package main
    import "os/exec"
    """
    
    tree = parser.parse(go_code)
    cursor = tree.walk()
    
    visited_children = False
    while True:
        if not visited_children:
            print(f"{'  ' * cursor.depth}{cursor.node.type} [{cursor.node.start_point}-{cursor.node.end_point}]")
            if cursor.goto_first_child():
                visited_children = False
                continue
        
        if cursor.goto_next_sibling():
            visited_children = False
            continue
        
        if not cursor.goto_parent():
            break
        visited_children = True

if __name__ == "__main__":
    inspect()
