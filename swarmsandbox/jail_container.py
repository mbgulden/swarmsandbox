import shutil
from typing import Dict, List, Optional
from .types import SandboxPolicy, SandboxResult
from .jail_subprocess import SubprocessJail

class ContainerJail(SubprocessJail):
    """Container-based isolation using Docker or Podman."""
    
    def __init__(self, policy: SandboxPolicy):
        super().__init__(policy)
        self.container_cli = shutil.which("docker") or shutil.which("podman")
        
    async def run(self, command: List[str], cwd: Optional[str] = None, 
                  env: Optional[Dict[str, str]] = None, stdin: Optional[str] = None) -> SandboxResult:
        
        if self.container_cli:
            # Assemble docker/podman command
            # Using alpine as a default image for execution, though in reality 
            # the image would be parameterized in the policy
            container_cmd = [self.container_cli, "run", "--rm", "-i"]
            
            if not self.policy.network.allow_network:
                container_cmd.extend(["--network", "none"])
                
            # Resource limits
            container_cmd.extend([
                f"--memory={self.policy.resource_limits.max_memory_mb}m",
                f"--pids-limit={self.policy.resource_limits.max_processes}"
            ])
            
            container_cmd.append("alpine")
            container_cmd.extend(command)
            
            # Note: mapping mounts and cwd would require translating host paths 
            # to container paths properly. We omit full mapping here to stay within
            # scope, and gracefully fallback or pass through.
            
            return await super().run(container_cmd, cwd, env, stdin)
            
        # Graceful fallback
        return await super().run(command, cwd, env, stdin)
