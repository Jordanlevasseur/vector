# Roadmap
1. Secure foundation: independent runtime, config, migrations, kernel offline
   policy, diagnostics, tests and backup foundations. Host acceptance required.
2. Permanent memory: transactional immutable original bytes, event identity,
   provenance/revisions, hashes, duplicate events, exact reconstruction, verified
   backup/restore and crash tests.
3. Retrieval: incremental FTS5, exact/metadata/temporal/source search, rebuilds,
   provenance and controlled 10,000-fact measurements.
4. Knowledge: source-linked claims, entities/relations, supported scoped conflicts,
   assessments and overrides; never automatic truth or discarded raw input.
4.5. Mandatory portability and scalable storage: registered state, exact offline
   export/restore, managed models/assets, incremental backup, verified crash/full
   disk recovery, larger-volume moves and measured growth beyond 10k. Permanent
   acceptance gate for all later subsystems; see PORTABILITY.md.
5. Reasoning: bounded evidence/context interfaces and separately secured local
   inference. No unsafe connection to an unqualified inference daemon.
6. Deterministic scientific tools with checked units and bounded operation.
7. Desktop: ingestion, sources, search, knowledge, health; no voice work.
8. Qualification: representative reliability/resource/retrieval benchmarks.
9. HELIX integration: prohibited until separately authorized.
Progress and measured acceptance are recorded separately from this plan.

## Current boundary
Stages 1–4.5 remain preserved. Inference/evidence/learning/tool foundations were
checkpointed at 5079048 (81 passing actual-host tests). The desktop integration adds
actual protected workflows, managed-model materialization and indexed history.
Framework and OS-profile acceptance is separate from actual model accuracy; no
simulated test establishes model reasoning. See INTELLIGENCE_SPEC.md,
DESKTOP_SPEC.md and PROGRESS.md for final test/model results. Stage 6 currently
covers a bounded deterministic subset; general scientific reasoning remains open.
Stage 7 has a working local X11 interface, with representative usability/security
qualification still required. Stage 8 remains a release gate. Stage 9 remains
unauthorized. No host-wide security relaxation or shared-service reuse is permitted.


## Next engineering batches after dae4abf
1. Add representative independently graded evidence tasks (missing/conflicting
   evidence, cross-document synthesis, exact instruction following), then qualify
   a locally available capable model. Current Qwen0.5B scored 0/3 on the narrow
   two-source task; no model is certified for ordinary scientific reasoning.
2. Complete project-to-source associations and browsing/pagination, richer
   assessment/override review, and representative human usability acceptance.
   Project/conversation persistence works; full research-project organization is
   unfinished. Local X11/XWayland is the only qualified display transport.
3. Expand deterministic engineering tools with explicit assumptions, error
   propagation and independently established domain cases; general algebra and
   engineering simulation remain outside the current bounded subset.
4. Qualify installed optional encryption when the dependency is provided locally;
   perform longer-duration, hostile-host and physical-power-loss acceptance.
   Current crash tests are process interruption tests, not physical power loss.
5. Release only after these gates and representative memory/performance/recovery
   workloads pass. Keep inference optional and evidence-only workflows available.

## Memory/project organization milestone after d06f7d5
Implemented durable source associations, versioned research items, project archival/
reactivation/history, memory-category/source/time recall, exact-entity/evidence
expansion, scoped reconciliation, deferred learning, old-session resumption and
byte-bounded history. Original evidence has priority over optional project notes.
A measured one-commit-per-source bulk bottleneck is addressed with approved atomic
batches, preserving synchronous FULL and crash rollback. See the new memory spec.

Next milestone: independently qualify mixed-domain and temporal reasoning over a
representative adversarial evidence corpus, add reviewed entity-alias proposals
only with measured retrieval benefit, and conduct user usability/recovery sessions.
A capable actual local model remains a separate qualification gate; literal memory
views and explicit user links do not establish semantic understanding. Optional
installed encryption and physical-power-loss/hostile-host acceptance remain open.


Immediate next milestone after memory/project acceptance: build a derived, rebuildable
full-history FTS index for versioned project notes/tasks/goals, validate latest-version
retrieval against independently chosen notes older than the recent-20 context window,
and expose those results through existing forms/context without promoting user notes
to verified evidence. Preserve registered portability and original source attribution.
Then qualify reviewed entity-alias proposals and representative mixed-domain/temporal
reasoning; actual model capability remains independently gated.
