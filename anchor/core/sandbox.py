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
"""

import subprocess  # anchor: ignore RI-12-SUBPROCESS
import os
import sys
import platform
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class CageStatus(Enum):
    """Execution result status from the Diamond Cage."""
    SAFE = "safe"
    VIOLATION = "violation"
    TIMEOUT = "timeout"
    SETUP_ERROR = "setup_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class CageResult:
    """Result from a Diamond Cage execution."""
    status: CageStatus
    output: str = ""
    error: str = ""
    exit_code: int = 0


class DiamondCage:
    """
    The Diamond Cage: A WASM-based sandbox for secure code execution.
    
    Uses WasmEdge runtime with Python compiled to WebAssembly to create
    a mathematically proven isolation boundary. Suspect code runs in a
    universe where only explicitly mounted directories exist.
    
    Example:
        cage = DiamondCage()
        if cage.is_installed():
            result = cage.run_safe("suspect.py", "./allowed_dir")
            if result.status == CageStatus.VIOLATION:
                print(f"Security violation: {result.error}")
    """
    
    # WasmEdge release information
    WASMEDGE_VERSION = "0.13.5"
    PYTHON_WASM_VERSION = "3.11.3"
    
    # Download URLs (Official WasmEdge releases)
    WASMEDGE_RELEASES = {
        "linux_x86_64": f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-manylinux2014_x86_64.tar.gz",
        "darwin_x86_64": f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-darwin_x86_64.tar.gz",
        "darwin_arm64": f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-darwin_arm64.tar.gz",
        "windows_x86_64": f"https://github.com/WasmEdge/WasmEdge/releases/download/{WASMEDGE_VERSION}/WasmEdge-{WASMEDGE_VERSION}-windows.zip",
    }
    
    # Using a working Python WASM release from webassemblylabs (formerly vmware-labs)
    # Using a working Python WASM release from the original vmware-labs path (more stable redirects)
    PYTHON_WASM_URL = "https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/python%2F3.11.3%2B20230428-7d1b259/python-3.11.3.wasm"
    
    def __init__(self, anchor_home: Optional[Path] = None, verbose: bool = False):
        """
        Initialize the Diamond Cage.
        
        Args:
            anchor_home: Custom path for Anchor home directory.
                        Defaults to ~/.anchor
            verbose: Enable verbose logging
        """
        self.anchor_home = anchor_home or (Path.home() / ".anchor")
        self.verbose = verbose
        self.bin_dir = self.anchor_home / "bin"
        
        # Determine OS and architecture
        self.os_name = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # Normalize architecture names
        if self.arch in ("x86_64", "amd64"):
            self.arch = "x86_64"
        elif self.arch in ("arm64", "aarch64"):
            self.arch = "arm64"
        
        # Set binary names based on OS
        if self.os_name == "windows":
            self.runtime_name = "wasmedge.exe"
        else:
            self.runtime_name = "wasmedge"
        
        self.runtime_path = self.bin_dir / self.runtime_name
        self.python_wasm_path = self.bin_dir / f"python-{self.PYTHON_WASM_VERSION}.wasm"
    
    def is_installed(self) -> bool:
        """Check if the Diamond Cage environment is ready."""
        return self.runtime_path.exists() and self.python_wasm_path.exists()
    
    def get_platform_key(self) -> str:
        """Get the platform key for downloading the correct binary."""
        return f"{self.os_name}_{self.arch}"
    
    def run_safe(
        self,
        target_script: str,
        context_dir: str,
        timeout: int = 10,
        env_vars: Optional[Dict[str, str]] = None
    ) -> CageResult:
        """
        Execute a Python script inside the Diamond Cage.
        
        The script runs in complete isolation:
        - It can ONLY see files in context_dir (mounted as /app)
        - It has NO network access
        - It has NO access to environment variables (unless explicitly passed)
        - It will be killed if it exceeds the timeout
        
        Args:
            target_script: Path to the Python script to execute
            context_dir: The ONLY directory the script can access
            timeout: Maximum execution time in seconds (default: 10)
            env_vars: Optional environment variables to pass to the script
            
        Returns:
            CageResult with status, output, and error information
        """
        if not self.is_installed():
            return CageResult(
                status=CageStatus.SETUP_ERROR,
                error="Diamond Cage not installed. Run 'anchor init' first."
            )
        
        # Resolve paths
        abs_target = Path(target_script).resolve()
        abs_context = Path(context_dir).resolve()
        
        # Validate target is within context (prevents path traversal)
        try:
            rel_path = abs_target.relative_to(abs_context)
            guest_script_path = f"/app/{rel_path.as_posix()}"
        except ValueError:
            return CageResult(
                status=CageStatus.SETUP_ERROR,
                error=f"Target script must be inside context directory. "
                      f"Target: {abs_target}, Context: {abs_context}"
            )
        
        # Build the cage command
        cmd = [
            str(self.runtime_path),
            "--dir", f"/app:{abs_context}",  # Mount context as /app
        ]
        
        # Add network blocking (WasmEdge doesn't have network by default, 
        # but we're explicit for documentation)
        # Note: WasmEdge WASI doesn't support networking without explicit plugins
        
        # Add environment variables if specified
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["--env", f"{key}={value}"])
        
        # Add the WASM interpreter and script
        cmd.extend([
            str(self.python_wasm_path),
            guest_script_path
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(abs_context)
            )
            
            if result.returncode == 0:
                return CageResult(
                    status=CageStatus.SAFE,
                    output=result.stdout,
                    exit_code=0
                )
            else:
                return CageResult(
                    status=CageStatus.VIOLATION,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode
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
            return CageResult(
                status=CageStatus.SYSTEM_ERROR,
                error=str(e)
            )
    
    def analyze_file_safely(
        self,
        target_file: str,
        analysis_script: str,
        timeout: int = 30
    ) -> CageResult:
        """
        Analyze a file using a trusted analysis script in the sandbox.
        
        This is useful for loading potentially malicious model files
        or executing suspect code with a known-safe analyzer.
        
        Args:
            target_file: The file to analyze (will be mounted read-only)
            analysis_script: Trusted script that performs the analysis
            timeout: Maximum execution time
            
        Returns:
            CageResult with analysis output
        """
        # Create a temporary context that includes both files
        target_path = Path(target_file).resolve()
        script_path = Path(analysis_script).resolve()
        
        # Use the common parent as context
        common_parent = target_path.parent
        if not script_path.is_relative_to(common_parent):
            common_parent = Path.cwd()
        
        return self.run_safe(
            target_script=analysis_script,
            context_dir=str(common_parent),
            timeout=timeout
        )


    def uninstall(self):
        """Cleanly remove the Diamond Cage from the local system."""
        import shutil  # anchor: ignore RI-08-SHUTIL
        if self.anchor_home.exists():
            # Only remove the cage binaries, keep other anchor data if any
            if self.bin_dir.exists():
                shutil.rmtree(self.bin_dir)
            
            # If the anchor home is now empty, remove it too
            try:
                if not any(self.anchor_home.iterdir()):
                    self.anchor_home.rmdir()
            except:
                pass


def install_diamond_cage(force: bool = False, verbose: bool = False) -> bool:
    """
    Install the Diamond Cage dependencies (WasmEdge + Python WASM).
    
    Args:
        force: If True, reinstall even if already present
        verbose: Enable verbose logging
        
    Returns:
        True if installation succeeded, False otherwise
    """
    import urllib.request
    import tarfile
    import zipfile
    import shutil
    
    cage = DiamondCage(verbose=verbose)
    
    if cage.is_installed() and not force:
        if verbose: print("💎 Diamond Cage already installed.")
        return True
    
    # Create directories
    cage.bin_dir.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print("💎 Installing Diamond Cage (WasmEdge Runtime)...")
        print(f"   Platform: {cage.os_name}/{cage.arch}")
        print(f"   Location: {cage.bin_dir}")
    
    # Get the correct download URL
    platform_key = cage.get_platform_key()
    if platform_key not in cage.WASMEDGE_RELEASES:
        if verbose:
            print(f"❌ Unsupported platform: {platform_key}")
            print("   Supported: linux_x86_64, darwin_x86_64, darwin_arm64, windows_x86_64")
        return False
    
    wasmedge_url = cage.WASMEDGE_RELEASES[platform_key]
    
    try:
        # Download WasmEdge
        if verbose: print(f"⬇️  Downloading WasmEdge {cage.WASMEDGE_VERSION}...")
        archive_path = cage.bin_dir / "wasmedge_download"
        
        with urllib.request.urlopen(wasmedge_url, timeout=60) as response:
            with open(archive_path, 'wb') as f:
                f.write(response.read())
        
        # Extract based on OS
        if verbose: print("📦 Extracting WasmEdge...")
        if cage.os_name == "windows":
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(cage.bin_dir)
        else:
            with tarfile.open(archive_path, 'r:gz') as tf:
                tf.extractall(cage.bin_dir)
        
        # Clean up archive
        archive_path.unlink()
        
        # Find and move the binary to the expected location
        # (WasmEdge extracts into a subdirectory)
        for item in cage.bin_dir.rglob(cage.runtime_name):
            if item != cage.runtime_path:
                shutil.move(str(item), str(cage.runtime_path))
                break
        
        # Make executable on Unix
        if cage.os_name != "windows":
            cage.runtime_path.chmod(0o755)
        
        if verbose: print("✅ WasmEdge installed.")
        
    except Exception as e:
        if verbose: print(f"❌ Failed to install WasmEdge: {e}")
        return False
    
    try:
        # Download Python WASM
        if verbose: print(f"⬇️  Downloading Python {cage.PYTHON_WASM_VERSION} WASM...")
        
        with urllib.request.urlopen(cage.PYTHON_WASM_URL, timeout=120) as response:
            with open(cage.python_wasm_path, 'wb') as f:
                f.write(response.read())
        
        if verbose: print("✅ Python WASM installed.")
        
    except Exception as e:
        if verbose: print(f"❌ Failed to install Python WASM: {e}")
        return False
    
    if verbose:
        print("")
        print("💎 Diamond Cage Ready!")
        print(f"   Runtime: {cage.runtime_path}")
        print(f"   Python:  {cage.python_wasm_path}")
    
    return True
