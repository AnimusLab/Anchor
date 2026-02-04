"""
HuggingFace Plugin for Transformers Models

Supports HuggingFace model formats (.bin, .safetensors with config.json).
"""

from typing import Dict, Any
import json
import os


class HuggingFacePlugin:
    """Plugin for HuggingFace Transformers format."""
    
    def extract_metadata(self, model_path: str) -> Dict[str, Any]:
        """
        Extract metadata from HuggingFace model.
        
        Looks for config.json in the same directory.
        """
        metadata = {}
        
        try:
            # Look for config.json
            model_dir = os.path.dirname(model_path)
            config_path = os.path.join(model_dir, 'config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    metadata.update(config)
            
            # Look for training metadata
            training_args_path = os.path.join(model_dir, 'training_args.bin')
            if os.path.exists(training_args_path):
                metadata['has_training_metadata'] = True
            
            metadata['format'] = 'huggingface'
            metadata['vendor'] = 'huggingface'
            
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def analyze_weights(self, model_path: str) -> Dict[str, Any]:
        """Analyze HuggingFace model weights."""
        analysis = {
            'has_anomalies': False,
            'format': 'huggingface'
        }
        
        try:
            import os
            file_size = os.path.getsize(model_path)
            analysis['size_mb'] = file_size / (1024 * 1024)
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
