"""
SafeTensors Plugin for AnchorGrid/HuggingFace Models

Supports .safetensors format used by AnchorGrid and HuggingFace.
"""

from typing import Dict, Any
import json


class SafeTensorsPlugin:
    """Plugin for SafeTensors format."""
    
    def extract_metadata(self, model_path: str) -> Dict[str, Any]:
        """
        Extract metadata from SafeTensors file.
        
        SafeTensors format:
        - Header with JSON metadata
        - Tensor data
        """
        metadata = {}
        
        try:
            with open(model_path, 'rb') as f:
                # Read header size (first 8 bytes)
                import struct
                header_size = struct.unpack('<Q', f.read(8))[0]
                
                # Read header JSON
                header_bytes = f.read(header_size)
                header = json.loads(header_bytes.decode('utf-8'))
                
                # Extract metadata
                if '__metadata__' in header:
                    metadata.update(header['__metadata__'])
                
                # Count tensors
                tensor_count = len([k for k in header.keys() if k != '__metadata__'])
                metadata['tensor_count'] = tensor_count
                metadata['format'] = 'safetensors'
                
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def analyze_weights(self, model_path: str) -> Dict[str, Any]:
        """Analyze weight distributions in SafeTensors model."""
        analysis = {
            'has_anomalies': False,
            'format': 'safetensors'
        }
        
        try:
            import os
            file_size = os.path.getsize(model_path)
            analysis['size_mb'] = file_size / (1024 * 1024)
            
            # Basic sanity checks
            if file_size < 1024 * 1024:
                analysis['has_anomalies'] = True
                analysis['anomaly_description'] = 'Model file suspiciously small'
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
