import tree_sitter_python
from tree_sitter import Language, Parser

# 1. Export Query and QueryCursor
try:
    from tree_sitter import Query, QueryCursor
except ImportError:
    print("❌ ERROR: Could not import Query/QueryCursor from tree_sitter.")
    raise


def get_language():
    """
    Returns the compiled Python language grammar.
    """
    return Language(tree_sitter_python.language())


def get_parser():
    """
    Returns a Parser configured for Python.
    """
    # FIX: Pass the language directly to the constructor (New API)
    return Parser(get_language())
