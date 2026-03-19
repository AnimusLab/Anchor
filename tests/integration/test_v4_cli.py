import pytest
import os
import shutil
from pathlib import Path
from click.testing import CliRunner
from anchor.cli import cli as main

@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project directory."""
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()
    # Add a dummy file to scan
    (project_dir / "app.py").write_text("import os\nos.system('ls')\n")
    return project_dir

def test_v4_init_regulators(temp_project):
    """
    Verify that anchor init correctly creates the government directory 
    and copies requested regulators.
    """
    runner = CliRunner()
    
    # Change CWD to temp_project
    with runner.isolated_filesystem(temp_dir=temp_project):
        # Run init with a regulator
        result = runner.invoke(main, ["init", "--regulators", "rbi"])
        
        assert result.exit_code == 0
        
        # Check directory structure
        dot_anchor = Path(".anchor")
        assert dot_anchor.exists()
        assert (dot_anchor / "government").exists()
        assert (dot_anchor / "government" / "RBI_Regulations.anchor").exists()
        
        # Verify manifest
        constitution_path = dot_anchor / "constitution.anchor"
        assert constitution_path.exists()
        with open(constitution_path, "r") as f:
            content = f.read()
            assert "namespace: RBI" in content
            # The loader should have marked it active: true if passed via --regulators
            assert "active: true" in content

def test_v4_check_with_federated_rules(temp_project):
    """
    Verify that anchor check correctly loads and applies rules from 
    different domains and regulators.
    """
    runner = CliRunner()
    
    with runner.isolated_filesystem(temp_dir=temp_project):
        # 1. Add dummy code
        Path("app.py").write_text("import os\nos.system('ls')\n")
        
        # 2. Initialize with security domain and RBI regulator
        # Use --no-sign to skip signature generation for faster testing if needed,
        # but we want to test the full flow.
        init_result = runner.invoke(main, ["init", "--domains", "security", "--regulators", "rbi"])
        assert init_result.exit_code == 0, f"Init failed: {init_result.output}"
    
        # 3. Run check
        # Use --verbose to see loader info and bypass sync blocking
        result = runner.invoke(main, ["check", ".", "--verbose"])
        
        # ANC-014 (Shell Injection) should be detected
        assert "ANC-014" in result.output

def test_v4_init_all(temp_project):
    """
    Verify that anchor init --all correctly creates all federated directories
    and copies all available domain, framework, and regulator files.
    """
    runner = CliRunner()
    
    with runner.isolated_filesystem(temp_dir=temp_project):
        result = runner.invoke(main, ["init", "--all"])
        
        assert result.exit_code == 0
        
        dot_anchor = Path(".anchor")
        assert dot_anchor.exists()
        
        # Check domains (9 expected)
        domains_dir = dot_anchor / "domains"
        assert domains_dir.exists()
        # Filter for .anchor files to be safe
        assert len(list(domains_dir.glob("*.anchor"))) == 9
        
        # Check frameworks (3 expected)
        frameworks_dir = dot_anchor / "frameworks"
        assert frameworks_dir.exists()
        # FINOS, NIST, OWASP
        assert len(list(frameworks_dir.glob("*.anchor"))) == 3
        
        # Check regulators (6 expected)
        government_dir = dot_anchor / "government"
        assert government_dir.exists()
        assert len(list(government_dir.glob("*.anchor"))) == 6
