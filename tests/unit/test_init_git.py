import os
import sys
from unittest.mock import patch, MagicMock
from anchor.cli import init

def test_init_git_confirm_yes():
    # Mocking environment to simulate a Git repository and an interactive terminal
    with patch("os.path.exists") as mock_exists, \
         patch("sys.stdin") as mock_stdin, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("os.makedirs") as mock_makedirs, \
         patch("shutil.copy2") as mock_copy, \
         patch("yaml.safe_load") as mock_yaml_load, \
         patch("yaml.dump") as mock_yaml_dump, \
         patch("click.confirm") as mock_confirm:
         
        # Simulate .git directory exists
        def exists_side_effect(path):
            if path == ".git":
                return True
            if ".anchor" in str(path) or "constitution" in str(path) or "policy" in str(path):
                return False
            return True
            
        mock_exists.side_effect = exists_side_effect
        mock_stdin.isatty.return_value = True
        
        # We mock click.confirm:
        # 1. Enable Git governance checks? (True)
        # 2. Install pre-commit? (True)
        # 3. Create pre-commit config? (True)
        # 4. Would you like to create an initial governance commit? (True)
        mock_confirm.side_effect = [True, True, True, True]
        
        # Call the callback directly to avoid CliRunner overriding sys.stdin
        init.callback(
            domains='',
            frameworks='',
            regulators='',
            sandbox=False,
            all_items=False,
            force=False,
            no_sign=True,
            policy_name='policy.anchor'
        )
        
        # Verify check_calls were called for git add and git commit
        git_add_calls = [
            call for call in mock_check_call.call_args_list 
            if call[0][0][0] == "git" and call[0][0][1] == "add"
        ]
        git_commit_calls = [
            call for call in mock_check_call.call_args_list 
            if call[0][0][0] == "git" and call[0][0][1] == "commit"
        ]
        
        assert len(git_add_calls) > 0
        assert len(git_commit_calls) == 1

def test_init_git_confirm_no():
    with patch("os.path.exists") as mock_exists, \
         patch("sys.stdin") as mock_stdin, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("os.makedirs") as mock_makedirs, \
         patch("shutil.copy2") as mock_copy, \
         patch("yaml.safe_load") as mock_yaml_load, \
         patch("yaml.dump") as mock_yaml_dump, \
         patch("click.confirm") as mock_confirm:
         
        def exists_side_effect(path):
            if path == ".git":
                return True
            if ".anchor" in str(path) or "constitution" in str(path) or "policy" in str(path):
                return False
            return True
            
        mock_exists.side_effect = exists_side_effect
        mock_stdin.isatty.return_value = True
        
        # Enable git checks but decline initial commit
        mock_confirm.side_effect = [True, True, True, False]
        
        init.callback(
            domains='',
            frameworks='',
            regulators='',
            sandbox=False,
            all_items=False,
            force=False,
            no_sign=True,
            policy_name='policy.anchor'
        )
        
        # Verify git commit was NOT called
        git_commit_calls = [
            call for call in mock_check_call.call_args_list 
            if call[0][0][0] == "git" and call[0][0][1] == "commit"
        ]
        
        assert len(git_commit_calls) == 0
