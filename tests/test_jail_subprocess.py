import asyncio
import pytest
from swarmsandbox.jail_subprocess import SubprocessJail
from swarmsandbox.policy import PolicyValidator
from swarmsandbox.types import ResourceLimits, SandboxTimeoutError

def test_subprocess_jail_basic():
    policy = PolicyValidator.default_policy()
    jail = SubprocessJail(policy)
    
    async def run_test():
        return await jail.run(["python", "-c", "print('test')"])
        
    result = asyncio.run(run_test())
    assert result.exit_code == 0
    assert "test" in result.stdout

def test_subprocess_jail_timeout():
    policy = PolicyValidator.default_policy()
    policy.resource_limits.max_cpu_seconds = 0.5
    jail = SubprocessJail(policy)
    
    async def run_test():
        await jail.run(["python", "-c", "import time; time.sleep(2)"])
        
    with pytest.raises(SandboxTimeoutError):
        asyncio.run(run_test())

def test_subprocess_jail_output_limit():
    policy = PolicyValidator.default_policy()
    # Set limit to 1MB
    policy.resource_limits.max_file_size_mb = 1
    jail = SubprocessJail(policy)
    
    async def run_test():
        script = "print('a' * 2 * 1024 * 1024)"
        return await jail.run(["python", "-c", script])
        
    result = asyncio.run(run_test())
    
    # Ensure it's capped at 1MB
    assert len(result.stdout.encode('utf-8')) <= 1 * 1024 * 1024
