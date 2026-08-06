# Anchor Plugins

This directory contains vendor-specific plugins for model format support.

## Available Plugins

### 1. **GGUF Plugin** (`gguf_plugin.py`)
**For:** LM Studio models  
**Format:** `.gguf`  
**Features:**
- Metadata extraction from GGUF headers
- Weight anomaly detection
- File size validation

**Usage:**
```python
from anchor.plugins.gguf_plugin import GGUFPlugin

plugin = GGUFPlugin()
metadata = plugin.extract_metadata("model.gguf")
analysis = plugin.analyze_weights("model.gguf")
```

---

### 2. **SafeTensors Plugin** (`safetensors_plugin.py`)
**For:** AnchorGrid, HuggingFace models  
**Format:** `.safetensors`  
**Features:**
- JSON header parsing
- Tensor counting
- Metadata extraction

**Usage:**
```python
from anchor.plugins.safetensors_plugin import SafeTensorsPlugin

plugin = SafeTensorsPlugin()
metadata = plugin.extract_metadata("model.safetensors")
```

---

### 3. **HuggingFace Plugin** (`huggingface_plugin.py`)
**For:** HuggingFace Transformers  
**Format:** `.bin`, `.safetensors` (with `config.json`)  
**Features:**
- config.json parsing
- Training metadata detection
- Model architecture validation

**Usage:**
```python
from anchor.plugins.huggingface_plugin import HuggingFacePlugin

plugin = HuggingFacePlugin()
metadata = plugin.extract_metadata("pytorch_model.bin")
```

---

## Creating Custom Plugins

To add support for a new model format:

### 1. Create plugin file: `anchor/plugins/myformat_plugin.py`

```python
class MyFormatPlugin:
    """Plugin for custom model format."""
    
    def extract_metadata(self, model_path: str) -> Dict[str, Any]:
        """Extract metadata from model file."""
        # Your implementation
        return metadata
    
    def analyze_weights(self, model_path: str) -> Dict[str, Any]:
        """Analyze weight distributions."""
        # Your implementation
        return analysis
```

### 2. Register in `model_auditor.py`

```python
def _load_plugins(self):
    plugins = {}
    
    try:
        from anchor.plugins.myformat_plugin import MyFormatPlugin
        plugins['myformat'] = MyFormatPlugin()
    except ImportError:
        pass
    
    return plugins
```

### 3. Update format detection

```python
def _detect_format(self, model_path: str) -> str:
    ext = Path(model_path).suffix.lower()
    
    format_map = {
        '.myext': 'myformat',
        # ... existing formats
    }
    
    return format_map.get(ext, 'unknown')
```

---

## Supported Vendors

| Vendor | Format | Plugin | Status |
|--------|--------|--------|--------|
| LM Studio | `.gguf` | `gguf_plugin.py` | ✅ Ready |
| AnchorGrid | `.safetensors` | `safetensors_plugin.py` | ✅ Ready |
| HuggingFace | `.bin`, `.safetensors` | `huggingface_plugin.py` | ✅ Ready |
| OpenAI | API-based | `openai_plugin.py` | 🚧 Planned |
| Anthropic | API-based | `anthropic_plugin.py` | 🚧 Planned |
| Google | `.keras`, `.h5` | `keras_plugin.py` | 🚧 Planned |
| ONNX | `.onnx` | `onnx_plugin.py` | 🚧 Planned |

---

## Plugin Interface

All plugins must implement:

```python
class PluginInterface:
    def extract_metadata(self, model_path: str) -> Dict[str, Any]:
        """
        Extract metadata from model file.
        
        Returns:
            Dictionary with metadata fields:
            - format: str
            - vendor: str
            - tensor_count: int (optional)
            - training_metadata: dict (optional)
            - error: str (if extraction failed)
        """
        pass
    
    def analyze_weights(self, model_path: str) -> Dict[str, Any]:
        """
        Analyze weight distributions.
        
        Returns:
            Dictionary with analysis results:
            - has_anomalies: bool
            - anomaly_description: str (if has_anomalies)
            - size_mb: float
            - format: str
            - error: str (if analysis failed)
        """
        pass
```

---

## No Vendor Lock-In

anchor-audit is **vendor-agnostic** by design:

✅ Works with LM Studio  
✅ Works with AnchorGrid  
✅ Works with HuggingFace  
✅ Works with any system via plugins  

**This ensures maximum adoption and prevents vendor lock-in.**
