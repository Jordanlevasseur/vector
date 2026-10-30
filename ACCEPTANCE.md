# Acceptance requirements
Stage 1: clean local-only installation; mandatory actual kernel denial with a
positive socket control; fail-closed missing-policy startup; independent private
database; migration/restart/log/backup checks. Restricted runner failures are not
host passes. Stage 2: repeated events, original byte reconstruction, revisions,
transaction rollback and process-crash recovery; verified non-overwriting backup
and restore. Stage 3: incremental/rebuilt indexes, source attribution, representative
controlled 10k retrieval/latency measurements. Stage 4: provenance-preserving claim
integration, supported conflicts and explicit override history. Subsequent reasoning,
tools, GUI and release stages require their own measured acceptance. No stage passes
because files or unit tests alone exist. Stage 9 remains unauthorized.

## Measured acceptance through the supported Stage 4 foundation
- Stage 1 checkpoint ac2295e: 10 actual-host tests and clean offline install/startup.
- Stage 2 checkpoint 89a5f68: 21 actual-host tests including crash and recovery.
- Stage 3 checkpoint 1cce94c: 27 tests and controlled 10k measurements (BENCHMARKS.md).
- Final Stage 4/resource-hardening: 43 source and 43 independent installed tests,
  with no skips or expected failures. Kernel positive/denial control is included.
  Dedicated default data is independent from the source tree and HELIX.

This accepts only the documented bounded formats and operations. No general
language extraction, calibrated truth determination, broad scientific reasoning,
embedding retrieval, large-scale corpus qualification, graphical workflow or
inference-service security has passed acceptance. Stage 9 is not authorized.
Upgrade acceptance explicitly covers populated schema-2 originals and a schema-2
backup migrating to schema 4 with unchanged event identity, source bytes and FTS
retrieval. Physical power-loss testing, hostile-host review, inference isolation,
GUI workflows, general NLP and representative multi-source reasoning remain open.

## Mandatory Stage 4.5 gate
PORTABILITY.md defines the new contract. Required acceptance covers complete
populated export/import; exact originals/IDs/duplicate events/revisions/claims/
overrides/registered state/assets; different-location restore and index rebuild;
corrupt/incomplete/unsafe input rejection; real-process interruption recovery;
disk-full rollback; incremental correctness; kernel network denial during transfer;
missing-asset failure; and measured storage growth beyond 10,000 records.
A created archive is not a verified backup. Actual restore verification is required.
Stage 5A cannot rely on unverified portability. GUI/inference/release qualification
remains separate, and skipped optional-dependency tests are never counted as passes.


Final Stage 4.5 source acceptance: 67 passed/no skips; installed acceptance:
66 passed/one explicitly unverified optional-encryption test in .venv. The same
positive encryption test passed on the actual host interpreter. Actual cross-volume
publication, crash/restart, disk-full rollback, unsafe import rejection and transfer
network denial passed. Real schema-4 default data migrated/restored at schema 5
with its original event ID/bytes/hash unchanged. BENCHMARKS.md records the 50k
workload and precise performance-revision boundary. This qualifies the documented
storage operations, not local reasoning, GUI, physical power loss or broad release.
