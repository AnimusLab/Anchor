from typing import Dict, Type, Optional
from anchor.adapters.base import LanguageAdapter
from anchor.adapters.typescript import TypeScriptAdapter
from anchor.adapters.python import PythonAdapter
from anchor.adapters.java import JavaAdapter
from anchor.adapters.go import GoAdapter
from anchor.adapters.rust import RustAdapter
from anchor.adapters.c_cpp import CCppAdapter
from anchor.adapters.csharp import CSharpAdapter
from anchor.adapters.ruby import RubyAdapter
from anchor.adapters.php import PHPAdapter
from anchor.adapters.swift import SwiftAdapter
from anchor.adapters.kotlin import KotlinAdapter
from anchor.adapters.scala import ScalaAdapter
import os

class LanguageRegistry:
    _adapters: Dict[str, Type[LanguageAdapter]] = {}
    _ext_map: Dict[str, Type[LanguageAdapter]] = {}

    @classmethod
    def register(cls, adapter_cls: Type[LanguageAdapter]):
        """Registers a new language adapter."""
        instance = adapter_cls()
        cls._adapters[instance.language_id] = adapter_cls
        for ext in instance.extensions:
            cls._ext_map[ext] = adapter_cls

    @classmethod
    def get_adapter_for_file(cls, filename: str) -> Optional[LanguageAdapter]:
        """Returns the correct adapter instance for a given filename."""
        _, ext = os.path.splitext(filename)
        adapter_cls = cls._ext_map.get(ext.lower())
        if adapter_cls:
            return adapter_cls()
        return None

# Auto-register supported languages on import
LanguageRegistry.register(TypeScriptAdapter)
LanguageRegistry.register(PythonAdapter)
LanguageRegistry.register(JavaAdapter)
LanguageRegistry.register(GoAdapter)
LanguageRegistry.register(RustAdapter)
LanguageRegistry.register(CCppAdapter)
LanguageRegistry.register(CSharpAdapter)
LanguageRegistry.register(RubyAdapter)
LanguageRegistry.register(PHPAdapter)
LanguageRegistry.register(SwiftAdapter)
LanguageRegistry.register(KotlinAdapter)
LanguageRegistry.register(ScalaAdapter)

