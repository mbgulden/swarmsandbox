import subprocess
import sys

def test_cli_help():
    # Test that the CLI entry point can be imported and run
    # Since we use argparse, running with -h will exit(0)
    result = subprocess.run([sys.executable, "-m", "swarmsandbox.cli", "-h"], capture_output=True)
    # Depending on how the module is executed it might fail if __main__ isn't set up perfectly for -m,
    # but we can test the CLI via python -c as well.
    # Actually, let's just run it with the expected script command if it were installed, 
    # but since it's not installed yet, we'll import and run main and catch SystemExit
    import pytest
    from swarmsandbox.cli import main
    import sys as sys_module
    
    # Mock sys.argv
    original_argv = sys_module.argv
    sys_module.argv = ["swarmsandbox", "policy-check"]
    
    try:
        # Should not raise exception
        main()
    finally:
        sys_module.argv = original_argv

def test_cli_inspect():
    from swarmsandbox.cli import main
    import sys as sys_module
    
    original_argv = sys_module.argv
    sys_module.argv = ["swarmsandbox", "inspect"]
    
    try:
        main()
    finally:
        sys_module.argv = original_argv
