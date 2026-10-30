# Memory orchestration and project organization

Authoritative originals, event identity, claims, assessments and scoped overrides
retain their existing contracts. This layer organizes their use; it does not train
model weights, certify truth or provide general semantic understanding.

## Durable project state
`projects.Projects` retains existing project IDs/conversations and adds append-only
project status revisions, many-to-many original-event associations, and versioned
items: goals, requirements, notes, decisions, tasks, milestones, unresolved questions
and hypotheses. Items carry original evidence IDs, open/done/blocked/deferred status,
subjective optional confidence and explicit uncertainty. Updating an item requires
its current revision; stale updates fail rather than replacing newer work. Project
archival appends status only. Restoration reactivates the same project ID; no
original, association, conversation or previous item version is deleted.

New state uses registered version-1 `project_sources`, `project_items`, `memory_links`
and `learning_queue` contracts in the existing append-only SQLite records. Migration
7 registers these contracts and adds indexed project/event/target lookups. No side
database or persistent cache is introduced. Source links reference events instead
of copying bytes; one event can belong to any number of projects. Contract payloads
and references are validated on writes and portable export/import. Previous schema
migrations are unchanged. Existing archives remain forward-restorable.

Input preservation commits before optional organization/extraction, following the
existing learning rule. The application acknowledges the combined operation after
linking and recording deferred extraction. If interrupted between commits, the
original remains globally searchable; it may need explicit linking afterwards.
No completion or atomic cross-phase acknowledgement is fabricated. Individual
project item/link/version+audit writes are transactional and writer-coordinated.

## Memory views and retrieval
`memory_intelligence` supplies episodic (original text events), semantic (source-
linked claims), procedural (explicit procedure-kind or procedure-predicate claims), project (explicit
associations) and working (saved conversation questions) views. Names identify
storage/retrieval views, not inferred cognitive understanding. Binary and oversized
originals remain available via original/event browsing; lexical indexing is still
limited to supported extracted UTF-8 text. Total storage counts are not capped;
individual operations and result pages retain explicit resource bounds.

Recall uses literal FTS with explicit source/time/project/category filters. UTC
original occurrence times preserve chronological awareness; timestamps do not prove
when the source's described event happened. Source excerpts now center on a matching
term, with exact original character offsets, instead of always quoting the first
500 characters. Derived text must still match hash-verified originals. Exact hashes
identify duplicate bytes while retaining distinct submissions. Overlap detection
returns bounded literal candidates, never a semantic-duplicate decision. Source
revision ancestry remains explicit; no old version is discarded.

User-authored memory links describe related/supporting/contradicting/overlapping/
revising evidence with a reason and original IDs. Link labels are unverified user
interpretations. Exact entities and one-hop relationships reuse the knowledge
engine; no fuzzy entity merge, embedding search or unrestricted graph traversal.

## Context and continuity
Contexts retain conservative byte budgets and source limits. Original evidence is
allocated before derived claims, history or project notes; optional omitted content
sets the truncation marker. Project sources are
preferred while global evidence remains eligible; project-only filtering must be
explicit. Scoped recall never deletes/hides global originals from global search.
Bounded exact-entity/one-hop expansion, explicit source links and indexed comparable
claim lookups assemble cross-document evidence. User project records with literal
term overlap may contribute their cited originals and explicitly labelled notes,
decisions or hypotheses. Such records do not become source evidence automatically.

The last four saved user questions may provide follow-up context; a short follow-up
can use the preceding question's literal terms for retrieval. Prior generated
answers never become authoritative sources. Cursor browsing/resumption exposes
older sessions instead of replacing them with summaries or imposing a history cap.
Context records include original occurrence dates, relevant claims, assessments,
scoped user assumptions, disagreements and explicit unanswered-evidence notices.
These checks certify attribution and supported literal comparison, not semantic
entailment, calibrated confidence, exhaustive recall or general reasoning.

## Learning/reassessment
Intentionally provided input is retained and model-dependent extraction is recorded
as deferred. Deterministic learning remains explicit. Model proposals keep existing
strict source-span/subject/value/scope validation and human approval. New comparable
exclusive claims produce bounded source-linked reconciliation and a review-needed
queue version. Existing assessments/overrides remain intact; no automatic winner or
verified-fact state is created. Model absence never discards input. Learning,
assessment and override histories remain inspectable. Model output cannot invoke
project mutations, approve proposals, run tools or issue commands.

## Desktop and acceptance
Actual existing tabs now expose project source linking, archival/restoration,
histories, item forms/revisions, category/time/project recall, evidence comparison/
relationships, entity lookup, correction history, deferred extraction and old-session
resumption. Ordinary input uses forms/list selections, with read-only diagnostics;
no manual JSON input or shell operation is required. Existing local-X11 protection,
fixed backend RPC, thread-synchronized seccomp and separately qualified inference
remain mandatory. No cloud/shared-service fallback is introduced.

Acceptance must include independent chronological and late-file recall, duplicate
submission preservation, cross-project reuse, entity-linked conflicts/uncertainty,
stale-write rejection, abrupt process rollback, actual protected desktop workflows,
and complete portable restoration of all new revisions/references. Benchmark warm
literal retrieval/context separately from actual model performance. Qwen0.5B's
previous 0/3 model score remains unqualified; framework acceptance changes no model
accuracy or release gate.

Bulk association uses explicit approved batches of 1–64 source IDs, consistent with
existing bounded intake operations. All new links and audits commit atomically with
SQLite synchronous FULL; a missing reference or interruption rolls the batch back.
Repeated association is idempotent. Larger projects use successive bounded batches;
there is no total project/source count cap. Multi-select Knowledge sources and click
Link selected source to authorize one batch. This avoids one fsync transaction per
source during bulk organization without lowering acknowledgement durability.

Final budget handling can reduce an excerpt around its literal hit while retaining
exact original offsets and setting truncation. Hash/span/quote validation is unchanged.
If even minimum evidence metadata cannot fit, diagnostics distinguish budget omission
from no search match. Working-memory date filters apply to saved turn timestamps;
archived-source filters are explicitly rejected for conversation-only views.

Current project-item context selection inspects the most recent 20 item versions
and includes up to four literal matches. Older items remain fully retained/paged,
but there is no dedicated full-text index over all project-note bodies yet. This
is distinct from the full original-source FTS index and is a remaining milestone.
