import asyncio
from swarmsandbox.sandbox import Sandbox
from swarmsandbox.types import SandboxBackend

def test_sandbox_run_sync_echo():
    sandbox = Sandbox(backend=SandboxBackend.SUBPROCESS)
    # Using python -c for cross-platform echo
    result = sandbox.run_sync(["python", "-c", "print('hello world')"])
    assert result.exit_code == 0
    assert "hello world" in result.stdout.lower()

def test_sandbox_run_sync_env_scrubbing():
    sandbox = Sandbox(backend=SandboxBackend.SUBPROCESS)
    # python -c "import os; print(os.environ.get('SECRET', 'not_found'))"
    result = sandbox.run_sync(
        ["python", "-c", "import os; print(os.environ.get('SECRET', 'not_found'))"],
        env={"SECRET": "my_secret_key"}
    )
    # The SECRET should be scrubbed by the default policy
    assert "not_found" in result.stdout
