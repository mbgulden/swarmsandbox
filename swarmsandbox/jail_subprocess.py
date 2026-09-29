from __future__ import annotations

import asyncio
import os
import time
import uuid
from contextlib import suppress

from .policy import PolicyValidator
from .types import SandboxPolicy, SandboxResult, SandboxTimeoutError


class SubprocessJail:
    """Universal fallback jail using standard library subprocess."""
    
    def __init__(self, policy: SandboxPolicy):
        self.policy = policy
        
    async def run(self, command: list[str], cwd: str | None = None, 
                  env: dict[str, str] | None = None, stdin: str | None = None) -> SandboxResult:
        sandbox_id = str(uuid.uuid4())
        start_time = time.monotonic()
        
        # Merge environment and sanitize
        base_env = os.environ.copy() if env is None else env.copy()
        sanitized_env = PolicyValidator.sanitize_environment(base_env, self.policy)
        
        process = None
        try:
            # We use asyncio subprocess to support timeouts properly
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=sanitized_env
            )
            
            input_bytes = stdin.encode() if stdin else None
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input=input_bytes),
                    timeout=self.policy.resource_limits.max_cpu_seconds
                )
            except asyncio.TimeoutError:
                if process.returncode is None:
                    process.kill()
                    await process.communicate()
                raise SandboxTimeoutError(f"Command timed out after {self.policy.resource_limits.max_cpu_seconds} seconds")
                
            end_time = time.monotonic()
            
            # Simple size limit on output
            max_bytes = self.policy.resource_limits.max_file_size_mb * 1024 * 1024
            stdout_str = stdout_bytes.decode(errors='replace')[:max_bytes]
            stderr_str = stderr_bytes.decode(errors='replace')[:max_bytes]
            
            return SandboxResult(
                exit_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_seconds=end_time - start_time,
                sandbox_id=sandbox_id,
                resource_usage={"cpu_time": end_time - start_time}
            )
            
        except FileNotFoundError as e:
            return SandboxResult(
                exit_code=127,
                stdout="",
                stderr=f"Command not found: {e}",
                duration_seconds=time.monotonic() - start_time,
                sandbox_id=sandbox_id,
                resource_usage={}
            )
        except SandboxTimeoutError:
            raise
        except Exception as e:  # noqa: BLE001 — intentional: convert any unexpected failure into a SandboxResult
            if process and process.returncode is None:
                with suppress(OSError):
                    process.kill()
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Internal sandbox error: {e!s}",
                duration_seconds=time.monotonic() - start_time,
                sandbox_id=sandbox_id,
                resource_usage={}
            )
