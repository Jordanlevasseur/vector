# Local model collaboration

Baseline: 12a03c5. Reuse the existing application, context/semantic retrieval,
source validator, registered portable records, Tk desktop and qualified worker.
No changes to foundational laws, originals, schemas, dependencies or HELIX.

## Inspection findings

The installed desktop starts without inference unless given an explicit model
store. Application has one GenerationConfig and OllamaAdapter. The qualified
worker already isolates Ollama in a private network/user namespace, with seccomp,
read-only model storage, cgroup memory/pids/CPU controls and keep_alive=0.
There is no collaborative controller or conversation-level model preference.
The two installed manifests are in separate stores. Host Ollama is not running;
the application must use its private worker, never start a shared host listener.

Existing arithmetic routes must retain independent checked findings. Existing
source and answer citation validation must retain its requirements. General
model ideas can be recorded as unverified outputs, never inserted as source
claims or approved findings. A model's criticism or agreement is not validation.

## Implementation contract

Discover models through the qualified worker; bind selectable roles to exact
local identifiers. Persist a default mode and independent conversation choices
in registered preferences. Retain the legacy generation preference unchanged.
Single modes use one model; Both uses identical independent tasks/evidence,
reciprocal reviews of the actual outputs, then synthesis. Retain uncertainty and
criticism even if synthesis omits it. Optional bounded extra review requires an
unresolved issue and stops on repeated output or lack of changed criticism.

Use one sequential inference channel. Each generation unloads its runner. Add
verified zero worker swap, host reserve/pressure checks and observed resource
metadata. Do not trim essential prompts or peer outputs to fit; fail explicitly.
Multiple stores are composed only as read-only bind mounts inside the existing
private namespace; never copy, modify or expose private host model directories.

Save the immutable task/configuration/evidence snapshot and every completed or
failed stage. Resume an interrupted run only explicitly, with the original
configuration and model digests, validating completed outputs again. A failed
Both run offers explicit single-model continuation; never invent participation.
No generated text is dispatched as an application command.

Desktop controls use the actual backend, retain three primary destinations,
history and drafts, show phase updates, and expose generated answers/review
summaries separately from the clean final answer. No hidden chain of thought.

## Qualification

Test real dispatch/persistence/recovery, exact shared context, peer handoff,
disagreement, missing models, malformed/truncated replies, cancellation,
sequential unload, source corruption, offline denial and GUI controls. Mock
orchestration tests qualify wiring only. Record separate actual local inference
acceptance and resource measurements; unavailable/blocked tests are not passes.
Never declare release readiness from mocked collaboration or model agreement.

## Backend interface and persistence

`model_modes` discovers qualified local models and reports role availability and
resource blockers. `model_mode_set` accepts mode `a`, `b` or `both`, scope
`conversation` or `default`, and optional validated settings. Settings contain
exact discovered role bindings, synthesis role, 0–2 additional review rounds and
a GenerationConfig with an empty model field. Only role bindings select models.
The UI persists choices via these operations; no production default is silently
chosen. Existing legacy generation preferences remain separate and intact.

`model_run` returns saved outputs and errors. `model_resume` requires explicit
approval and resumes only the original conversation/project, snapshot, model
digests and limits. `model_continue` requires explicit approval and mode `a` or
`b`; it starts a clearly identified single-model child run with the original task
and evidence. A terminated worker requires restarting VECTOR to qualify another
worker before continuation. A context overflow requires a new request with
explicitly larger limits; resumption never silently changes the frozen limits.

The registered `model_runs` contract stores original prompts, their hashes,
ordered stage output/configuration/digest/metrics, failed attempts and explicit
partials. Conversations reference those records. History and restore replay
source attestations, handoff hashes and checked historical findings. Cached
answers cannot override the stage evidence. Review disagreements/uncertainties
remain visible even if the synthesis omits them. Records remain unverified;
there is no automatic source-claim, approval, training or tool action.

Recent conversation history is complete within the operation budget or refused.
Existing annotated semantic retrieval is used when present; source conditions,
conflicts, scoped assumptions and project preferences remain qualified. Up to two
recent conversation/project investigations use existing independently replayed
finding documents. Project relevance uses bounded literal goal overlap and is
explicitly non-exhaustive. No second knowledge store or reasoning engine exists.

## Startup and resource boundaries

The desktop can read a private, owner-controlled
`~/.config/vector/local-inference.json` declaration before applying the core
policy. It contains only `model_directories` (1–8 absolute roots), `memory_bytes`
and `tasks`; no command, URL or executable option is accepted. Explicit isolated
data installations do not inherit it unless passed `--runtime-profile FILE`.
Model roots are composed as verified read-only namespace mounts, with conflicts
rejected. The existing shared host Ollama service is never contacted.

MemoryMax, TasksMax, CPUQuota, namespaces, filesystem restrictions and seccomp
remain required; MemorySwapMax=0 is independently verified. A larger profile
blocked by the existing RAM-plus-384MiB reserve check may start with a stricter
768MiB ceiling and a visible notice. Models whose asset size exceeds that ceiling
are refused before loading. This is a conservative admission rule, not a claim
that disk size is an exact RAM estimate. Requalification/restart is necessary to
increase an already qualified worker ceiling; normal supported mode changes do
not restart the application.

Every generation checks host reserve, OOM events, worker swap, host swap-out and
sustained full-memory pressure. Missing monitoring fails closed. Ollama must
report no loaded runner before and after every generation; keep_alive=0 and
one loaded model/one parallel request remain enforced. Timeout/cancellation
terminates the private worker. No cloud, network fallback or downloaded component
is introduced. These measures do not establish model answer correctness.

The configurable synthesis default is role B, based on the already recorded
Lenovo matched trial (2B 3/4, 0.5B 1/4). That small result is not evidence of
general superiority or a change to VECTOR's active/default model.

## Advanced investigation budgets

A collaboration is five physical invocation attempts, or up to nine with two
additional review/refinement rounds. Existing investigation slices reserve that
bound before starting and charge the actual attempts, including failures. A
one-call slice cannot silently execute Both mode. Its time allowance is shared
across the stages rather than renewed for every model. Checked deterministic
findings remain available when optional generation is paused for insufficient
budget. The existing advanced budget API can explicitly authorize a larger slice;
semantic_answer also accepts model_calls while retaining its default of one.

Managed assets use the existing validated materialization mechanism before
runtime discovery. Catalog entries explicitly distinguish imported assets from
inspected runtime metadata. Required v2 manifest aliases are created only in the
private ephemeral runtime, never by rewriting original model installations.
