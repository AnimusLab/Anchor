
import pytest
from anchor.adapters.rust import RustAdapter
from tree_sitter import Parser, Query, QueryCursor

def test_rust_adapter_properties():
    adapter = RustAdapter()
    assert adapter.language_id == "rust"
    assert ".rs" in adapter.extensions

def test_rust_dangerous_call_detection():
    adapter = RustAdapter()
    parser = Parser(adapter.get_grammar())
    
    rust_code = b"""
    use std::process::Command;
    
    fn main() {
        let output = Command::new("rm")
            .arg("-rf")
            .arg("/")
            .output()
            .expect("failed to execute process");
            
        unsafe {
            // Some unsafe code
        }
    }
    """
    
    tree = parser.parse(rust_code)
    # Check for Command::new type calls
    # Note: tree-sitter-rust structure for Command::new might be:
    # (call_expression function: (scoped_identifier path: (identifier) name: (identifier)))
    # or just scoped_identifier.
    
    query_str = adapter.build_dangerous_call_query(["Command::new"])
    
    # print(f"DEBUG: tree-sitter version: {tree_sitter.__version__}")
    
    query = Query(adapter.get_grammar(), query_str)
    
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
    except TypeError:
        cursor = QueryCursor()
        captures = cursor.captures(query, tree.root_node)
        
    # captures is dict { name: [node, ...] }
    assert len(captures) > 0
    func_name_nodes = captures.get("func_name")
    assert func_name_nodes is not None
    
    found_command = False
    for node in func_name_nodes:
        if b"Command::new" in rust_code[node.start_byte:node.end_byte]:
            found_command = True
            break
            
    assert found_command

def test_rust_import_detection():
    adapter = RustAdapter()
    parser = Parser(adapter.get_grammar())
    
    rust_code = b"""
    use std::fs;
    use std::process::Command;
    """
    
    tree = parser.parse(rust_code)
    
    # Check for use std::fs
    query_str = adapter.build_import_query(["std::fs"])
    
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
    
    found_fs = False
    for node in import_nodes:
        if b"std::fs" in rust_code[node.start_byte:node.end_byte]:
            found_fs = True
            break
            
    assert found_fs
