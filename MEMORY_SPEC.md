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
