"""
Model Auditor for Anchor-Audit

Validates LLM model weights against Anchor policies.
Vendor-agnostic: Works with LM Studio, AnchorGrid, HuggingFace, OpenAI, etc.

Architecture:
- Plugin system for different model formats
- Universal policy enforcement
- Human-readable report generation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import io
import pickletools
import struct
import yaml
import json
import os
import zipfile
from pathlib import Path

# Pickle globals that give a model file code execution on load. `builtins` is
# only dangerous for a handful of names; the rest are dangerous as a module.
_DANGEROUS_MODULES = {
    "os", "posix", "nt", "subprocess", "sys", "socket", "shutil", "importlib",
    "runpy", "pty", "ctypes", "webbrowser", "pickle", "marshal", "commands",
    "multiprocessing", "code", "codeop",
}
_DANGEROUS_BUILTINS = {"eval", "exec", "compile", "open", "__import__", "input", "getattr", "setattr"}
_DANGEROUS_GLOBALS = {
    ("numpy.testing._private.utils", "runstring"),
    ("torch.utils.bottleneck.__main__", "run_cprofile"),
    ("timeit", "timeit"),
    ("platform", "popen"),
}
_MAX_PICKLE_SCAN_BYTES = 256 * 1024 * 1024


def scan_pickle_stream(stream: "io.BufferedIOBase") -> List[str]:
    """Return dangerous ``module.name`` globals referenced by the pickle(s) in ``stream``.

    Walks the opcode stream with ``pickletools`` (nothing is executed). Legacy
    PyTorch ``.bin`` files contain several consecutive pickles, so scanning
    continues after each STOP. STACK_GLOBAL operands are resolved from the
    preceding string pushes; if they cannot be resolved the global is reported
    as ``<unresolved STACK_GLOBAL>`` rather than assumed safe.
    """
    found: List[str] = []
    scanned = 0
    while scanned < _MAX_PICKLE_SCAN_BYTES:
        start = stream.tell()
        head = stream.read(1)
        if not head or head != b"\x80":  # every protocol >= 2 pickle starts with PROTO
            break
        stream.seek(start)
        strings: List[str] = []
        try:
            for opcode, arg, _pos in pickletools.genops(stream):
                name = opcode.name
                if name in ("SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8", "UNICODE"):
                    strings.append(str(arg))
                    strings = strings[-4:]
                elif name == "GLOBAL":
                    module, _, attr = str(arg).partition(" ")
                    found.extend(_judge_global(module, attr))
                elif name == "STACK_GLOBAL":
                    if len(strings) >= 2:
                        found.extend(_judge_global(strings[-2], strings[-1]))
                    else:
                        found.append("<unresolved STACK_GLOBAL>")
                elif name == "STOP":
                    break
        except Exception:
            break
        scanned += stream.tell() - start
    return found


def _judge_global(module: str, attr: str) -> List[str]:
    top = module.split(".")[0]
    if (module, attr) in _DANGEROUS_GLOBALS:
        return [f"{module}.{attr}"]
    if module == "builtins" or module == "__builtin__":
        return [f"{module}.{attr}"] if attr in _DANGEROUS_BUILTINS else []
    if top in _DANGEROUS_MODULES:
        return [f"{module}.{attr}"]
    return []


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
    # True when no check could actually verify the file (unsupported format, no
    # applicable checks). Callers must not treat such a model as approved.
    unverified: bool = False


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
        
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

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
        
        # 3b. Built-in file-safety checks. These do not depend on any policy
        # rules being loaded, so a model is never "approved" by running zero checks.
        builtin_results = self._builtin_checks(model_path, model_format)
        checks_total += len(builtin_results)
        verifying = 0
        for result in builtin_results:
            if result['status'] == 'passed':
                checks_passed += 1
                verifying += 1
                if self.verbose: print(f"   ✅ {result['id']}: {result['name']}")
            elif result['status'] == 'failed':
                violations.append(result)
                verifying += 1
                if self.verbose: print(f"   ❌ {result['id']}: {result['message']}")
            elif result['status'] == 'warning':
                warnings.append(result)
                checks_passed += 1
                if self.verbose: print(f"   ⚠️  {result['id']}: {result['message']}")
        unverified = (checks_total - len(builtin_results) + verifying) == 0

        # 4. Calculate metrics
        metrics = self._calculate_metrics(model_path, metadata, model_format)
        
        # 5. Generate recommendation
        recommendation, confidence = self._generate_recommendation(
            violations, warnings, metrics
        )
        
        # 6. Determine overall status
        if violations:
            status = AuditStatus.FAILED
        elif warnings or unverified:
            status = AuditStatus.NEEDS_REVIEW
        else:
            status = AuditStatus.PASSED
        if unverified and not violations:
            recommendation, confidence = "NEEDS_REVIEW", 0.5
        
        return AuditResult(
            status=status,
            checks_passed=checks_passed,
            checks_total=checks_total,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            recommendation=recommendation,
            confidence=confidence,
            unverified=unverified,
        )

    def _builtin_checks(self, model_path: str, model_format: str) -> List[Dict[str, Any]]:
        """File-safety checks that need no policy configuration."""
        def result(rule_id, name, status, message=""):
            return {"id": rule_id, "name": name, "status": status, "message": message}

        try:
            if model_format == 'safetensors':
                problem = self._check_safetensors(model_path)
                return [result("MODEL-001", "SafeTensors header is well-formed",
                               "failed" if problem else "passed", problem or "")]
            if model_format == 'gguf':
                problem = self._check_gguf(model_path)
                return [result("MODEL-002", "GGUF header is well-formed",
                               "failed" if problem else "passed", problem or "")]
            if model_format == 'pytorch':
                dangerous = self._scan_pickle_file(model_path)
                if dangerous is None:
                    return [result("MODEL-003", "Pickle payload scan", "warning",
                                   "Could not locate a pickle payload to scan; verify this file manually.")]
                shown = ", ".join(sorted(set(dangerous))[:5])
                return [result("MODEL-003", "No code-execution globals in pickle payload",
                               "failed" if dangerous else "passed",
                               f"Pickle payload imports code-execution callables: {shown}" if dangerous else "")]
        except Exception as exc:  # unreadable / truncated file: do not approve
            return [result("MODEL-000", "File could be inspected", "failed", f"Could not inspect model file: {exc}")]
        return []

    @staticmethod
    def _check_safetensors(path: str) -> Optional[str]:
        size = os.path.getsize(path)
        with open(path, 'rb') as f:
            raw = f.read(8)
            if len(raw) < 8:
                return "File is too small to be a SafeTensors file."
            (header_len,) = struct.unpack('<Q', raw)
            if header_len == 0 or header_len > min(100 * 1024 * 1024, size - 8):
                return f"Invalid SafeTensors header length ({header_len})."
            try:
                header = json.loads(f.read(header_len).decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return "SafeTensors header is not valid JSON."
        if not isinstance(header, dict):
            return "SafeTensors header is not a JSON object."
        data_size = size - 8 - header_len
        for name, info in header.items():
            if name == "__metadata__":
                continue
            offsets = info.get("data_offsets") if isinstance(info, dict) else None
            if (not isinstance(offsets, list) or len(offsets) != 2
                    or not all(isinstance(o, int) for o in offsets)
                    or offsets[0] < 0 or offsets[0] > offsets[1] or offsets[1] > data_size):
                return f"Tensor '{name}' has invalid data_offsets."
        return None

    @staticmethod
    def _check_gguf(path: str) -> Optional[str]:
        with open(path, 'rb') as f:
            head = f.read(8)
        if len(head) < 8 or head[:4] != b"GGUF":
            return "Missing GGUF magic bytes."
        (version,) = struct.unpack('<I', head[4:8])
        if version not in (1, 2, 3):
            return f"Unsupported GGUF version ({version})."
        return None

    @staticmethod
    def _scan_pickle_file(path: str) -> Optional[List[str]]:
        """Dangerous globals in a pickle-based model file, or None if no pickle was found."""
        found: List[str] = []
        payloads = 0
        if zipfile.is_zipfile(path):  # torch >= 1.6 archives
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    if name.endswith('.pkl'):
                        payloads += 1
                        with zf.open(name) as member:
                            found.extend(scan_pickle_stream(io.BytesIO(member.read(_MAX_PICKLE_SCAN_BYTES))))
        else:
            with open(path, 'rb') as f:
                if f.read(1) == b"\x80":
                    payloads = 1
                    f.seek(0)
                    found.extend(scan_pickle_stream(f))
        return found if payloads else None
    
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
            '.onnx': 'onnx',
            '.pkl': 'pytorch',
            '.pickle': 'pytorch',
            '.ckpt': 'pytorch',
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
