from __future__ import annotations

import platform

from .jail_subprocess import SubprocessJail
from .types import SandboxPolicy, SandboxResult


class WindowsJobJail(SubprocessJail):
    """Windows-specific containment using Job Objects."""
    
    def __init__(self, policy: SandboxPolicy):
        super().__init__(policy)
        # Note: Proper Job Object implementation requires ctypes or pywin32.
        # For this hermetic standard library implementation, we rely on the SubprocessJail
        # fallback as requested when actual Job Object APIs are not accessible without extensions.
        # In a real environment with win32api installed, we'd use CREATE_BREAKAWAY_FROM_JOB
        # and assign process to a restricted job object.
        self.is_windows = platform.system() == "Windows"
        
    async def run(self, command: list[str], cwd: str | None = None, 
                  env: dict[str, str] | None = None, stdin: str | None = None) -> SandboxResult:
        # Fall back to standard SubprocessJail behavior gracefully
        return await super().run(command, cwd, env, stdin)
