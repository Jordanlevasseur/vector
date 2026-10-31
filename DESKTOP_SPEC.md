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

Memory/project workflow now includes explicit many-project source associations,
versioned goal/requirement/note/decision/task/milestone/question/hypothesis forms,
archive/reactivate status, histories and evidence-linked item revisions. Opening a
project scopes new submissions by association; global originals remain searchable.
Knowledge offers memory-category/time/project/source recall, duplicate/version
comparison, evidence links, entity lookup and assessment/override history. Learning
shows deferred extraction and explicit reconciliation. Saved-conversation browsing
can resume older sessions. Histories page by both count and response bytes; original
records remain complete. Project timelines summarize conversation entries and link
back to complete saved turns rather than replicating large inference traces.
Context allocates original evidence ahead of notes/history, preventing optional
project records from crowding sources out of small-model budgets.

## Literary workspace
Learning opens the protected literary workspace without replacing existing tabs.
It provides paged title/author/subject/language/known-print-period filters, original
passages and rights, full offline licenses, resumable approved pack import and
processing, errors, body and selected-passage observations, source-linked pending
interpretations/review, typed concept and edition relations, historical layers,
licensed dictionary import and pronunciation references. Project links reuse existing
source associations. Corpus downloads are not an application action. Print dates
unknown in the provider catalog remain unknown and do not match period filters.
Automated local-display checks do not establish human usability or RTL quality.

Source CRLF/CR is normalized only when inserting text into reader/license widgets.
The current passage retains its original quote/character offsets for observations,
interpretations and exact exports. Native regressions use CRLF originals. Statistics
count actual rowids through the existing grouped passage index rather than trusting
processing summaries; partial/reset/rebuild counts remain exact. Real-library GUI
acceptance kept its 60-second wait and asserted all 1,288,804 passages. Cold-cache
and human usability remain separate gates.
