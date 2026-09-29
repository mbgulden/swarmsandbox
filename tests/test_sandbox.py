import os
import sys

from swarmsandbox.sandbox import Sandbox
from swarmsandbox.types import SandboxBackend


def test_sandbox_run_sync_echo():
    sandbox = Sandbox(backend=SandboxBackend.SUBPROCESS)
    # Using sys.executable for cross-platform reliability ("python" may not be on PATH)
    result = sandbox.run_sync([sys.executable, "-c", "print('hello world')"])
    assert result.exit_code == 0
    assert "hello world" in result.stdout.lower()

def test_sandbox_run_sync_env_scrubbing():
    sandbox = Sandbox(backend=SandboxBackend.SUBPROCESS)
    # sys.executable -c "import os; print(os.environ.get('SECRET', 'not_found'))"
    # NOTE: pass a full, realistic environment (like a real caller would) —
    # a stripped-down env breaks child startup on some platforms
    # (e.g. WinError 87 with an empty env block, hash-seed init failures).
    env = os.environ.copy()
    env["SECRET"] = "my_secret_key"
    result = sandbox.run_sync(
        [sys.executable, "-c", "import os; print(os.environ.get('SECRET', 'not_found'))"],
        env=env,
    )
    # The SECRET should be scrubbed by the default policy
    assert "not_found" in result.stdout
