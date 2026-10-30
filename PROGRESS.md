# Verified progress

## Stage 1 — secure foundation
Implemented independent package/configuration, private SQLite WAL/FULL migrations,
append-only audit, bounded local logs, consistent unique backups, explicit bounded
file intake, and mandatory kernel seccomp offline policy. No model dependency.

Lenovo: 10/10 tests passed. Actual unfiltered socket creation was the positive
control; VECTOR then denied socket families and inherited socket/process bypasses.
Fresh `--no-index --no-deps --no-build-isolation` installation and installed CLI
startup passed. Restricted runner: 9 tests passed, one positive-control socket
creation error caused by the runner's own restrictions; not reported as a pass.

No inference daemon policy is qualified, and no model communication is enabled.
No broad filesystem sandbox or hostile-host guarantees are claimed. HELIX was
not read as a code dependency or changed. Next: Stage 2 permanent originals/events.

## Stage 2 — permanent memory
Implemented immutable content-addressed bytes, distinct submission events, per-event
filenames/media/metadata, source identity, revision ancestry, extraction statuses,
transactional bounded batches, integrity checking, exact export, unique backups and
checksum-verified restore into a new location only. Failed restores remain blocked
in quarantine. Binary/invalid UTF-8 originals are retained without false extraction.

Lenovo full suite: 21/21 passed, including actual CLI ingest/list/show/export/backup/
restore, before/after-COMMIT process crashes, deduplicated repeated events, failed
batch rollback, corruption detection, append-only controls and all Stage 1 checks.
No hardware power-loss claim or malicious-administrator authenticity is implied.
Next: Stage 3 incremental lexical retrieval and measured controlled 10k workload.

## Stage 3 — deterministic retrieval
Implemented incremental contentless FTS5, source/time/typed metadata filters,
literal query handling, bounded ranked excerpts with original verification, and
atomic rebuild from originals. CLI search/rebuild is integrated.

Lenovo full suite: 27/27 passed. Controlled 10,000-record benchmark reconstructed
100% of originals and returned correct top-1/source attribution for all ID-bearing
lexical queries. Warm-cache median exact lookup 0.0246 ms; lexical 1.5431 ms;
13,402,112 database bytes; peak process RSS 34,672 KiB. Ingest 38.12 s; rebuild
0.454 s. This does not establish general semantic or factual reasoning ability.
Next: Stage 4 source-linked claims, supported scoped conflict detection and explicit
auditable operating overrides; originals remain unchanged.
