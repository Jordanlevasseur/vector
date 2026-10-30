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
