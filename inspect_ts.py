
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser, Query, QueryCursor
from anchor.adapters.java import JavaAdapter

def inspect():
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
    query = Query(adapter.get_grammar(), query_str)
    
    try:
        cursor = QueryCursor(query)
        print("Used QueryCursor(query)")
    except TypeError:
        cursor = QueryCursor()
        print("Used QueryCursor()")

    captures = cursor.captures(tree.root_node)
    
    print(f"Type of captures: {type(captures)}")
    print(f"Content of captures: {captures}")
    
    if isinstance(captures, dict):
        print("It is a DICT.")
        for k, v in captures.items():
            print(f"Key: {k}, Value: {v}")
    elif isinstance(captures, list):
        print("It is a LIST.")
        if len(captures) > 0:
            print(f"First element type: {type(captures[0])}")
            print(f"First element: {captures[0]}")

if __name__ == "__main__":
    inspect()
