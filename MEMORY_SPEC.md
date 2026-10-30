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
