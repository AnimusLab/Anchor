
import pytest
from anchor.adapters.java import JavaAdapter
from tree_sitter import Parser

def test_java_adapter_properties():
    adapter = JavaAdapter()
    assert adapter.language_id == "java"
    assert ".java" in adapter.extensions

def test_java_dangerous_call_detection():
    adapter = JavaAdapter()
    parser = Parser(adapter.get_grammar())
    
    java_code = b"""
    public class Vulnerable {
        public void run() {
            Runtime.getRuntime().exec("rm -rf /");
        }
    }
    """
    
    tree = parser.parse(java_code)
    query_str = adapter.build_dangerous_call_query(["exec"])
    from tree_sitter import Query, QueryCursor
    query = Query(adapter.get_grammar(), query_str)
    
    # Modern QueryCursor requires Query object in constructor
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
    except TypeError:
        # Fallback for other bindings
        cursor = QueryCursor()
        captures = cursor.captures(query, tree.root_node)
    
    # We expect to capture the 'exec' identifier
    # captures is a dict { name: [node, ...] }
    assert len(captures) > 0
    
    violation_nodes = captures.get("violation")
    assert violation_nodes is not None
    assert len(violation_nodes) > 0

    method_name_nodes = captures.get("func_name")
    assert method_name_nodes is not None
    assert java_code[method_name_nodes[0].start_byte:method_name_nodes[0].end_byte] == b"exec"

def test_java_audit_hook_detection():
    # Test checking for imports (e.g. reflection)
    adapter = JavaAdapter()
    parser = Parser(adapter.get_grammar())
    
    java_code = b"""
    import java.lang.reflect.Method;
    import java.util.Scanner;
    
    class Test {}
    """
    
    tree = parser.parse(java_code)
    # Check for reflection import
    query_str = adapter.build_import_query(["java.lang.reflect.Method"])
    from tree_sitter import Query, QueryCursor
    query = Query(adapter.get_grammar(), query_str)
    
    # Modern QueryCursor requires Query object in constructor
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
    except TypeError:
        # Fallback for other bindings
        cursor = QueryCursor()
        captures = cursor.captures(query, tree.root_node)

    assert len(captures) > 0
    
    # captures is dict { name: [node] }
    # We allow 'import_name' or Just the default capture if valid
    
    found_node = None
    # Check for specific capture names defined in the adapter query
    if "import_name" in captures:
        found_node = captures["import_name"][0]
    elif "violation" in captures:
        found_node = captures["violation"][0]
        
    assert found_node is not None
    # The capture includes the scoped identifier
    assert b"java.lang.reflect.Method" in java_code[found_node.start_byte:found_node.end_byte]
