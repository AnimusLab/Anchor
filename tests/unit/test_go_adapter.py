
import pytest
from anchor.adapters.go import GoAdapter
from tree_sitter import Parser, Query, QueryCursor

def test_go_adapter_properties():
    adapter = GoAdapter()
    assert adapter.language_id == "go"
    assert ".go" in adapter.extensions

def test_go_dangerous_call_detection():
    adapter = GoAdapter()
    parser = Parser(adapter.get_grammar())
    
    go_code = b"""
    package main
    import (
        "fmt"
        "os/exec"
    )

    func main() {
        cmd := exec.Command("rm", "-rf", "/")
        cmd.Run()
    }
    """
    
    tree = parser.parse(go_code)
    # Testing both simple call "Command" and selector "exec.Command"
    query_str = adapter.build_dangerous_call_query(["exec.Command", "Command"])
    
    query = Query(adapter.get_grammar(), query_str)
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
    except TypeError:
        cursor = QueryCursor()
        captures = cursor.captures(query, tree.root_node)
    
    # captures is dict { name: [node, ...] }
    assert len(captures) > 0
    
    method_name_nodes = captures.get("func_name")
    assert method_name_nodes is not None
    assert len(method_name_nodes) > 0
    
    # In tree-sitter-go, selector_expression has a field: (field_identifier) which is "Command"
    # Our query captures the 'func_name' as either the identifier or the field_identifier
    # so we expect "Command" to be captured.
    
    found_command = False
    for node in method_name_nodes:
        if b"Command" in go_code[node.start_byte:node.end_byte]:
            found_command = True
            break
            
    assert found_command

def test_go_import_detection():
    adapter = GoAdapter()
    parser = Parser(adapter.get_grammar())
    
    go_code = b"""
    package main
    import (
        "fmt"
        "os/exec"
    )
    """
    
    tree = parser.parse(go_code)
    # Note: query regex matches against string literal content including quotes usually?
    # tree-sitter-go string_literal includes quotes.
    # The adapter uses regex match.
    # ^("os/exec")$ to match exact string with quotes? 
    # Or does tree-sitter match content? 
    # Let's try matching the content inside quotes or just the whole literal.
    
    # If the adapter regex is just "os/exec", and the node text is "\"os/exec\"", 
    # we might need to adjust the regex or the query.
    # For now, let's test if we can catch it.
    
    query_str = adapter.build_import_query(['"os/exec"']) 
    
    query = Query(adapter.get_grammar(), query_str)
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
    except TypeError:
        cursor = QueryCursor()
        captures = cursor.captures(query, tree.root_node)
        
    assert len(captures) > 0
    import_nodes = captures.get("import_name")
    assert import_nodes is not None
    # match against full literal including quotes
    assert b'"os/exec"' in go_code[import_nodes[0].start_byte:import_nodes[0].end_byte]
