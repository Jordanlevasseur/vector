# Desktop and shared application workflow

`vector-desktop` is a lightweight single-threaded Tk interface with Assistant,
Knowledge, Learning, Projects, Tools and Settings. A separate backend implements the
same real application operations as the CLI. Requests/responses use bounded framed
pipes, explicit identities and a fixed operation allowlist, not shell commands or
model-issued actions. The frontend polls asynchronously so inference, imports and
backups do not block window events. Cancellation interrupts the backend operation;
SQL transactions roll back and incomplete transfers retain their existing recovery
markers. Cancelling inference terminates that worker; restart to qualify a new one.

The frontend establishes exactly one local X11 connection during trusted bootstrap,
then applies a thread-synchronized seccomp profile. New sockets and processes remain
denied. Only the exact preconnected local X11 descriptor may use send/receive syscalls;
peer family/address/credentials are checked. Remote DISPLAY values are rejected before
connection. Explicit FIFO descriptors are retained for the backend and Tk notifier.
The backend independently activates its kernel profile before opening VECTOR data.
Direct library calls are not a security sandbox and must supply their own boundary.

The default launcher works without models. Application-menu actions can select an
explicit local Ollama directory, use imported managed models, or open another private
data folder. No automatic shared-daemon connection occurs. Model selection and budgets
are persistent preferences; runtime isolation is qualified afresh, never trusted from
an imported flag. Selecting external weights records required external dependencies;
complete backups fail until assets are imported. Using external weights again records
those dependencies again. Managed assets are verified into an ephemeral private layout.
Runtime binaries/libraries remain separately installed platform dependencies.

Assistant displays model status, evidence-only fallback, uncertainty, scoped conflicts
and user assumptions, plus clickable source references. Model inferences are labelled
unverified. It does not execute document instructions or automatically promote answers
to claims. Learning archives exact originals, supports the existing deterministic pipe
format, and can ask the selected model for reviewable proposals. Proposal sources,
scopes and spans are bounded to the selected original; explicit user approval is
required before atomic claim application. AI extraction may fail on a small model.

Projects preserve IDs and conversation associations across restarts. Cursor-based
history and project browsing avoid a fixed stored-history count limit. Migration 6
adds only indexes for contract/history/claim lookups; older data and archives migrate
forward. Calculation controls authorize one deterministic operation, with portable
results and versions. Storage, exact original export, recovery, verified backup,
new-only restore, relocation, separate recovery keys and optional encrypted operations
invoke existing Stage 4.5 interfaces. Restore creates a new installation without
silently replacing the running one; use Open Data Folder to select it later.

The menu launcher is installed by `vector-install-desktop`. Existing customized
launchers are preserved rather than overwritten. The launcher is machine integration,
not authoritative user state; reinstall from the matching offline wheel on a new
computer. All project, conversation, preference, tool, proposal and operational-error
state is in registered SQLite contracts and included in complete portable exports.
No model service, host-wide firewall, sysctl or unrelated repository is modified.

Current limitations: local X11/XWayland is required; native Wayland-only profiles are
not qualified. Generated prose is not independently certified truth. The initial
scientific tools do not provide general symbolic algebra or engineering certification.
Model generation and independent evidence/answer qualification are reported separately
from UI/framework tests. UI availability alone does not imply release readiness.
