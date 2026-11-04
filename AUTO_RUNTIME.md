# Automatic local model management

AUTO is the normal desktop default. Discovery reads bounded metadata only in
previously approved local model roots. It neither downloads nor contacts a
registry. Manual exact model, A, B and Both selections remain available. Existing
model bindings and histories are retained. AUTO is a separate preference; saved
execution records continue to pin exact A/B roles and original prompts.

The hardware policy reads RAM, available memory, swap, CPU affinity/features,
cgroup ancestors, memory pressure, storage and GPU descriptors. CPU is the only
qualified backend. GPU detection does not authorize devices. Runtime limits are
finite: memory after host reserve, zero worker swap, per-service pids/CPU caps,
one loaded runner, task-sized context/output/time and live pressure/OOM monitoring.
Previously measured peaks can raise estimates, never erase the weight floor.
Functional evidence and task capabilities are distinct from accuracy evaluations.
Model size is only a provisional preference among otherwise comparable candidates;
no claim of model quality is inferred from parameter count.

A small controller starts before the core's strict seccomp filter. It has a private
network/user namespace, no IP sockets, no host process directories, no VECTOR data
mount, no new user namespaces, read-only code/model mounts and a fixed local
user-manager connection. The core retains pipes, not network or execution access.
The controller accepts only named operations and models in approved roots, never
commands, paths, endpoints or environment variables. Host-root-owned executable
fingerprints are captured before user-namespace entry and checked again inside.
Each inference service retains the existing complete qualification and its own
namespace, cgroup and seccomp filter. BindsTo terminates workers if their controller
exits. Stop verifies service/cgroup cleanup before a replacement can start.

AUTO expands context for the complete current request when a model and safe budget can support it; required instructions are never shortened. Manual profile ceilings can grow with actual host/cgroup RAM and are clamped again at launch, rather than retaining the old fixed2GiB assumption.

The first message verifies complete selected-model SHA dependencies, starts the
private runtime, independently checks isolation/cgroups, inspects local runtime
metadata and generates. Ollama v2 selector digests are linked to the original
manifest graph; both are retained. Actual runtime identity must match one of
these verified identities. Unrelated corrupt models do not enter the selected
runtime overlay. Unknown/incompatible packages stay visible with their reason.

AUTO fallback creates distinct parent-linked execution records with the same
complete request/evidence. At most three distinct candidates and one transient
worker restart are allowed. Only actual resource or worker failures trigger it.
Cancellation, inaccurate answers, invalid outputs and integrity/qualification
failures do not trigger model substitution. Manual selection never substitutes.
A later message may qualify a fresh worker after failure or cancellation.

No new model-root permission is silently granted. An unapproved directory still
needs one explicit local grant. Existing root declarations persist. External model
portability obligations remain recorded automatically when used; those notices
are not internet permissions. Existing experimental consent remains scoped to
manual attempts and must be explicitly acknowledged in private runtime settings.
AUTO never turns it on. The existing profile's memory ceiling remains a hard cap for manual inference; AUTO derives its own finite hardware ceiling. The configured process ceiling applies to both. No saved manual limit is silently ignored. Applying a new grant/profile still requires a new protected
startup; ordinary model changes and worker recovery do not require reopening.

Plans allow arbitrary named sequential participants. The current executor retains
two roles and five-stage Both collaboration. AUTO conservatively selects a single
model; automatic collaboration/parallel/GPU execution awaits separate real local
qualification. Managed-model launch/import remains available through its existing
explicit workflow. Actual results and limits are recorded in the workspace report;
policy simulations are never inference acceptance results.

Controller diagnostics use a third explicit pipe, never a desktop socket or
execution exemption. An EOF clears qualification and preserves bounded stderr;
cancellation cannot replace the original diagnostic. A service-stop failure keeps
the exact unverified unit identity and prevents replacement until cleanup succeeds.
A controller-process crash itself requires a fresh application startup; ordinary
worker failures, stops and cancellations can recover within the current session.
