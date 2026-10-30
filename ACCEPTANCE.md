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
