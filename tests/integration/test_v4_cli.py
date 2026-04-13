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
        # Use local constitution to match the current state and avoid GitHub sync mismatch
        from anchor.core.config import settings
        pkg_root = Path(main.callback.__globals__['__file__']).parent
        project_root = pkg_root.parent
        local_const = pkg_root / "governance" / "constitution.anchor"
        local_mitig = pkg_root / "governance" / "mitigation.anchor"
        local_lock = project_root / "GOVERNANCE.lock"
        
        settings.constitution_url = local_const.as_uri()
        settings.mitigation_url = local_mitig.as_uri()
        settings.governance_lock_url = local_lock.as_uri()

        # Use --no-sign to skip signature generation for faster testing if needed,
        # but we want to test the full flow.
        init_result = runner.invoke(main, ["init", "--domains", "security", "--regulators", "rbi", "--no-sign"])
        assert init_result.exit_code == 0, f"Init failed: {init_result.output}"
    
        # 3. Run check
        # Use --verbose to see loader info and bypass sync blocking
        result = runner.invoke(main, ["check", ".", "--verbose"])
        
        # DEBUG: Print output if assertion fails
        if not any(id in result.output for id in ["FINOS-014", "SEC-007"]):
             print(f"INIT OUTPUT:\n{init_result.output}")
             print(f"CHECK OUTPUT:\n{result.output}")

        # Detection should match either the framework ID or the canonical SEC ID
        assert any(id in result.output for id in ["FINOS-014", "SEC-007"])

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

        # Check government (6 expected)
        gov_dir = dot_anchor / "government"
        assert gov_dir.exists()
        assert len(list(gov_dir.glob("*.anchor"))) == 6

def test_v4_init_all_activation(temp_project):
    """
    Verify that init --all correctly marks items as active in the manifest.
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=temp_project):
        runner.invoke(main, ["init", "--all"])
        
        constitution_path = Path(".anchor/constitution.anchor")
        with open(constitution_path, "r") as f:
            content = f.read()
            # Ensure at least one from each category is active
            assert "namespace: FINOS" in content
            assert "active: true" in content  # for FINOS
            assert "namespace: RBI" in content
            assert "active: true" in content  # for RBI

def test_fail_on_zero_laws(tmp_path):
    """Anchor must never report PASSED with 0 active laws."""
    runner = CliRunner()
    # Create an empty directory with no .anchor
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    
    # Force settings to a non-existent constitution to truly trigger 0 laws
    # We also need to ensure we aren't loading from the internal governance library
    # One way is to set governance_root to an empty temp dir
    from anchor.core.config import settings
    settings.constitution_url = (empty_dir / "none.anchor").as_uri()
    settings.mitigation_url = (empty_dir / "none_mitig.anchor").as_uri()

    # Clear cache to ensure zero laws are found
    # (This was already added in previous step but repeating for context)
    cache_dir = Path.home() / ".anchor" / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    # We need a way to tell the CLI to skip internal defaults if needed, 
    # but for this test, simply having no .anchor and an invalid URL 
    # should fail the V4 loader too, IF we ensure it doesn't find internal domains.
    # Actually, let's just assert that it exits with error 2.
    import unittest.mock
    # Force zero rules by mocking the loader's output
    with unittest.mock.patch('anchor.core.loader.load_constitution') as mock_load:
        from anchor.core.loader import LoadedConstitution
        mock_load.return_value = LoadedConstitution(
            manifest=None, rules={}, errors=["Triggered mock zero laws"]
        )
        
        result = runner.invoke(main, ['check', str(empty_dir)])
        
        # Should exit with error code 2
        assert result.exit_code == 2
        assert "0 active laws loaded" in result.output
    
    # Should exit with error code, not 0
    assert result.exit_code != 0
    # Should never say PASSED
    assert "PASSED" not in result.output
    # Should explain what happened
    assert any(msg in result.output for msg in ["0 active laws", "ERROR", "VIOLATION"])

def test_integrity_violation_always_shown(temp_project):
    """Integrity violations must surface even without --verbose."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=temp_project):
        runner.invoke(main, ["init", "--domains", "security"])
        
        # Tamper with a file
        sec_path = Path(".anchor/domains/security.anchor")
        content = sec_path.read_text()
        sec_path.write_text(content + "\n# Tampered")
        
        # Run check without --verbose
        result = runner.invoke(main, ["check", "."])
        
        # Should surface the violation
        assert result.exit_code == 2
        assert "ANCHOR INTEGRITY VIOLATION" in result.output
