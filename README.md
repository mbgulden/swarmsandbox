# 🧪 SwarmSandbox

[![CI](https://github.com/mbgulden/swarmsandbox/actions/workflows/ci.yml/badge.svg)](https://github.com/mbgulden/swarmsandbox/actions)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/swarmsandbox/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/deps-zero%20runtime-emerald.svg)](https://github.com/mbgulden/swarmsandbox)

> **Cross-platform hermetic process containment for AI agent swarm execution**  
> *One unified `Sandbox` API across Linux namespaces, Windows Job Objects, and containers — with a pure-stdlib subprocess fallback that works everywhere.*

---

## 💡 Why SwarmSandbox?

AI agent swarms (Prismatic agents, Claude Code, Codex, CrewAI, AutoGen) execute **untrusted generated code** all day long:
- Running a candidate patch's test suite on a shared host.
- Letting an agent try shell commands without risking the developer's machine.
- Executing tool calls from a multi-agent swarm where one rogue agent shouldn't sink the fleet.
- Sandboxing benchmark harnesses that run arbitrary third-party submissions.

**SwarmSandbox** gives you a single `Sandbox` facade: pick a policy (resource limits, network off, env scrubbed, mounts locked down), pick a backend (or let `AUTO` choose), and run any command. If the fancy isolation layer isn't available on the current machine, it degrades gracefully to the subprocess jail instead of crashing your swarm.

---

## 🏛️ How It Works

```
                    ┌──────────────────────────────────────────────┐
                    │                Your Agent Loop               │
                    │   Sandbox(policy=policy, backend=AUTO)       │
                    └──────────────────────┬───────────────────────┘
                                           │
                                     1. Policy
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │              PolicyValidator                 │
                    │   - Resource limits (CPU / memory / procs)   │
                    │   - Network policy (default: deny all)       │
                    │   - Env allowlist + blocklist scrubbing      │
                    │   - Mount validation (path-traversal guard)  │
                    └──────────────────────┬───────────────────────┘
                                           │
                               2. Backend selection
                                           ▼
         ┌─────────────┬──────────────┬──────────────┬─────────────┐
         ▼             ▼              ▼              ▼             ▼
      ┌─────┐   ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐
      │AUTO │   │ SUBPROCESS │  │ NAMESPACE │  │JOB_OBJECT│  │ CONTAINER │
      │     │   │ (stdlib,   │  │ (Linux    │  │(Windows) │  │(Docker /  │
      │picks│   │  always    │  │ unshare,  │  │          │  │ Podman,   │
      │per- │   │  works)    │  │  netns    │  │          │  │ alpine)   │
      │OS   │   │            │  │  when     │  │          │  │          │
      └─────┘   └────────────┘  │ avail.)   │  └──────────┘  └───────────┘
                                └───────────┘
```
All backends extend `SubprocessJail`, so isolation layers are **additive** — a backend that can't apply its native mechanism falls back to sanitized subprocess execution with policy enforcement (timeouts, output caps, env scrubbing) intact.

---

## 📦 Installation

```bash
pip install swarmsandbox
```

*Pure Python standard library. Zero runtime dependencies.*

```bash
# With dev/test tooling
pip install "swarmsandbox[dev]"
```

---

## 🚀 Quick Start (< 5 minutes)

### 1. Run a command in a sandbox

```bash
# Echo through the auto-selected backend for this OS
swarmsandbox run echo "hello from the sandbox"

# Pin a backend explicitly
swarmsandbox run --backend subprocess python -c "print('contained')"
```

### 2. Check the default policy

```bash
swarmsandbox policy-check
# Default policy is valid.
```

### 3. Inspect backend capabilities on this machine

```bash
swarmsandbox inspect
# OS: Linux
# Backends supported gracefully: AUTO, SUBPROCESS, JOB_OBJECT, NAMESPACE, CONTAINER
```

### 4. Use the Python API

```python
from swarmsandbox import Sandbox, SandboxBackend, SandboxPolicy, ResourceLimits, MountSpec

# Defaults: 512 MB memory, 60 s CPU, no network, secrets scrubbed from env
sandbox = Sandbox(backend=SandboxBackend.AUTO)

result = sandbox.run_sync(["python", "-c", "print('hello world')"])
print(result.exit_code)   # 0
print(result.stdout)      # hello world
print(result.duration_seconds)

# Secrets never reach the child process
result = sandbox.run_sync(
    ["python", "-c", "import os; print(os.environ.get('API_KEY', 'not_found'))"],
    env={"API_KEY": "sk-live-..."},
)
assert "not_found" in result.stdout
```

---

## 🐍 Python SDK

### `Sandbox` — the facade

```python
from swarmsandbox import Sandbox, SandboxBackend, SandboxPolicy, ResourceLimits, NetworkPolicy

policy = SandboxPolicy(
    resource_limits=ResourceLimits(
        max_memory_mb=512,     # container --memory / advisory
        max_cpu_seconds=60.0,  # hard timeout -> SandboxTimeoutError
        max_processes=32,       # container --pids-limit
        max_file_size_mb=100,  # stdout/stderr capture cap
    ),
    network=NetworkPolicy(allow_network=False, allowed_hosts=[]),
    mounts=[MountSpec(host_path="/data", sandbox_path="/app", read_only=True)],
    env_allowlist=[],                                    # empty = inherit, minus blocklist
    env_blocklist=["API_KEY", "SECRET", "TOKEN"],        # substring match, case-insensitive
)

sandbox = Sandbox(policy=policy, backend=SandboxBackend.AUTO)

# Async
result = await sandbox.run(["pytest", "tests/"], cwd="/repo", stdin="input\n")

# Sync wrapper
result = sandbox.run_sync(["pytest", "tests/"])
```

### `SandboxResult`

| Field | Type | Meaning |
|---|---|---|
| `exit_code` | `int` | Process exit code (`127` = command not found, `-1` = internal error) |
| `stdout` / `stderr` | `str` | Captured output, truncated at `max_file_size_mb` |
| `duration_seconds` | `float` | Wall-clock execution time |
| `sandbox_id` | `str` | UUID for this execution |
| `resource_usage` | `dict` | e.g. `{"cpu_time": 1.23}` |

### `PolicyValidator` — validate, merge, sanitize

```python
from swarmsandbox import PolicyValidator

warnings = PolicyValidator.validate(policy)             # e.g. ["max_memory_mb should be positive"]
merged = PolicyValidator.merge(base_policy, override)   # override wins; lists union
clean_env = PolicyValidator.sanitize_environment(os.environ, policy)
```

`validate()` flags non-positive resource limits and `..` path traversal in mounts, and normalizes the blocklist to uppercase.

### `MountManager` — mounts & scratch layers

```python
from swarmsandbox import MountManager

mgr = MountManager()
prepared = mgr.prepare_mounts([MountSpec(host_path="/data", sandbox_path="/app")])
# raises SandboxError on path traversal or symlink escapes
scratch = mgr.create_scratch_layer()  # temp dir for throwaway work
mgr.cleanup()                         # removes scratch dirs
```

### Exceptions

- `SandboxError` — base class (mount violations, internal errors)
- `SandboxTimeoutError(SandboxError)` — command exceeded `max_cpu_seconds`; the process is killed
- `SandboxViolationError(SandboxError)` — policy violation hook for stricter backends

---

## 🖥️ Backends

| Backend | Class | Mechanism |
|---|---|---|
| `AUTO` | — | Picks per OS: Windows → job objects, Linux → namespaces, else subprocess |
| `SUBPROCESS` | `SubprocessJail` | `asyncio` subprocess + env sanitization, timeout kill, output caps. Works everywhere. |
| `NAMESPACE` | `LinuxNamespaceJail` | Wraps with `unshare -p -f --mount-proc` (+ `-n` netns when network denied). Falls back on non-Linux. |
| `JOB_OBJECT` | `WindowsJobJail` | Windows Job Object containment when the Win32 APIs are available. Falls back otherwise. |
| `CONTAINER` | `ContainerJail` | `docker`/`podman run --rm -i --network none --memory=… --pids-limit=… alpine …`. Falls back when no container CLI is found. |

CLI backend names: `auto`, `subprocess`, `container`, `windows`, `linux`.

> **Honest limits:** in this 0.1.0 release the native layers are thin wrappers — the subprocess jail underneath always enforces timeouts, env scrubbing, and output caps, but true cgroup memory accounting and full mount-namespace isolation are on the roadmap. Don't run actively malicious code and assume the subprocess backend contains it.

---

## ⌨️ CLI Reference

```
swarmsandbox run [--backend auto|subprocess|container|windows|linux] CMD [ARGS...]
    Run a command in a sandbox. Exits with the child's exit code.

swarmsandbox policy-check
    Validate the default policy and print any warnings.

swarmsandbox inspect
    Print OS and gracefully-supported backends on this machine.
```

---

## 🤖 CI / CD Integration (GitHub Actions)

Run agent-generated commands inside a sandbox as part of your own pipelines:

```yaml
- name: Install SwarmSandbox
  run: pip install swarmsandbox

- name: Run untrusted test suite in sandbox
  run: swarmsandbox run --backend auto pytest tests/ --tb=short
```

---

## 🗺️ Prismatic / Swarm Ecosystem

SwarmSandbox is part of the **Prismatic agent-swarm primitives** family:

- 🧪 **SwarmSandbox**: Cross-platform process containment for agent execution *(this repo)*.
- 🛡️ **SwarmProof**: Truth Oracle, evidence ledgers, and anti-hallucination gates.
- 🔒 **SwarmLock**: Tokenized, non-blocking distributed advisory locks.
- ⏱️ **SwarmCron**: Native high-precision background cron scheduling.
- 🔀 **SwarmRouter**: Intelligent query routing and model cascading *(coming soon)*.
- 🧠 **SwarmCurator**: Long-term memory distillation and context compaction *(coming soon)*.

Pair it with **SwarmProof** to get executed-command receipts you can cryptographically verify, and **SwarmLock** to coordinate which agent owns the sandbox at any moment.

---

## 📄 License

MIT © Michael Gulden
