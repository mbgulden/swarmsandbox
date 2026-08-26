import os
from copy import deepcopy
from typing import List
from .types import SandboxPolicy, ResourceLimits, NetworkPolicy


class PolicyValidator:
    """Validates and normalizes sandbox policies."""

    @staticmethod
    def validate(policy: SandboxPolicy) -> List[str]:
        """Validate a sandbox policy and return a list of warnings."""
        warnings = []
        if policy.resource_limits.max_memory_mb <= 0:
            warnings.append("max_memory_mb should be positive")
        if policy.resource_limits.max_cpu_seconds <= 0:
            warnings.append("max_cpu_seconds should be positive")

        for mount in policy.mounts:
            if ".." in mount.host_path or ".." in mount.sandbox_path:
                warnings.append(f"Path traversal detected in mount: {mount.host_path} -> {mount.sandbox_path}")

        # Ensure env_blocklist items are uppercase for consistent checking
        policy.env_blocklist = [env.upper() for env in policy.env_blocklist]
        
        return warnings

    @staticmethod
    def merge(base: SandboxPolicy, override: SandboxPolicy) -> SandboxPolicy:
        """Merge two policies with the override taking precedence."""
        merged = deepcopy(base)
        
        # Override ResourceLimits
        if override.resource_limits:
            merged.resource_limits.max_memory_mb = override.resource_limits.max_memory_mb
            merged.resource_limits.max_cpu_seconds = override.resource_limits.max_cpu_seconds
            merged.resource_limits.max_processes = override.resource_limits.max_processes
            merged.resource_limits.max_file_size_mb = override.resource_limits.max_file_size_mb
            
        # Override NetworkPolicy
        if override.network:
            merged.network.allow_network = override.network.allow_network
            if override.network.allowed_hosts:
                merged.network.allowed_hosts = list(set(merged.network.allowed_hosts + override.network.allowed_hosts))

        # Merge Mounts
        if override.mounts:
            merged.mounts.extend(override.mounts)

        # Merge Env
        if override.env_allowlist:
            merged.env_allowlist = list(set(merged.env_allowlist + override.env_allowlist))
        if override.env_blocklist:
            merged.env_blocklist = list(set(merged.env_blocklist + override.env_blocklist))

        return merged

    @staticmethod
    def default_policy() -> SandboxPolicy:
        """Provide sensible default sandbox policy."""
        return SandboxPolicy(
            resource_limits=ResourceLimits(),
            network=NetworkPolicy(allow_network=False),
            mounts=[],
            env_allowlist=[],
            env_blocklist=["API_KEY", "SECRET", "TOKEN", "PASSWORD", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        )

    @staticmethod
    def sanitize_environment(env: dict, policy: SandboxPolicy) -> dict:
        """Sanitize environment variables based on allowlist and blocklist."""
        sanitized = {}
        for key, value in env.items():
            key_upper = key.upper()
            
            # Check blocklist first (case insensitive for keys)
            blocked = False
            for blocked_item in policy.env_blocklist:
                if blocked_item in key_upper:
                    blocked = True
                    break
                    
            if blocked:
                continue
                
            # If allowlist is present, only allow those keys
            if policy.env_allowlist:
                allowed = False
                for allowed_item in policy.env_allowlist:
                    if allowed_item.upper() == key_upper:
                        allowed = True
                        break
                if not allowed:
                    continue
                    
            sanitized[key] = value
            
        return sanitized
