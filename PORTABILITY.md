# Stage 4.5: portable state and storage

VECTOR remains offline. This format requires a compatible VECTOR application,
Linux seccomp/libseccomp, Python 3.12+ and SQLite/FTS5. Application code, Python,
OS libraries and drivers are platform dependencies, not executable archive content.
The application must be installed from trusted offline media separately.

## Persistent inventory
The SQLite snapshot includes exact legacy originals, immutable submission events,
source identities/revisions/provenance, extracted text/indexes, claims/entities/
relationships, conflicts, assessments, authorized overrides, audit and schema
metadata. Migration 5 adds versioned records for conversations, projects,
procedures, preferences, capabilities, models, adapters and extensions, plus
registered future contracts. These are storage contracts; conversation or model
reasoning features are not thereby implemented. Every managed object and reference
is included, including streamed originals and locally imported inert model files.
Runtime byte-limit preferences are authoritative inside the database and restored
without embedding the previous machine's physical data path.

Future subsystems must register a versioned contract, put durable records in its
SQLite records and import every required file through managed storage. The current
implementation accepts version 1 contracts. Unknown tables/files, unsupported
contract versions, missing/corrupt managed objects and declared external assets
prevent a complete export. This is not an automatic discovery guarantee for
undeclared dependencies outside VECTOR's data root. Model manifests validate
required asset IDs/hashes and runtime/version declarations. No assets are loaded,
executed, downloaded or deemed runtime-qualified by restoration.

Excluded: unrelated home/OS files, credentials, application binaries, machine-local
data-location bindings, SQLite WAL/SHM already represented by the snapshot,
rotating diagnostic logs and recognized same-disk recovery replicas. Authoritative
audit/history in SQLite is included. Existing database-only backup/restore remains
supported for installations without managed objects; it explicitly refuses to
claim that it backs up managed assets. Use export-vector for portable state.

## Supported CLI
Global options precede commands. Paths below are examples, not automatic actions.

```sh
vector --data-dir /private/vector export-vector /media/ssd/vector-backups
vector --data-dir /private/vector verify-export /media/ssd/vector-backups
vector --data-dir /new/private/vector restore-vector /media/ssd/vector-backups
vector --data-dir /private/vector storage
vector --data-dir /private/vector events --limit 1000
vector --data-dir /private/vector move-data /larger/private/vector
vector --data-dir /private/vector import-asset models model-weights /selected/weights.gguf --purpose model-weight
vector --data-dir /private/vector register-model local-model v1 declared-runtime model-weights
```

`import-vector` aliases restore-vector. Restore refuses existing installations.
Interrupted restores retain `.restore-incomplete`; use the identical repository /
snapshot with `--resume`. Normal startup rejects quarantined data. A successful
restore verifies all logical file checksums, SQLite schema/integrity/references,
original hashes and managed content before removing quarantine. `verify-export`
performs a real restore into a new private temporary installation, then removes
only that disposable verification copy. Restoring never executes extension code.

Move serializes supported writers, exports a consistent installation and validates
a new destination before atomically writing a machine-local redirection at the
old location. Previously open writers then refuse writes; new configuration loads
follow validated redirects. Old originals are retained. If interrupted before
redirection, the old location remains active. A completed destination left before
redirection is a preserved recovery copy; retry will refuse overwriting it. Choose
a new location or explicitly review that recovery copy. Supported writers must use
the cooperative lock; arbitrary direct SQL/file modifications are outside this
contract. Neither movement nor export deletes authoritative old data.

## Format, efficiency and recovery
A repository directory contains repository.json, immutable objects, immutable
snapshot catalogues, pending receipts and latest.json. Transfer the whole directory
on removable storage. Publication stages on the destination filesystem before
atomic no-replace linking, so source and repository may be on different volumes.
After an abrupt exit, unreferenced UUID .part files may remain on that backup
volume; they are reproducible transfer fragments and are never activated. Files are fixed logical names (`database`, `object:SHA256`),
never user archive paths. A consistent SQLite backup plus all managed objects is
split into 1 MiB blocks. SHA-256 addressing, exact-content deduplication and zlib
level-1 lossless compression reuse unchanged blocks across snapshots. Distinct
submission events remain distinct. SQLite page churn may change blocks; this is
not a claim of optimal differential backup. Repositories grow until explicitly
retired: no garbage collection or retention deletion is automatic.

Publication is last; interrupted exports cannot masquerade as complete snapshots.
Private snapshot work is under source `portable_work/REPOSITORY/TRANSFER`, and is
removed after durable publication. To resume use `export-vector DEST --resume ID`.
A completed snapshot lost between publication and head update is independently
restored/verified before finalization. An interrupted SQLite snapshot must be
retained for review and a fresh export started; it cannot be used as complete.
A complete object journal can be adopted with `storage-recover`. Incomplete,
unacknowledged input fragments are retained and reported for explicit review;
automatic deletion/resumption of partial source imports is not implemented.

Free-space checks retain max(64 MiB, 1% of volume) reserve. Capacity diagnostics
sample volume free space and provide a recent-growth estimate when possible, not
a guaranteed forecast. SQLite-full errors roll back transactions. Restore checks
capacity conservatively for the full snapshot even on resume; extra free space
may be needed. Snapshot backup/block processing has deadlines; cancelled work
remains unactivated. Existing copies are never overwritten except labelled
incomplete restore work owned by that exact transfer.

There is no application total document/claim/conversation/history count ceiling.
Events and generic records have cursor paging (up to 1000 results per page).
Streamed file ingestion and original export avoid materializing large originals;
managed content is compressed and hashed incrementally. Legacy byte ingestion and
text extraction have explicit 8 MiB default / 16 MiB maximum per-operation bounds,
64-event / 16 MiB batches, bounded metadata and 4000-character evidence spans.
These are resource bounds, not total collection limits. Large originals are
preserved, but full-text indexing above the extraction limit is explicitly deferred.
Pipe-format claim integration streams lines, stores all valid claims atomically,
returns a bounded preview and exposes claim paging. Oversized physical lines are
explicitly skipped, never treated as fully integrated evidence.

Growth path: move to a larger local volume, measure query/index/restore budgets,
then design partitioned local objects/indexes preserving global UUID/hash/provenance
contracts if actual measurements warrant it. No distributed database is introduced.

## Sensitive backups and recovery keys
Plain repositories contain private data in readable/compressed form; protect the
whole volume and permissions. Optional encryption requires the locally installed
`cryptography` package. Missing support fails closed; no install/download or
plaintext fallback occurs. Generate a 32-byte random private key with
`vector create-recovery-key /separate/private/recovery.key`. Pass `--key-file PATH`
to export, restore and verify. Keep key copies on separately protected offline
media outside source data and backup directories. A lost key cannot be recovered;
there is no password reset, embedded key or backdoor.

Encryption uses standard HKDF-SHA256 with random repository salt, AES-256-GCM
per-object authentication with random nonces and repository/context binding, and
HMAC-SHA256 opaque content filenames. Catalogue authentication finishes before
SQLite parsing. Counts, sizes, timing and repository identity remain observable.
Key holders can rewrite archives; encrypted snapshots do not provide independent
anti-rollback protection. Retain snapshot IDs/receipts separately if replay matters.
Same-user source tampering and a hostile privileged OS remain outside this model.

Imports reject traversal, symbolic links, arbitrary logical paths, unknown schema,
malformed metadata, missing files, unsupported settings and bounded decompression
violations. Hashes detect corruption, not a hostile actor rewriting an entire
unencrypted archive. The current format requires compatible application/schema
versions and has no automatic downgrade conversion. Desktop actions now use the separately tested GUI/IPC profile described in
DESKTOP_SPEC.md. Inference/model quality is independently qualified; archive creation
alone does not establish portability, model accuracy or release readiness.

Migration 7 registers project_sources/project_items/memory_links/learning_queue.
Their append-only versions, histories, original IDs, uncertainty, decisions/tasks,
relationships and deferred extraction are included in the existing SQLite snapshot.
Payload/reference validation runs before portable activation. No model, project
archive flag or imported record grants execution authorization. Project archival
is retained status, distinct from exporting the complete VECTOR installation.
