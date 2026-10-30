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
