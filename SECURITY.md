# Security policy and threat model
Supported runtime: `vector` or `python -m vector_core`. Every startup loads a Linux
seccomp filter before configuration, databases, logs, input or model processing.
Kernel rules deny network socket creation (including IPv4, IPv6, raw/Unix), socket
operations, io_uring, new processes/exec, ptrace, process-memory writes, pidfd socket
acquisition and namespace changes. no_new_privs is mandatory. Inherited descriptors
above 2 are closed; socket standard streams are rejected. Failure to install or
verify the filter prevents data operations. There is no disable flag, telemetry,
package download, remote fallback or tool/shell execution path. This is OS syscall
enforcement, not an application URL allowlist. CLI/library internals are not a
sandbox for arbitrary user Python; direct library callers must supply an equivalent
boundary. Trusted Python/interpreter/site startup, the host kernel and the user
account remain prerequisites. Same-user source tampering, privileged attackers,
physical disk destruction and hostile forwarding of ordinary stdio are outside
this boundary. This is not full filesystem confinement of trusted Python.

Only explicitly selected regular input files are read. Traversal/symlinks, device
files, FIFOs, oversized/mutating inputs and unrelated data directories are rejected.
Data must be separate from HELIX and code and private to its owner. No document is
executed or imported. No general document parser, model tools or shell is enabled.
SQLite parameters and bounded operations are required throughout.

Inference is disabled, including loopback: its separate daemon's egress has not
been qualified. VECTOR's filter cannot constrain an already running Ollama service.
Do not weaken host-wide settings or claim inference-service isolation was verified.
Future Unix/loopback inference requires a separately tested OS policy and explicit
profile change. External network denial remains mandatory.

Hashes detect tested corruption; they do not authenticate against an attacker able
to rewrite the database and all backups. Originals have append-only SQL controls,
not immunity to hostile administrators. Restore must never overwrite existing data.

## Final foundation checks
Data ancestors must be owned by the current user or root and must not permit
untrusted-account writes; root-owned sticky temporary directories are permitted.
This prevents other-account path renaming beneath an otherwise private data root.
Original byte counts are checked before materialization; raw object and SQLite
value bounds reject oversized/corrupt inputs. Restore has disk reserve/change
checks and quarantine; backup deadlines cannot produce a complete manifest.

Actual Lenovo acceptance includes a positive unfiltered socket-creation control,
followed by kernel denial of IPv4/IPv6/Unix sockets, inherited descriptor closure
and denied process creation. These are syscall observations, not a packet-capture
study, hostile-host certification or verification of an inference daemon. Separate
inference/display profiles have not been activated or qualified. No host-wide
firewall, shared service or Linux security setting was changed.
