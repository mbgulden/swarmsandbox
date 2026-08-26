import os
import pytest
from swarmsandbox.mount import MountManager
from swarmsandbox.types import MountSpec, SandboxError

def test_mount_manager_prepare_valid():
    manager = MountManager()
    cwd = os.getcwd()
    mounts = [MountSpec(host_path=cwd, sandbox_path="/app")]
    prepared = manager.prepare_mounts(mounts)
    assert len(prepared) == 1
    assert prepared[0].host_path == os.path.abspath(cwd)

def test_mount_manager_path_traversal():
    manager = MountManager()
    mounts = [MountSpec(host_path="../some/path", sandbox_path="/app")]
    with pytest.raises(SandboxError, match="Path traversal not allowed"):
        manager.prepare_mounts(mounts)

def test_scratch_layer_creation_and_cleanup():
    manager = MountManager()
    scratch_dir = manager.create_scratch_layer()
    assert os.path.exists(scratch_dir)
    assert os.path.isdir(scratch_dir)
    
    manager.cleanup()
    assert not os.path.exists(scratch_dir)
