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

The default profile has no inference sockets, including loopback. An already running
shared Ollama service is never treated as isolated. The separately qualified worker
and explicit pipe/display profiles below provide the supported integration; their
qualification does not certify model answer quality. Host-wide settings remain
unchanged and external-network denial remains mandatory.

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
study, hostile-host certification or verification of an inference daemon. At the Stage 4 checkpoint, separate
inference/display profiles had not been activated or qualified; the subsequent
profiles and tests are described below. No host-wide
firewall, shared service or Linux security setting was changed.
VECTOR write connections enable recursive triggers: SQLite REPLACE must not bypass
immutable-table DELETE guards. Actual regression tests verified rejection with
original bytes unchanged. Future/negative migration versions are refused without
rewriting the version. Direct hostile-owner database edits remain outside the
supported write interface and cannot be prevented by in-database triggers alone.

## Portable imports and optional encryption
PORTABILITY.md defines the untrusted import boundary, strict logical paths/schema,
bounded decompression, new-only quarantine and actual restore verification. No
imported capability/model code is executed. Unknown/missing state fails closed.
Managed models are inert until separately qualified offline inference is implemented.
Optional installed cryptography supplies standard AES-256-GCM/HKDF; key absence or
authentication failure never falls back to plaintext. Protect recovery keys on
separate offline media; no recovery exists if all key copies are lost. Plain hash
archives are not adversarially authenticated; encryption does not prevent replay.
All new CLI actions activate the same mandatory kernel offline policy first.

## Stage 5/desktop profiles
The default no-socket/no-process profile is preserved. Explicit FIFO retention uses
`seccomp-offline-ipc-v1`; the desktop uses `seccomp-offline-desktop-v1` with only its
already-connected local X11 descriptor excepted for socket I/O. New sockets/connects
and process creation remain denied. Filtering synchronizes existing threads. Remote
displays are refused before connection and inherited display peers are checked.

A trusted pre-data startup phase may launch a dedicated Ollama worker in fresh
Bubblewrap namespaces under a transient user cgroup. Its network contains loopback
only, external routes are absent, Unix/other socket families and namespace changes
are denied, capabilities are dropped and nested user namespaces are disabled. Host
homes and the shared Ollama home are hidden. The CPU-only profile hides GPU backend
libraries and constrains memory, tasks and aggregate CPU using verified cgroup v2
controls. No RLIMIT_NPROC per-user limit is used. Selected model files are read-only;
metadata/scratch are private bounded tmpfs. Executables must be root-owned installed
programs; startup uses a fixed local user-bus address and sanitized environment.
Qualification is per launch before source data reaches the worker. No unqualified
shared service or cloud fallback is permitted. Source/response validation remains
independent of the model. See INTELLIGENCE_SPEC.md and DESKTOP_SPEC.md for the exact
scope and current model qualification; no hostile privileged-host guarantee is made.

The memory/project upgrade adds no OS permissions or model-callable actions.
User-authored project decisions/hypotheses and evidence relationship labels remain
unverified records. Association/reference and revision validation fail closed;
project scoping only filters/preferentially ranks queries, never removes originals.
Registered new-state payloads are validated during portable restoration. Existing
kernel profiles and local inference qualification remain unchanged.

## Literary ingestion boundary
Literature remains inert untrusted data. Runtime accepts only explicitly approved
local packages with bounded strict metadata, numeric PG identities, content hashes,
regular no-follow object files and edition-specific U.S. rights evidence. DTDs and
entities are rejected; uncertain rights, special copyright notices, incomplete PG
licenses, changed manifests and mismatched source hashes fail closed. Originals
retain the complete attached license; readers expose its full text offline.
All sockets remain denied by the existing kernel policy. Development acquisition
is a separate, authorized provider-mirror operation, absent from the runtime wheel.
Provider assertions and hashes are not publisher signatures or legal adjudication.
Source text cannot approve interpretations, execute commands or change permissions.
