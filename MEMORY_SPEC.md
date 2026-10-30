# Permanent memory specification
Original bytes are authoritative. Separate content-addressed blob identity from
submission-event identity: identical input may share bytes but must create distinct
events. Store stable source/event IDs, UTC timestamps, media type, original hash,
metadata, optional revision ancestry and extraction state. Revisions append events
and do not mutate originals. Text extraction is derived and may fail while original
bytes remain retained. All acknowledged batch events commit transactionally with
SQLite synchronous FULL and WAL. Do not claim stronger storage/hardware guarantees
than fsync and SQLite provide. Backups use the SQLite backup API, hashes and a
complete manifest; restores target a new empty location only. Verify original
hashes, references and database consistency. No deletion/compaction of originals
is currently authorized. Working/semantic/procedural memory can be represented as
derived records without separate databases until measured need exists.

## Implemented Stage 2 layout
`blobs` stores SHA-256/body/byte count; `sources` stores stable logical identity;
`events` stores immutable submission/revision metadata and the original per-event
filename. `texts` stores replaceable UTF-8 extraction or explicit failure status.
`audit` records committed event/hash identities, not source content in logs.
One SQLite transaction covers a batch and all derived writes; max 64 events and
16 MiB aggregate, default 8 MiB per original. Restore copies a verified snapshot
to a new private data root, validates SQLite/references/all blob hashes, then
removes its incomplete marker durably. Existing data is never replaced.

Resource hardening checks original byte counts before loading blobs; oversize
corrupt records fail validation rather than entering Python memory. Backups have
an explicit deadline and no complete manifest on timeout. Restore checks available
disk plus reserve and refuses growth/change beyond the initial snapshot size.
Complete hashing is streamed. These are bounded operational safeguards, not a
malicious-administrator or physical-drive reliability guarantee.
Directory creation and the VECTOR identity marker are fsynced before database use,
so a successful database operation does not rely on an unsynced startup marker.
Software crash/rollback checks passed; physical power-loss/drive failure was not
performed and is not certified by those checks.
Write connections explicitly enable recursive triggers to protect originals against
SQLite's implicit DELETE during REPLACE. Corrupt/negative schema versions fail
closed. The local backup directory is on the same disk by default; it is not
independent disaster recovery, and physical disk loss has not been qualified.

## Stage 4.5 permanent portability contract
Migration 5 registers all future persistent subsystems and versioned generic state.
Managed CAS objects stream large originals/assets without a collection count cap.
`external_originals` connects legacy blob hashes to managed content; duplicate
submission events retain identity across both APIs. Exact bytes stay authoritative.
Portable repositories contain a consistent database plus all managed objects;
unknown state and missing/external required assets fail closed. Verified new-only
restoration, encryption policy, relocation, paging, operation bounds, exclusions
and growth strategy are specified permanently in PORTABILITY.md.

New conversations, reasoning traces, configurations, project sessions, model
manifests/assets, learning proposals/approvals, tool runs and desktop errors use
registered portable records. There is no additional side database. Migration 6
adds contract/UUID-prefix cursor and claim lookup indexes. Original bytes and IDs
are preserved. Imported generation/session preferences are validated before portable
activation. Runtime model materializations and scratch/log files are ephemeral;
application launchers and runtime libraries are platform installation dependencies.

MEMORY_INTELLIGENCE_SPEC.md defines derived episodic/semantic/procedural/project/
working views and registered project/source/evidence/reassessment records. These
views preserve originals and earlier revisions; source associations never copy
original bytes. Model-free context and session continuation remain available.

## Literary state
Books and rights metadata use existing immutable original events and managed
objects. Bibliography, curriculum, processing checkpoints, body observations and
linguistic records/links use registered versioned state. Original-source attestation
quotes are checked, including during portable restoration. Derived passage FTS is
rebuildable; source corruption prevents false attribution. Importing the same
provider ID/hash reuses its edition; related translations remain explicit editions.
No summary replaces an original and no curriculum entry establishes proficiency.
