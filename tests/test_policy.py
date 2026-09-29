from swarmsandbox.policy import PolicyValidator
from swarmsandbox.types import MountSpec, ResourceLimits, SandboxPolicy


def test_validate_default_policy():
    policy = PolicyValidator.default_policy()
    warnings = PolicyValidator.validate(policy)
    assert not warnings

def test_validate_warnings():
    policy = SandboxPolicy(
        resource_limits=ResourceLimits(max_memory_mb=-1),
        mounts=[MountSpec(host_path="../test", sandbox_path="/test")]
    )
    warnings = PolicyValidator.validate(policy)
    assert len(warnings) == 2
    assert any("max_memory_mb" in w for w in warnings)
    assert any("Path traversal" in w for w in warnings)

def test_merge_policies():
    base = SandboxPolicy(
        resource_limits=ResourceLimits(max_memory_mb=512),
        env_blocklist=["API_KEY"]
    )
    override = SandboxPolicy(
        resource_limits=ResourceLimits(max_memory_mb=1024),
        env_blocklist=["SECRET"]
    )
    merged = PolicyValidator.merge(base, override)
    assert merged.resource_limits.max_memory_mb == 1024
    assert set(merged.env_blocklist) == {"API_KEY", "SECRET"}

def test_env_sanitization():
    policy = SandboxPolicy(
        env_allowlist=["ALLOWED_VAR"],
        env_blocklist=["API_KEY", "SECRET"]
    )
    env = {
        "ALLOWED_VAR": "value",
        "API_KEY": "hide_me",
        "OTHER_VAR": "will_be_dropped_due_to_allowlist"
    }
    sanitized = PolicyValidator.sanitize_environment(env, policy)
    assert "ALLOWED_VAR" in sanitized
    assert "API_KEY" not in sanitized
    assert "OTHER_VAR" not in sanitized
