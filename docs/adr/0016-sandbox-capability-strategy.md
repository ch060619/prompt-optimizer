# ADR-0016: Cross-Platform Sandbox Capability Strategy

## Status

Accepted for the minimum RC-204 runtime boundary.

## Decision

Expose one `SandboxReport` and `SandboxController` to the process boundary.
Linux uses bubblewrap when detected and builds a command with private PID,
mount, IPC, UTS, and (by default) network namespaces. The workspace is the
only writable project mount and common system directories are read-only mounts.
Windows reuses the existing Job Object process-tree boundary; AppContainer and
per-process ACL token setup are reported as unavailable rather than implied.

When a platform sandbox is unavailable, the controller keeps the application
workspace/symlink boundary but refuses reduced execution until explicit
approval. Callers that require a strong sandbox fail with
`SandboxUnavailable`. `ProcessManager` invokes this check before spawning.

## Non-equivalence

Job Objects constrain process lifetime and resource membership, not filesystem
access. Bubblewrap namespace isolation is not a seccomp policy. Application
path checks are not equivalent to either OS boundary. The report preserves
these distinctions for approval and UI messaging.

## Verification boundary

Tests use simulated Windows/Linux capability reports, traversal/symlink
fixtures, bwrap launch-spec assertions, and a real local reduced-process
lifecycle. No claim is made for a real Linux host, bwrap installation, Windows
AppContainer token, ACL policy, or escape test against an OS sandbox.
