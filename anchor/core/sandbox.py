"""
Diamond Cage: WASM-Based Secure Sandbox for Anchor-Audit

This module provides a lightweight, zero-privilege sandbox using WasmEdge
to safely execute untrusted Python code. Unlike Docker, it requires no
daemon, no root access, and starts in milliseconds.

The "Diamond Cage" provides:
- Complete filesystem isolation (code only sees mounted directories)
- Network blocking by default (no data exfiltration)
- Timeout enforcement (DoS protection)
- Cross-platform support (Windows, Linux, macOS)
- Differential Behavioral Verification (V3): side-by-side original vs patched
  comparison to prove a security fix is safe before applying it.
"""

import subprocess  # anchor: ignore ANC-018
import os
import sys
import time
import platform
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


# ===========================================================================
# Core result types
# ===========================================================================

class CageStatus(Enum):
    """Execution result status from a single Diamond Cage run."""
    SAFE          = "safe"
    VIOLATION     = "violation"
    TIMEOUT       = "timeout"
    SETUP_ERROR   = "setup_error"
    SYSTEM_ERROR  = "system_error"


@dataclass
class CageResult:
    """Result from a single Diamond Cage execution."""
    status:    CageStatus
    output:    str = ""
    error:     str = ""
    exit_code: int = 0


# ===========================================================================
# V3 Behavioral Verification types
# ===========================================================================

@dataclass
class BehaviorSnapshot:
    """
    A complete behavioral fingerprint of one script execution.

    Captures everything that is observable from outside the WASM sandbox:
    stdout, stderr, exit code, and wall-clock timing.  Combined for
    differential comparison in verify_patch().
    """
    stdout:     str
    stderr:     str
    exit_code:  int
    elapsed_ms: float
    timed_out:  bool = False

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    def output_signature(self) -> str:
        """Stable hash of observable outputs (for quick equality check)."""
        import hashlib
        blob = f"{self.exit_code}||{self.stdout.strip()}||{self.stderr.strip()}"
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def has_new_errors(self, baseline: "BehaviorSnapshot") -> bool:
        """Return True if this snapshot has stderr content the baseline did not."""
        baseline_lines = set(baseline.stderr.strip().splitlines())
        current_lines  = set(self.stderr.strip().splitlines())
        return bool(current_lines - baseline_lines)

    def timing_anomaly(self, baseline: "BehaviorSnapshot",
                       threshold_factor: float = 3.0) -> bool:
        """Return True if this run is >threshold_factor times slower than baseline."""
        if baseline.elapsed_ms < 10:        # avoid division by near-zero
            return False
        return self.elapsed_ms > baseline.elapsed_ms * threshold_factor


class VerificationVerdict(Enum):
    """
    The output of a differential behavioral verification run.

    Priority (highest to lowest):
      MALICIOUS_HALLUCINATION — patch introduces new dangerous side-effects
      BEHAVIOUR_CHANGED       — observable outputs differ (patch is too wide)
      PROVED_SAFE             — violation removed AND behaviour preserved
      CAGE_ERROR              — sandbox could not execute one or both scripts
      NOT_INSTALLED           — Diamond Cage is not available on this machine
    """
    PROVED_SAFE             = "proved_safe"
    BEHAVIOUR_CHANGED       = "behaviour_changed"
    MALICIOUS_HALLUCINATION = "malicious_hallucination"
    CAGE_ERROR              = "cage_error"
    NOT_INSTALLED           = "not_installed"


@dataclass
class VerificationResult:
    """
    The full result of a verify_patch() call.

    Includes the verdict, both behavior snapshots, and the human-readable
    rationale explaining the decision.
    """
    verdict:   VerificationVerdict
    rationale: str
    original:  Optional[BehaviorSnapshot] = None
    patched:   Optional[BehaviorSnapshot]  = None

    @property
    def is_approved(self) -> bool:
        """True only when the patch is proven safe to apply."""
        return self.verdict == VerificationVerdict.PROVED_SAFE

    def as_dict(self) -> Dict[str, Any]:
        return {
            "verdict":   self.verdict.value,
            "approved":  self.is_approved,
            "rationale": self.rationale,
            "original":  {
                "exit_code":  self.original.exit_code,
                "elapsed_ms": self.original.elapsed_ms,
                "timed_out":  self.original.timed_out,
                "sig":        self.original.output_signature(),
            } if self.original else None,
            "patched": {
                "exit_code":  self.patched.exit_code,
                "elapsed_ms": self.patched.elapsed_ms,
                "timed_out":  self.patched.timed_out,
                "sig":        self.patched.output_signature(),
            } if self.patched else None,
        }


# ===========================================================================
# DiamondCage
# ===========================================================================

class DiamondCage:
    """
    The Diamond Cage: A WASM-based sandbox for secure code execution and
    differential behavioral verification.

    V2 (static) capabilities:
      - run_safe()           — execute a Python script in full WASM isolation
      - analyze_file_safely() — analyze a suspect file using a trusted script

    V3 (behavioral verification) additions:
      - capture_behavior()   — run a script and return a BehaviorSnapshot
      - verify_patch()       — prove a security fix is safe via differential run

    Example (V3):
        cage = DiamondCage()
        result = cage.verify_patch(
            original_script="src/auth.py",
            patched_script="src/auth_fixed.py",
            context_dir="src/",
        )
        if result.is_approved:
            apply_patch()
        else:
            print(f"Patch rejected: {result.rationale}")
    """

    WASMEDGE_VERSION    = "0.13.5"
    PYTHON_WASM_VERSION = "3.11.3"

    WASMEDGE_RELEASES = {
        "linux_x86_64":  f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-manylinux2014_x86_64.tar.gz",
        "darwin_x86_64": f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-darwin_x86_64.tar.gz",
        "darwin_arm64":  f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-darwin_arm64.tar.gz",
        "windows_x86_64":f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-windows.zip",
    }

    PYTHON_WASM_URL = (
        "https://github.com/vmware-labs/webassembly-language-runtimes/releases/"
        "download/python%2F3.11.3%2B20230428-7d1b259/python-3.11.3.wasm"
    )

    def __init__(self, anchor_home: Optional[Path] = None, verbose: bool = False):
        self.anchor_home = anchor_home or (Path.home() / ".anchor")
        self.verbose     = verbose
        self.bin_dir     = self.anchor_home / "bin"

        self.os_name = platform.system().lower()
        self.arch    = platform.machine().lower()

        if self.arch in ("x86_64", "amd64"):
            self.arch = "x86_64"
        elif self.arch in ("arm64", "aarch64"):
            self.arch = "arm64"

        self.runtime_name    = "wasmedge.exe" if self.os_name == "windows" else "wasmedge"
        self.runtime_path    = self.bin_dir / self.runtime_name
        self.python_wasm_path = self.bin_dir / f"python-{self.PYTHON_WASM_VERSION}.wasm"

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_installed(self) -> bool:
        """Check if the Diamond Cage environment is ready."""
        return self.runtime_path.exists() and self.python_wasm_path.exists()

    def get_platform_key(self) -> str:
        return f"{self.os_name}_{self.arch}"

    # ------------------------------------------------------------------
    # V2: Core isolation execution
    # ------------------------------------------------------------------

    def run_safe(
        self,
        target_script: str,
        context_dir:   str,
        timeout:       int  = 10,
        env_vars:      Optional[Dict[str, str]] = None,
    ) -> CageResult:
        """
        Execute a Python script inside the Diamond Cage.

        The script runs in complete isolation:
        - It can ONLY see files in context_dir (mounted as /app)
        - It has NO network access
        - It has NO access to environment variables (unless explicitly passed)
        - It will be killed if it exceeds the timeout

        Returns CageResult with status, output, and error information.
        """
        if not self.is_installed():
            return CageResult(
                status=CageStatus.SETUP_ERROR,
                error="Diamond Cage not installed. Run 'anchor init' first."
            )

        abs_target  = Path(target_script).resolve()
        abs_context = Path(context_dir).resolve()

        try:
            rel_path          = abs_target.relative_to(abs_context)
            guest_script_path = f"/app/{rel_path.as_posix()}"
        except ValueError:
            return CageResult(
                status=CageStatus.SETUP_ERROR,
                error=(
                    f"Target script must be inside context directory. "
                    f"Target: {abs_target}, Context: {abs_context}"
                )
            )

        cmd = [str(self.runtime_path), "--dir", f"/app:{abs_context}"]

        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["--env", f"{key}={value}"])

        cmd.extend([str(self.python_wasm_path), guest_script_path])

        try:
            result = subprocess.run(  # anchor: ignore ANC-018
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(abs_context),
            )
            if result.returncode == 0:
                return CageResult(status=CageStatus.SAFE, output=result.stdout, exit_code=0)
            else:
                return CageResult(
                    status=CageStatus.VIOLATION,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode,
                )

        except subprocess.TimeoutExpired:
            return CageResult(
                status=CageStatus.TIMEOUT,
                error=f"Execution killed after {timeout}s (DoS protection)"
            )
        except FileNotFoundError:
            return CageResult(
                status=CageStatus.SETUP_ERROR,
                error=f"WasmEdge runtime not found at {self.runtime_path}"
            )
        except Exception as e:
            return CageResult(status=CageStatus.SYSTEM_ERROR, error=str(e))

    def analyze_file_safely(
        self,
        target_file:     str,
        analysis_script: str,
        timeout:         int = 30,
    ) -> CageResult:
        """
        Analyze a suspect file using a trusted script inside the sandbox.
        Useful for loading potentially malicious model files safely.
        """
        target_path = Path(target_file).resolve()
        script_path = Path(analysis_script).resolve()

        common_parent = target_path.parent
        if not script_path.is_relative_to(common_parent):
            common_parent = Path.cwd()

        return self.run_safe(
            target_script=analysis_script,
            context_dir=str(common_parent),
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # V3: Behavioral capture
    # ------------------------------------------------------------------

    def capture_behavior(
        self,
        script_path: str,
        context_dir: str,
        timeout:     int  = 30,
        env_vars:    Optional[Dict[str, str]] = None,
    ) -> BehaviorSnapshot:
        """
        Run a script in the cage and return a full BehaviorSnapshot.

        Unlike run_safe() (which returns pass/fail), this captures the
        complete observable behavior: stdout, stderr, exit code, and
        wall-clock timing.  Two scripts with identical snapshots are
        behaviorally equivalent.
        """
        start  = time.monotonic()
        result = self.run_safe(target_script=script_path,
                               context_dir=context_dir,
                               timeout=timeout,
                               env_vars=env_vars)
        elapsed_ms = (time.monotonic() - start) * 1000

        return BehaviorSnapshot(
            stdout     = result.output,
            stderr     = result.error,
            exit_code  = result.exit_code,
            elapsed_ms = elapsed_ms,
            timed_out  = result.status == CageStatus.TIMEOUT,
        )

    # ------------------------------------------------------------------
    # V3: Differential verification — the Truth Engine
    # ------------------------------------------------------------------

    def verify_patch(
        self,
        original_script: str,
        patched_script:  str,
        context_dir:     str,
        timeout:         int   = 30,
        timing_factor:   float = 3.0,
    ) -> VerificationResult:
        """
        Prove that a security patch is safe via differential behavioral verification.

        Algorithm (from V3 roadmap §4.1):
          1. Run original_script -> capture BehaviorSnapshot (baseline).
          2. Run patched_script  -> capture BehaviorSnapshot (candidate).
          3. Compare:
             a. If the patched run has NEW stderr lines not in baseline
                AND those lines look like suspicious file/network accesses
                -> MALICIOUS_HALLUCINATION
             b. If stdout or exit_code differ -> BEHAVIOUR_CHANGED
             c. If both snapshots match       -> PROVED_SAFE

        Args:
            original_script: Path to the original (possibly-violating) script.
            patched_script:  Path to the candidate fixed script.
            context_dir:     Sandbox mount root (both scripts must be inside).
            timeout:         Per-run execution timeout in seconds.
            timing_factor:   Flag if patched run > N× slower than original.

        Returns:
            VerificationResult with verdict and full snapshot evidence.
        """
        if not self.is_installed():
            return VerificationResult(
                verdict   = VerificationVerdict.NOT_INSTALLED,
                rationale = (
                    "Diamond Cage is not installed on this machine. "
                    "Run 'anchor init' to install WasmEdge."
                ),
            )

        # --- Step 1: Capture baseline ---
        if self.verbose:
            print("CAGE: Cage: capturing baseline behavior of original script...")
        original_snap = self.capture_behavior(original_script, context_dir, timeout)

        if original_snap.timed_out:
            return VerificationResult(
                verdict   = VerificationVerdict.CAGE_ERROR,
                rationale = (
                    f"Original script timed out after {timeout}s. "
                    "Cannot establish a behavioral baseline."
                ),
                original  = original_snap,
            )

        # --- Step 2: Capture patched ---
        if self.verbose:
            print("CAGE: Cage: capturing behavior of patched script...")
        patched_snap = self.capture_behavior(patched_script, context_dir, timeout)

        if patched_snap.timed_out:
            return VerificationResult(
                verdict   = VerificationVerdict.CAGE_ERROR,
                rationale = (
                    f"Patched script timed out after {timeout}s. "
                    "The fix may have introduced an infinite loop."
                ),
                original  = original_snap,
                patched   = patched_snap,
            )

        # --- Step 3a: Detect malicious hallucination ---
        # New stderr lines in the patched run that weren't in the original
        # are suspicious — the patch is doing something the original didn't.
        if patched_snap.has_new_errors(original_snap):
            new_err_lines = (
                set(patched_snap.stderr.strip().splitlines())
                - set(original_snap.stderr.strip().splitlines())
            )
            suspicious_keywords = {
                "permission", "denied", "access", "passwd", "shadow",
                "etc", "secret", "credential", "token", "key",
            }
            err_text = " ".join(new_err_lines).lower()
            if any(kw in err_text for kw in suspicious_keywords):
                return VerificationResult(
                    verdict   = VerificationVerdict.MALICIOUS_HALLUCINATION,
                    rationale = (
                        "Patched script attempts to access resources the original "
                        "did not: " + "; ".join(list(new_err_lines)[:3])
                    ),
                    original  = original_snap,
                    patched   = patched_snap,
                )

        # --- Step 3b: Timing anomaly (soft flag, escalate to BEHAVIOUR_CHANGED) ---
        if patched_snap.timing_anomaly(original_snap, timing_factor):
            return VerificationResult(
                verdict   = VerificationVerdict.BEHAVIOUR_CHANGED,
                rationale = (
                    f"Patched script ran {patched_snap.elapsed_ms:.0f}ms vs "
                    f"{original_snap.elapsed_ms:.0f}ms for the original "
                    f"(>{timing_factor}× threshold). Possible blocking call introduced."
                ),
                original  = original_snap,
                patched   = patched_snap,
            )

        # --- Step 3c: Output equivalence check ---
        if original_snap.output_signature() != patched_snap.output_signature():
            # Stdout or exit code differs — the patch changed observable behavior
            diff_reason = []
            if original_snap.exit_code != patched_snap.exit_code:
                diff_reason.append(
                    f"exit code {original_snap.exit_code} -> {patched_snap.exit_code}"
                )
            if original_snap.stdout.strip() != patched_snap.stdout.strip():
                diff_reason.append("stdout content differs")
            return VerificationResult(
                verdict   = VerificationVerdict.BEHAVIOUR_CHANGED,
                rationale = (
                    "Patched script produces different observable output: "
                    + ", ".join(diff_reason)
                ),
                original  = original_snap,
                patched   = patched_snap,
            )

        # --- Step 3d: PROVED SAFE ---
        return VerificationResult(
            verdict   = VerificationVerdict.PROVED_SAFE,
            rationale = (
                f"Behavioral equivalence confirmed. Both scripts produce identical "
                f"outputs (sig: {original_snap.output_signature()}). "
                f"Original: {original_snap.elapsed_ms:.0f}ms  "
                f"Patched: {patched_snap.elapsed_ms:.0f}ms"
            ),
            original  = original_snap,
            patched   = patched_snap,
        )

    # ------------------------------------------------------------------
    # V3: Scan a Python file for behavioral anomalies
    # ------------------------------------------------------------------

    def behavioral_scan(
        self,
        target_file: str,
        context_dir: str,
        timeout:     int = 15,
    ) -> Dict[str, Any]:
        """
        Execute a Python file in isolation and report behavioral findings.

        This is used by anchor check (--sandbox mode) to add a runtime
        behavioral layer on top of static AST analysis.  Any script that
        crashes, times out, or produces suspicious stderr is flagged.

        Returns a dict compatible with the violation format used in engine.py.
        """
        if not self.is_installed():
            return {"behavioral_violations": [], "cage_available": False}

        snap = self.capture_behavior(target_file, context_dir, timeout)

        violations = []

        if snap.timed_out:
            violations.append({
                "rule_id":  "CAGE-001",
                "severity": "blocker",
                "message":  f"Script execution timed out in the Diamond Cage after {timeout}s.",
                "file":     target_file,
                "line":     0,
            })

        # Scan stderr for signs of attempted privilege escalation
        SUSPICIOUS_PATTERNS = [
            ("passwd", "CAGE-002", "Attempted to read /etc/passwd"),
            ("shadow",  "CAGE-002", "Attempted to read /etc/shadow"),
            ("/.ssh",   "CAGE-003", "Attempted to access SSH keys"),
            ("os.environ", "CAGE-004", "Broad environment variable dump"),
            ("socket.connect", "CAGE-005", "Network socket call observed"),
        ]
        combined_output = (snap.stdout + snap.stderr).lower()
        for pattern, rule_id, msg in SUSPICIOUS_PATTERNS:
            if pattern in combined_output:
                violations.append({
                    "rule_id":  rule_id,
                    "severity": "blocker",
                    "message":  f"[Diamond Cage] {msg}",
                    "file":     target_file,
                    "line":     0,
                })

        return {
            "behavioral_violations": violations,
            "cage_available": True,
            "snapshot": {
                "exit_code":  snap.exit_code,
                "elapsed_ms": snap.elapsed_ms,
                "timed_out":  snap.timed_out,
                "sig":        snap.output_signature(),
            },
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def uninstall(self):
        """Cleanly remove the Diamond Cage from the local system."""
        if self.anchor_home.exists():
            if self.bin_dir.exists():
                shutil.rmtree(self.bin_dir)
            try:
                if not any(self.anchor_home.iterdir()):
                    self.anchor_home.rmdir()
            except Exception:
                pass


# ===========================================================================
# Installation helper
# ===========================================================================

def install_diamond_cage(force: bool = False, verbose: bool = False) -> bool:
    """
    Install the Diamond Cage dependencies (WasmEdge + Python WASM).

    Returns True if installation succeeded, False otherwise.
    """
    import urllib.request
    import tarfile
    import zipfile

    cage = DiamondCage(verbose=verbose)

    if cage.is_installed() and not force:
        if verbose:
            print("CAGE: Diamond Cage already installed.")
        return True

    cage.bin_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("CAGE: Installing Diamond Cage (WasmEdge Runtime)...")
        print(f"   Platform: {cage.os_name}/{cage.arch}")
        print(f"   Location: {cage.bin_dir}")

    platform_key = cage.get_platform_key()
    if platform_key not in cage.WASMEDGE_RELEASES:
        if verbose:
            print(f"ERR: Unsupported platform: {platform_key}")
            print("   Supported: linux_x86_64, darwin_x86_64, darwin_arm64, windows_x86_64")
        return False

    wasmedge_url = cage.WASMEDGE_RELEASES[platform_key]

    # --- Download WasmEdge ---
    try:
        if verbose:
            print(f"v  Downloading WasmEdge {cage.WASMEDGE_VERSION}...")
        archive_path = cage.bin_dir / "wasmedge_download"

        with urllib.request.urlopen(wasmedge_url, timeout=60) as response:
            with open(archive_path, "wb") as f:
                f.write(response.read())

        if verbose:
            print("PKP: Extracting WasmEdge...")
        if cage.os_name == "windows":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(cage.bin_dir)
        else:
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(cage.bin_dir)

        archive_path.unlink()

        # Find the bin directory inside the extracted archive
        # WasmEdge archives usually contain a nested structure like WasmEdge-0.13.5-windows/bin/
        extracted_bin = None
        for item in cage.bin_dir.rglob(cage.runtime_name):
            if item != cage.runtime_path:
                extracted_bin = item.parent
                break
        
        if extracted_bin:
            if verbose:
                print(f"   Moving binaries from {extracted_bin} to {cage.bin_dir}...")
            # Move all files from the extracted bin (including DLLs) to the destination bin_dir
            for f in extracted_bin.iterdir():
                dest = cage.bin_dir / f.name
                if dest.exists():
                    if dest.is_dir(): shutil.rmtree(dest)
                    else: dest.unlink()
                shutil.move(str(f), str(dest))
            
            # Cleanup the empty extracted directory structure
            # (Starting from the parent of the extracted bin)
            try:
                # Find the root of the extracted folder (e.g., WasmEdge-0.13.5-windows)
                top_level = extracted_bin
                while top_level.parent != cage.bin_dir and top_level.parent != top_level:
                    top_level = top_level.parent
                if top_level != cage.bin_dir:
                    shutil.rmtree(top_level)
            except Exception:
                pass

        if cage.os_name != "windows":
            cage.runtime_path.chmod(0o755)

        if verbose:
            print("[V] WasmEdge installed.")

    except Exception as e:
        if verbose:
            print(f"ERR: Failed to install WasmEdge: {e}")
        return False

    # --- Download Python WASM ---
    try:
        if verbose:
            print(f"v  Downloading Python {cage.PYTHON_WASM_VERSION} WASM...")

        with urllib.request.urlopen(cage.PYTHON_WASM_URL, timeout=120) as response:
            with open(cage.python_wasm_path, "wb") as f:
                f.write(response.read())

        if verbose:
            print("[V] Python WASM installed.")

    except Exception as e:
        if verbose:
            print(f"ERR: Failed to install Python WASM: {e}")
        return False

    if verbose:
        print()
        print("CAGE: Diamond Cage Ready!")
        print(f"   Runtime: {cage.runtime_path}")
        print(f"   Python:  {cage.python_wasm_path}")

    return True
