# Architecture
Python 3.12+, standard library, SQLite/FTS5, Linux libseccomp. No runtime Python
dependencies, external services or HELIX imports. `cli` installs mandatory kernel
policy before config/data operations. `config` owns an independent private data
scope; `intake` reads explicitly selected regular files through no-follow directory
handles; `database` owns transactional migrations and durability. `maintenance`
owns local logs and consistent non-overwriting backups. Memory, retrieval and
knowledge are separate layers built over authoritative originals. Models never
own memory or control authorization. Early stages expose a bounded CLI; a minimal
desktop can follow verified persistence/retrieval. No speculative services.

## Implemented layers through Stage 4
- `memory`: content-addressed originals, immutable submission/revision history and
  extraction status; transactional batches and exact reconstruction.
- `retrieval`: contentless FTS5, literal bounded queries, typed metadata/source/time
  filters, original-validated excerpts and atomic index rebuilding.
- `knowledge`: typed source-span proposals; explicit pipe-format learning; literal
  entities and one-hop relationship retrieval; comparable scoped disagreements;
  versioned user assessments and explicitly authorized scoped operating overrides.
- `benchmark`: resource-checked controlled 10k lexical/provenance/reconstruction
  measurement, not a model or natural-language reasoning evaluation.

Schema migrations 1-4 are forward transactional. Default SQLite page cache is
bounded to 4 MiB and SQLite values to 32 MiB. Original objects are currently bounded
to 16 MiB globally (default ingest 8 MiB); batches to 64 events / 16 MiB. Larger
archives grow by more independent objects, not an unbounded in-memory context.
Future large-object/chunked backends may preserve event/hash contracts.
