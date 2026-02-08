from typing import Dict, Type, Optional
from anchor.adapters.base import LanguageAdapter
from anchor.adapters.typescript import TypeScriptAdapter
from anchor.adapters.python import PythonAdapter
import os

class LanguageRegistry:
    _adapters: Dict[str, Type[LanguageAdapter]] = {}
    _ext_map: Dict[str, Type[LanguageAdapter]] = {}

    @classmethod
    def register(cls, adapter_cls: Type[LanguageAdapter]):
        """Registers a new language adapter."""
        # 1. Store by Language ID
        instance = adapter_cls() # Instantiate to get properties
        cls._adapters[instance.language_id] = adapter_cls
        
        # 2. Map Extensions to this Adapter
        for ext in instance.extensions:
            cls._ext_map[ext] = adapter_cls

    @classmethod
    def get_adapter_for_file(cls, filename: str) -> Optional[LanguageAdapter]:
        """Returns the correct adapter instance for a given filename."""
        _, ext = os.path.splitext(filename)
        
        # DEBUG: Print if we have any adapters registered at all
        # print(f"DEBUG: File={filename}, Ext={ext}, MapKeys={list(cls._ext_map.keys())}")
        
        adapter_cls = cls._ext_map.get(ext)
        if adapter_cls:
            return adapter_cls()
        return None

# Auto-register supported languages on import
LanguageRegistry.register(TypeScriptAdapter)
LanguageRegistry.register(PythonAdapter)
