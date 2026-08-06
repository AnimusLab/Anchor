import pytest
from anchor.core.registry import LanguageRegistry
from anchor.adapters.c_cpp import CCppAdapter
from anchor.adapters.csharp import CSharpAdapter
from anchor.adapters.ruby import RubyAdapter
from anchor.adapters.php import PHPAdapter
from anchor.adapters.swift import SwiftAdapter
from anchor.adapters.kotlin import KotlinAdapter
from anchor.adapters.scala import ScalaAdapter
from anchor.adapters.python import PythonAdapter
from anchor.adapters.typescript import TypeScriptAdapter

def test_language_registry_resolution():
    assert isinstance(LanguageRegistry.get_adapter_for_file("main.cpp"), CCppAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("Service.cs"), CSharpAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("app.rb"), RubyAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("index.php"), PHPAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("AppDelegate.swift"), SwiftAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("Main.kt"), KotlinAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("Pipeline.scala"), ScalaAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("script.py"), PythonAdapter)
    assert isinstance(LanguageRegistry.get_adapter_for_file("component.tsx"), TypeScriptAdapter)

def test_c_cpp_adapter_queries():
    adapter = CCppAdapter()
    assert adapter.language_id == "c_cpp"
    assert ".cpp" in adapter.extensions
    query = adapter.build_dangerous_call_query(["system", "exec"])
    assert "system" in query

def test_csharp_adapter_queries():
    adapter = CSharpAdapter()
    assert adapter.language_id == "csharp"
    assert ".cs" in adapter.extensions
    query = adapter.build_import_query(["Microsoft.SemanticKernel"])
    assert "Microsoft.SemanticKernel" in query

def test_ruby_adapter_queries():
    adapter = RubyAdapter()
    assert adapter.language_id == "ruby"
    assert ".rb" in adapter.extensions
    query = adapter.build_import_query(["langchain"])
    assert "langchain" in query

def test_kotlin_adapter_queries():
    adapter = KotlinAdapter()
    assert adapter.language_id == "kotlin"
    assert ".kt" in adapter.extensions
    assert ".kts" in adapter.extensions
