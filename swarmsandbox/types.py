from dataclasses import dataclass, field
from enum import Enum, auto


class SandboxError(Exception):
    """Base exception for all sandbox-related errors."""


class SandboxTimeoutError(SandboxError):
    """Raised when a sandbox execution exceeds the allotted time limit."""


class SandboxViolationError(SandboxError):
    """Raised when a sandbox execution violates a configured policy."""


@dataclass
class SandboxResult:
    """Represents the outcome of a sandbox execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    sandbox_id: str
    resource_usage: dict[str, float]


@dataclass
class MountSpec:
    """Specifies a file system mount for the sandbox."""
    host_path: str
    sandbox_path: str
    read_only: bool = True


@dataclass
class ResourceLimits:
    """Resource constraints for the sandbox."""
    max_memory_mb: int = 512
    max_cpu_seconds: float = 60.0
    max_processes: int = 32
    max_file_size_mb: int = 100


@dataclass
class NetworkPolicy:
    """Network access configuration."""
    allow_network: bool = False
    allowed_hosts: list[str] = field(default_factory=list)


@dataclass
class SandboxPolicy:
    """Complete security and resource policy for the sandbox."""
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network: NetworkPolicy = field(default_factory=NetworkPolicy)
    mounts: list[MountSpec] = field(default_factory=list)
    env_allowlist: list[str] = field(default_factory=list)
    env_blocklist: list[str] = field(
        default_factory=lambda: ["API_KEY", "SECRET", "TOKEN", "PASSWORD"]
    )


class SandboxBackend(Enum):
    """Available sandbox isolation backends."""
    AUTO = auto()
    SUBPROCESS = auto()
    JOB_OBJECT = auto()
    NAMESPACE = auto()
    CONTAINER = auto()
