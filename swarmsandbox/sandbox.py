from __future__ import annotations

import asyncio
import platform

from .jail_container import ContainerJail
from .jail_linux import LinuxNamespaceJail
from .jail_subprocess import SubprocessJail
from .jail_windows import WindowsJobJail
from .mount import MountManager
from .policy import PolicyValidator
from .types import SandboxBackend, SandboxPolicy, SandboxResult


class Sandbox:
    """Main facade for the swarmsandbox library."""
    
    def __init__(self, policy: SandboxPolicy | None = None, backend: SandboxBackend = SandboxBackend.AUTO):
        self.policy = policy or PolicyValidator.default_policy()
        
        # Validate policy and print warnings if any
        warnings = PolicyValidator.validate(self.policy)
        for warning in warnings:
            # In a real library, use logging
            print(f"Sandbox Warning: {warning}")
            
        self.backend_type = backend
        self.mount_manager = MountManager()
        self.jail = self._select_backend(backend)
        
    def _select_backend(self, backend: SandboxBackend):
        if backend == SandboxBackend.AUTO:
            os_name = platform.system()
            if os_name == "Windows":
                return WindowsJobJail(self.policy)
            elif os_name == "Linux":
                return LinuxNamespaceJail(self.policy)
            else:
                return SubprocessJail(self.policy)
        elif backend == SandboxBackend.SUBPROCESS:
            return SubprocessJail(self.policy)
        elif backend == SandboxBackend.JOB_OBJECT:
            return WindowsJobJail(self.policy)
        elif backend == SandboxBackend.NAMESPACE:
            return LinuxNamespaceJail(self.policy)
        elif backend == SandboxBackend.CONTAINER:
            return ContainerJail(self.policy)
            
        return SubprocessJail(self.policy)
        
    async def run(self, command: list[str], cwd: str | None = None, 
                  env: dict[str, str] | None = None, stdin: str | None = None) -> SandboxResult:
        """Run a command asynchronously within the sandbox."""
        # Prepare mounts
        if self.policy.mounts:
            # In a full implementation, this would setup the mount bindings
            # before calling the jail's run method
            self.mount_manager.prepare_mounts(self.policy.mounts)
            
        try:
            return await self.jail.run(command, cwd, env, stdin)
        finally:
            # Cleanup any scratch mounts
            self.mount_manager.cleanup()
            
    def run_sync(self, command: list[str], cwd: str | None = None, 
                 env: dict[str, str] | None = None, stdin: str | None = None) -> SandboxResult:
        """Run a command synchronously within the sandbox."""
        return asyncio.run(self.run(command, cwd, env, stdin))
