import os
import pathlib
import tempfile
from typing import List, Optional
from .types import MountSpec, SandboxError


class MountManager:
    """Validates and prepares mount specifications for sandboxes."""

    def __init__(self):
        self.temp_dirs = []

    def prepare_mounts(self, mounts: List[MountSpec]) -> List[MountSpec]:
        """Normalize and validate mounts."""
        prepared = []
        for mount in mounts:
            if ".." in mount.host_path or ".." in mount.sandbox_path:
                raise SandboxError(f"Path traversal not allowed: {mount.host_path} -> {mount.sandbox_path}")
                
            # Normalize paths
            host_path = os.path.abspath(os.path.normpath(mount.host_path))
            sandbox_path = os.path.normpath(mount.sandbox_path)

            # Check for symlink resolution to prevent traversal
            if os.path.exists(host_path) and os.path.islink(host_path):
                real_path = os.path.realpath(host_path)
                if not real_path.startswith(os.path.dirname(host_path)):
                     raise SandboxError(f"Symlink escapes restricted path: {host_path} -> {real_path}")

            prepared.append(MountSpec(
                host_path=host_path,
                sandbox_path=sandbox_path,
                read_only=mount.read_only
            ))
        return prepared

    def create_scratch_layer(self, prefix: str = "sandbox_scratch_") -> str:
        """Create a temporary directory to act as a scratch layer."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup(self):
        """Clean up temporary scratch directories."""
        import shutil
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
