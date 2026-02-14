"""
Model Auditor for Anchor-Audit

Validates LLM model weights against FINOS policies.
Vendor-agnostic: Works with LM Studio, AnchorGrid, HuggingFace, OpenAI, etc.

Architecture:
- Plugin system for different model formats
- Universal policy enforcement
- Human-readable report generation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import yaml
import json
import os
from pathlib import Path


class AuditStatus(Enum):
    """Audit result status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


@dataclass
class AuditResult:
    """Result of a model audit."""
    status: AuditStatus
    checks_passed: int
    checks_total: int
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    recommendation: str
    confidence: float


class ModelAuditor:
    """
    Vendor-agnostic model weight auditor.
    
    Supports:
    - LM Studio (.gguf)
    - AnchorGrid (.safetensors)
    - HuggingFace (.bin, .safetensors)
    - OpenAI (API-based)
    - Custom formats (via plugins)
    """
    
    def __init__(self, policy_config: Dict[str, Any], verbose: bool = False):
        """
        Initialize auditor with policy configuration.
        
        Args:
            policy_config: Merged policy from constitution.anchor + policy.anchor
            verbose: Enable verbose logging
        """
        self.policy = policy_config
        self.rules = policy_config.get('rules', [])
        self.verbose = verbose
        self.plugins = self._load_plugins()
    
    def _load_plugins(self) -> Dict[str, Any]:
        """Load model format plugins."""
        # Import plugins dynamically
        plugins = {}
        
        try:
            from anchor.plugins.safetensors_plugin import SafeTensorsPlugin
            plugins['safetensors'] = SafeTensorsPlugin()
        except ImportError:
            pass
        
        try:
            from anchor.plugins.gguf_plugin import GGUFPlugin
            plugins['gguf'] = GGUFPlugin()
        except ImportError:
            pass
        
        try:
            from anchor.plugins.huggingface_plugin import HuggingFacePlugin
            plugins['huggingface'] = HuggingFacePlugin()
        except ImportError:
            pass
        
        return plugins
    
    def audit_weights(self, 
                     model_path: str,
                     metadata_path: Optional[str] = None) -> AuditResult:
        """
        Audit model weights against policies.
        
        Args:
            model_path: Path to model weights file
            metadata_path: Optional path to training metadata JSON
        
        Returns:
            AuditResult with detailed findings
        """
        if self.verbose:
            print(f"\n🔍 Auditing Model: {model_path}")
        
        # 1. Detect model format
        model_format = self._detect_format(model_path)
        if self.verbose:
            print(f"   Format: {model_format}")
        
        # 2. Load model metadata
        metadata = self._load_metadata(model_path, metadata_path)
        
        # 3. Run policy checks
        violations = []
        warnings = []
        checks_passed = 0
        checks_total = len(self.rules)
        
        for rule in self.rules:
            result = self._check_rule(rule, model_path, metadata, model_format)
            
            if result['status'] == 'passed':
                checks_passed += 1
                if self.verbose: print(f"   ✅ {rule['id']}: {rule['name']}")
            elif result['status'] == 'failed':
                violations.append(result)
                if self.verbose: print(f"   ❌ {rule['id']}: {result['message']}")
            elif result['status'] == 'warning':
                warnings.append(result)
                checks_passed += 1  # Warnings don't fail the build
                if self.verbose: print(f"   ⚠️  {rule['id']}: {result['message']}")
        
        # 4. Calculate metrics
        metrics = self._calculate_metrics(model_path, metadata, model_format)
        
        # 5. Generate recommendation
        recommendation, confidence = self._generate_recommendation(
            violations, warnings, metrics
        )
        
        # 6. Determine overall status
        if violations:
            status = AuditStatus.FAILED
        elif warnings:
            status = AuditStatus.NEEDS_REVIEW
        else:
            status = AuditStatus.PASSED
        
        return AuditResult(
            status=status,
            checks_passed=checks_passed,
            checks_total=checks_total,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _detect_format(self, model_path: str) -> str:
        """Detect model format from file extension."""
        ext = Path(model_path).suffix.lower()
        
        format_map = {
            '.safetensors': 'safetensors',
            '.gguf': 'gguf',
            '.bin': 'pytorch',
            '.pt': 'pytorch',
            '.pth': 'pytorch',
            '.h5': 'keras',
            '.onnx': 'onnx'
        }
        
        return format_map.get(ext, 'unknown')
    
    def _load_metadata(self, 
                      model_path: str, 
                      metadata_path: Optional[str]) -> Dict[str, Any]:
        """Load model training metadata."""
        metadata = {}
        
        # Try to load from explicit metadata file
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Try to extract from model file itself
        model_format = self._detect_format(model_path)
        if model_format in self.plugins:
            plugin = self.plugins[model_format]
            extracted_metadata = plugin.extract_metadata(model_path)
            metadata.update(extracted_metadata)
        
        return metadata
    
    def _check_rule(self, 
                   rule: Dict[str, Any],
                   model_path: str,
                   metadata: Dict[str, Any],
                   model_format: str) -> Dict[str, Any]:
        """
        Check a single policy rule against the model.
        
        Rule types:
        - metadata_check: Validates training metadata
        - weight_analysis: Analyzes weight distributions
        - behavior_test: Tests model behavior
        - data_provenance: Verifies training data sources
        """
        rule_type = rule.get('check_type', 'metadata_check')
        
        if rule_type == 'metadata_check':
            return self._check_metadata_rule(rule, metadata)
        elif rule_type == 'weight_analysis':
            return self._check_weight_rule(rule, model_path, model_format)
        elif rule_type == 'behavior_test':
            return self._check_behavior_rule(rule, model_path, model_format)
        elif rule_type == 'data_provenance':
            return self._check_provenance_rule(rule, metadata)
        else:
            return {
                'rule_id': rule['id'],
                'status': 'warning',
                'message': f"Unknown rule type: {rule_type}"
            }
    
    def _check_metadata_rule(self, 
                            rule: Dict[str, Any],
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check metadata-based rules."""
        rule_id = rule['id']
        required_field = rule.get('metadata_field')
        expected_value = rule.get('expected_value')
        
        if not required_field:
            return {'rule_id': rule_id, 'status': 'passed', 'message': 'No metadata check required'}
        
        actual_value = metadata.get(required_field)
        
        if actual_value is None:
            return {
                'rule_id': rule_id,
                'status': 'failed',
                'message': f"Missing required metadata: {required_field}"
            }
        
        if expected_value and actual_value != expected_value:
            return {
                'rule_id': rule_id,
                'status': 'failed',
                'message': f"Metadata mismatch: {required_field} = {actual_value} (expected {expected_value})"
            }
        
        return {
            'rule_id': rule_id,
            'status': 'passed',
            'message': f"Metadata validated: {required_field}"
        }
    
    def _check_weight_rule(self,
                          rule: Dict[str, Any],
                          model_path: str,
                          model_format: str) -> Dict[str, Any]:
        """Check weight distribution rules."""
        rule_id = rule['id']
        
        # Use plugin to analyze weights
        if model_format not in self.plugins:
            return {
                'rule_id': rule_id,
                'status': 'warning',
                'message': f"No plugin available for {model_format} format"
            }
        
        plugin = self.plugins[model_format]
        analysis = plugin.analyze_weights(model_path)
        
        # Check for anomalies
        if analysis.get('has_anomalies', False):
            return {
                'rule_id': rule_id,
                'status': 'failed',
                'message': f"Weight anomalies detected: {analysis.get('anomaly_description')}"
            }
        
        return {
            'rule_id': rule_id,
            'status': 'passed',
            'message': 'Weight distribution normal'
        }
    
    def _check_behavior_rule(self,
                            rule: Dict[str, Any],
                            model_path: str,
                            model_format: str) -> Dict[str, Any]:
        """Check model behavior rules."""
        rule_id = rule['id']
        
        # Behavior tests require model loading (expensive)
        # For now, return warning - implement in production
        return {
            'rule_id': rule_id,
            'status': 'warning',
            'message': 'Behavior testing not yet implemented (requires model inference)'
        }
    
    def _check_provenance_rule(self,
                              rule: Dict[str, Any],
                              metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check data provenance rules."""
        rule_id = rule['id']
        
        data_sources = metadata.get('data_sources', [])
        allowed_sources = rule.get('allowed_sources', [])
        
        if not data_sources:
            return {
                'rule_id': rule_id,
                'status': 'failed',
                'message': 'No data provenance information provided'
            }
        
        # Check if all sources are allowed
        unauthorized = [s for s in data_sources if s not in allowed_sources]
        
        if unauthorized and allowed_sources:
            return {
                'rule_id': rule_id,
                'status': 'failed',
                'message': f"Unauthorized data sources: {', '.join(unauthorized)}"
            }
        
        return {
            'rule_id': rule_id,
            'status': 'passed',
            'message': f"Data provenance verified: {len(data_sources)} sources"
        }
    
    def _calculate_metrics(self,
                          model_path: str,
                          metadata: Dict[str, Any],
                          model_format: str) -> Dict[str, Any]:
        """Calculate model metrics."""
        metrics = {
            'model_size_mb': os.path.getsize(model_path) / (1024 * 1024),
            'format': model_format
        }
        
        # Extract from metadata
        if 'accuracy' in metadata:
            metrics['accuracy'] = metadata['accuracy']
        if 'training_duration_hours' in metadata:
            metrics['training_duration_hours'] = metadata['training_duration_hours']
        if 'data_points' in metadata:
            metrics['data_points'] = metadata['data_points']
        
        return metrics
    
    def _generate_recommendation(self,
                                violations: List[Dict],
                                warnings: List[Dict],
                                metrics: Dict[str, Any]) -> tuple[str, float]:
        """Generate human-readable recommendation."""
        if violations:
            return "REJECT", 0.95
        elif len(warnings) > 3:
            return "NEEDS_REVIEW", 0.75
        elif warnings:
            return "APPROVE_WITH_CONDITIONS", 0.85
        else:
            return "APPROVE", 0.95
