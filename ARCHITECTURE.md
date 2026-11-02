# Architecture
Python 3.12+, standard library, SQLite/FTS5, Linux libseccomp. No mandatory runtime Python
dependencies, external services or HELIX imports. `cli` installs mandatory kernel
policy before config/data operations. `config` owns an independent private data
scope; `intake` reads explicitly selected regular files through no-follow directory
handles; `database` owns transactional migrations and durability. `maintenance`
owns local logs and consistent non-overwriting backups. Memory, retrieval and
knowledge are separate layers built over authoritative originals. Models never
own memory or control authorization. A bounded CLI and lightweight desktop share actual application interfaces.
Inference and display IPC use separately verified profiles; no remote service is used.

## Implemented layers through Stage 4.5
- `memory`: content-addressed originals, immutable submission/revision history and
  extraction status; transactional batches and exact reconstruction.
- `retrieval`: contentless FTS5, literal bounded queries, typed metadata/source/time
  filters, original-validated excerpts and atomic index rebuilding.
- `knowledge`: typed source-span proposals; explicit pipe-format learning; literal
  entities and one-hop relationship retrieval; comparable scoped disagreements;
  versioned user assessments and explicitly authorized scoped operating overrides.
- `benchmark`: resource-checked controlled 10k lexical/provenance/reconstruction
  measurement, not a model or natural-language reasoning evaluation.

Schema migrations 1-5 are forward transactional. `storage` streams compressed,
content-addressed originals/assets; `persistence` owns registered versioned records
and inert model manifests. `portable` snapshots all registered state into immutable,
deduplicated block repositories and restores into quarantine before validation.
`portable_crypto` optionally uses installed cryptography for authenticated encryption;
it never downloads dependencies. `coordination` serializes supported writes and
verified location moves. Machine-local paths are rebound, never imported as code.

SQLite page cache is bounded to 4 MiB and individual SQLite values to 32 MiB.
Byte ingestion/text extraction retains per-operation limits; streamed originals
can be larger. Total collection counts are not capped. Large-document full-text
indexing remains explicitly deferred. PORTABILITY.md defines persistence contracts,
platform dependencies, recovery, encryption policy and tested scope. Future
subsystems must register all authoritative state/assets before claiming portability.

## Inference, reasoning, tools and desktop integration
`inference` defines bounded replaceable adapters; `worker_launcher` and
`inference_worker` implement a separately qualified CPU-only Ollama namespace and
pipe broker. `models` verifies explicit model dependencies and managed runtime
layouts. `context` composes deterministic original-linked evidence; `assistant`
validates citations and records bounded operational reasoning. `reasoning` provides
observable literal task decomposition, not a claim of general semantic planning.
`learning` keeps proposed knowledge separate until explicit atomic approval.
`tools` provides authorized Decimal/SI computations without eval or shell execution.
`service` is the shared actual operation boundary. `desktop` and `desktop_worker`
provide a responsive local GUI and independent protected backend. All durable state
uses the existing registered contracts; migration 6 adds lookup indexes only.
Inference/display profiles are qualified separately from model answer quality.

## Memory intelligence and durable projects
`projects` adds versioned user research records and many-project original links.
`memory_intelligence` coordinates literal memory views, comparison, relationships,
deferred extraction and source reconciliation. Existing context/retrieval/services
and desktop consume them. Migration 7 adds portable contracts and lookup indexes;
no original is replaced and no hidden persistent cache is created. See
MEMORY_INTELLIGENCE_SPEC.md for bounds, interruption semantics and qualification.

## Stage 5D linguistic and literary infrastructure
`languages` owns an extensible 43-target curriculum and sampled script inventory.
`literature` adds strict offline package validation, source/rights editions, resumable
body segmentation, original-verified passage FTS and versioned source attestations.
`literary_analysis` provides literal observations, pending vocabulary proposals,
English-only licensed CMU pronunciation alternatives and historical reading layers.
`library_service` and `library_desktop` reuse the existing protected service, context,
project and evidence interfaces. Migration 8 registers authoritative contracts and
derived schemas; body-analysis contracts register through the existing registry.
No duplicate memory engine, neural training or automatic fact promotion is added.
Developer-only `tools/acquire_pg.py` is outside the runtime package and exposes no
application/model operation. See LINGUISTIC_SPEC.md for limits and rights policy.

## Owner-defined foundational requirements
[FOUNDATIONAL_LAWS.md](FOUNDATIONAL_LAWS.md) V1.0 is the authoritative source for
independent discovery and authenticated owner authority over discretionary judgment.
Its traceability matrix assesses current components, gaps and future joint acceptance
criteria. Current evidence-only contracts and request budgets describe implemented
operations, not permanent cognitive ceilings. Scoped claim assumptions are not a
general authenticated owner-control mechanism. No such mechanism is implemented
by adopting these requirements; existing evidence, offline and authorization
boundaries remain in force. Material normative changes require owner authorization.

## Stage 6A investigation pathway
`investigation` adds renewable checkpointed reasoning slices over existing evidence,
adapters and Decimal tools; `authority` leaves privileged override fail-closed.
The shared service/CLI exposes ordinary approved lifecycle control. Versioned
registered investigation records participate in existing portable validation,
without a schema migration or alternate memory engine. See INVESTIGATION_SPEC.md
and STAGE6A_RESEARCH.md for mechanisms, limits and qualification boundaries.

## Stage 6B qualified source reasoning (experimental)
`semantic` qualifies existing source-linked claims through registered versioned
records, preserving explicit senses, conditions, dates, polarity and epistemic
status. Context/Ask can opt into connected evidence; existing investigations bind
reviewed source quantities to Decimal/SI tools and retain independently replayable
results. The existing service, CLI and desktop opt-in expose these capabilities.
No additional graph database, memory engine, controller, embedding model or SQL
migration is introduced. Runtime defaults remain unchanged. See SEMANTIC_SPEC.md
for interfaces, trust boundaries, bounded operation semantics and evaluation limits.

## Stage6C: checked findings and optional evidence handoff

`findings.py` provides typed views over existing immutable investigation event and
state revisions. There is no second knowledge database, graph, inference service
or schema migration. Source lookups replay pinned semantic interpretations;
calculations replay Decimal/SI tools and their recorded request/dependencies.
Completed outputs are matched against the original plan, not just a `verified`
label. Findings distinguish source support, checked conditional computation,
joined source inference, disputed/unknown results, owner assertions, hypotheses,
and simulation. Source support is never empirical truth certification.

Existing investigation strategies `compose` and `explain` add durable checked
answer events and optional unverified commentary respectively. Composition builds
semantic blocks from checked values/units, premises, joins and uncertainty, with
visible source handles and complete original provenance. It works with inference
disabled. The shared service exposes `semantic_answer`, `investigation_answer`
and paginated `investigation_list`; CLI and desktop expose these records. New
source selection remains explicit trusted-user data, not model-selected actions.
The ordinary chat/default model/experimental connected-evidence toggle is unchanged.

An optional model receives short local handles plus complete dependency facts,
conditions, temporal scope, polarity and disagreements. A fixed server-owned
schema permits a permutation of all findings and up to four explicitly unverified
interpretation/hypothesis notes. No model field can replace checked blocks,
quantities, statuses or citations. Notes are never merged into the authoritative
answer and do not constitute verified inference or execute operations. Oversize
handoffs refuse optional generation entirely; the checked answer remains usable.
No repeated inference or global context growth is introduced.

Portable restore independently replays persisted checked answer records against
pinned history. Later annotation changes/new conflicts leave historical answers
intact; current views warn that a new evaluation is required. Operation budgets
are bounded slices with continuation/selection, not claims of permanent cognitive
capacity limits. Unsupported observation types remain unknown until an independent
finding adapter exists; there is no generic promotion of arbitrary tool/model text.

## Experimental question planner

`planner.py` translates opted-in ordinary questions into the existing durable
investigation DAG: reviewed concept/alias/path grounding, explicit calculations,
checked composition, or explicit unresolved evidence/method requirements.
Historical plan replay and typed finding verification are separate checks.
The shared service, CLI and Assistant expose clarification, resume and optional
unverified neural exploration. Conversation records store durable references;
views are reconstructed from investigation evidence. No schema, default model,
OS security policy or privileged authority changes. See [PLANNING_SPEC.md](PLANNING_SPEC.md)
for trust boundaries, recovery and the tested language scope.
