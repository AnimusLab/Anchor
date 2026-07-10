import os
import sys
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from anchor.cli import check

def test_sandbox_consent_declined():
    runner = CliRunner()
    
    with patch("anchor.cli.sys") as mock_sys, \
         patch("anchor.core.sandbox.DiamondCage") as mock_cage_class, \
         patch("click.confirm") as mock_confirm:
         
        # Simulate sandbox not installed
        mock_cage = MagicMock()
        mock_cage.is_installed.return_value = False
        mock_cage_class.return_value = mock_cage
        
        # Simulate interactive TTY
        mock_sys.stdin = MagicMock()
        mock_sys.stdin.isatty.return_value = True
        
        # User declines download
        mock_confirm.return_value = False
        
        # Invoke check command
        result = runner.invoke(check, [".", "--no-sign"])
        
        # Verify confirm prompt was displayed and clicked
        mock_confirm.assert_called_with("Download and install now?", default=True)
        assert "Sandbox installation declined. Disabling sandbox-based evaluation." in result.output

def test_sandbox_consent_accepted_success():
    runner = CliRunner()
    
    with patch("anchor.cli.sys") as mock_sys, \
         patch("anchor.core.sandbox.DiamondCage") as mock_cage_class, \
         patch("anchor.core.sandbox.install_diamond_cage") as mock_install, \
         patch("click.confirm") as mock_confirm:
         
        mock_cage = MagicMock()
        mock_cage.is_installed.return_value = False
        mock_cage_class.return_value = mock_cage
        
        mock_sys.stdin = MagicMock()
        mock_sys.stdin.isatty.return_value = True
        
        # User accepts download
        mock_confirm.return_value = True
        # Installation succeeds
        mock_install.return_value = True
        
        result = runner.invoke(check, [".", "--no-sign"])
        
        mock_confirm.assert_called_with("Download and install now?", default=True)
        mock_install.assert_called_once()

def test_sandbox_integrity_verification_failure():
    # Test that a hash mismatch aborts installation in install_diamond_cage
    from anchor.core.sandbox import install_diamond_cage
    
    with patch("os.path.exists") as mock_exists, \
         patch("urllib.request.urlopen") as mock_urlopen, \
         patch("hashlib.sha256") as mock_sha256:
         
        mock_exists.return_value = True
        
        # Mock download response data
        mock_response = MagicMock()
        mock_response.read.return_value = b"corrupted data"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock hasher to return a bad/non-matching hash
        mock_hasher = MagicMock()
        mock_hasher.hexdigest.return_value = "bad_hash_value"
        mock_sha256.return_value = mock_hasher
        
        # Run install - should return False because WasmEdge verification fails
        # (with verbose=True to print errors)
        success = install_diamond_cage(force=True, verbose=True)
        assert success is False
