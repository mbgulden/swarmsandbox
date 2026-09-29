from __future__ import annotations

import platform
import shutil

from .jail_subprocess import SubprocessJail
from .types import SandboxPolicy, SandboxResult


class LinuxNamespaceJail(SubprocessJail):
    """Linux namespace isolation jail."""
    
    def __init__(self, policy: SandboxPolicy):
        super().__init__(policy)
        self.is_linux = platform.system() == "Linux"
        self.has_unshare = shutil.which("unshare") is not None
        
    async def run(self, command: list[str], cwd: str | None = None, 
                  env: dict[str, str] | None = None, stdin: str | None = None) -> SandboxResult:
        
        # If we have unshare and are on linux, we could wrap the command
        if self.is_linux and self.has_unshare:
            # Very basic namespace wrapping as an example
            unshare_cmd = ["unshare", "-p", "-f", "--mount-proc"]
            if not self.policy.network.allow_network:
                unshare_cmd.append("-n") # network namespace
            
            wrapped_command = unshare_cmd + command
            return await super().run(wrapped_command, cwd, env, stdin)
            
        # Graceful fallback
        return await super().run(command, cwd, env, stdin)
