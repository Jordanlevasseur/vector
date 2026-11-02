# VECTOR ordinary-conversation routing — measured repair report

Implementation checkpoint: `49cf0ada45ac55f9ef499fdce6a1e2011f73ac46`. Baseline: `f880e871eb1066a96f285d3ea7b707d559e1c6b8`.
The final report-only HEAD, clean repositories and installed byte checks are recorded in
[FINAL.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/FINAL.json). This is scoped routing/desktop acceptance, not general
reasoning, neural-model qualification or release readiness.

## Verified causes and repair

The actual saved arithmetic failure retrieved a telephone/address passage from
*Workshop on Electronic Texts*. Ordinary Desktop Send selected neither the calculator
nor checked composition: every default reasoning task was retrieve-evidence-only,
followed by model generation. Literal fallback searches treated numbers and operation
words as evidence queries. The unavailable isolated model worker compounded this
routing failure; no neural model was needed for arithmetic.

Summarization used the same retrieval path, which found a title. The desktop placed
provider licensing notices before raw quotes and did not clearly distinguish finding
text from fulfilling the requested operation. The existing planner/tools/findings were
separate, opt-in paths. Exact saved revision IDs, hashes, spans and the original data
flow are in ROUTING_REPAIR_AUDIT.md, written before source modification.

The existing reasoning frontend now fully parses bounded numeric requests before
retrieval/model preparation. Existing Decimal/SI tools, calculate/dependency strategies,
durable Investigations and independent findings.compose/validate_document are reused.
A single operation uses one calculation plus checked composition, without exploratory
planning or model loading. Ambiguous, incomplete, mixed and unsupported objectives
fail with clarification; no partial task is accepted. Units and numeric limits remain
authoritative. No eval, model-issued command or duplicate reasoning engine is added.

Conversation records pin immutable answer events. History/restart/portable restoration
recompile the original request and independently replay its calculation. Request IDs
are idempotent; prior numeric premises must be the immediately preceding checked result
in the same conversation/project. Owner pause/cancel is respected. Source/model prose
cannot become a numeric premise. Rejected JSON, repeated invalid output, altered
proofs and stale title indexes fail closed.

Explicit searches use their subject and a bounded all-term window, with source-title
preference. Bare-topic/validated source follow-ups retain their original conservative
context budgets and continuity behavior. Retrieved text remains source material, not
a certified explanation. Contradictions and scoped assumptions stay visible.

Document excerpts use a bounded exact normalized short title-heading anchor among
the first 128 existing units, including repeated-title/preface cases. Original bytes,
unit digests, hashes and spans are checked; no corpus/index is rewritten. Absence of
a credible heading is labeled as unverified opening excerpts. Full summary input
retains the complete canonical original body and independently recomputed bounds;
essential text is never silently clipped. A quotation alone is rejected as a summary,
including recovery after a crash between generic persistence and task finalization.
Model synthesis, when eligible, remains unverified. Experimental planning/connected
evidence remain opt-in. Unavailable interpretation is a truthful limitation with
access to the existing investigation control, not a fabricated fan diagnosis.

## Actual desktop and independent evaluations

The same seven questions were sent through the real protected installed native
application with advanced flags off and an unavailable neural worker. Four arithmetic
requests were wrong/unfulfilled before and four are now independently checked and
correct. The other accepted branches comprise one relevant retrieval and two explicit
capability limitations. They are not seven completed reasoning answers.

| Request | Before | Final installed | Recorded result |
|---|---:|---:|---|
| 568 times 564 | 60.057s | 3.045s | 320,352 |
| 568 multiplied by 564 | 41.795s | 1.708s | 320,352 |
| (13+7)*2, then /8 | 32.231s | 1.545s | 5 |
| 25% of 200 | 21.196s | 0.812s | 50 |
| Electrical resistance | 23.581s | 7.428s | Primary electrical source / Ohm’s law |
| Intermittent fan vibration | 31.874s | 0.356s | Explicit unresolved limitation; planner offered |
| Declaration summary | 8.745s | 1.089s | Explicit limitation; actual declaration excerpts offered |

Arithmetic mean wall time changed from **38.820s** to
**1.777s**. These are measured end-to-end observations;
cache state and background I/O differ, so this is not a controlled CPU benchmark.
Frontend peak RSS: 29.71 MiB before,
30.96 MiB after. Final backend peak sampled RSS/HWM:
32.93 MiB, sampled backend swap:
0KiB. Backend CPU across the sample interval:
0.740s; frontend CPU: 2.080s.
These are process measurements, not whole-host peaks. Accepted production generation
records: **0**. No real Qwen reasoning or summary-quality gain is claimed.

The first installed replay still offered publishing-history front matter and ranked
a thermal analogy first. That result was retained and prompted the final selection
batch. Its initial external scorer also incorrectly demanded adjacent words
“electrical resistance.” The final frozen external source expectations require the
primary electrical-science passage to contain the actual voltage/current/resistance
relation, and declaration excerpts to contain the original opening. Runtime code
never receives those gold expectations. No existing security test or acceptance
requirement was relaxed. Exact records: [comparison.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/comparison.json),
[final desktop replay](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/desktop-selection-final.json),
[external source gold](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/acceptance-source-gold.json).

The approved native theme/core, hamburger, three primary workspaces, bubble-free
stream, fixed multiline composer and secondary controls remain. Actual GUI tests
verify Send, checked display, continuation and saved history/restart. Full rights
notices remain inspectable through response/evidence and original-source controls.
Old saved payloads and failed historical turns are retained rather than rewritten.

## Tests and preservation

- Final source: **257/257 passed**, no skips, 747.264s.
- Final installed: **256 passed /257 executed**, one explicit skip,
  767.244s. Optional cryptography is absent in the isolated venv;
  positive authenticated-encryption tests passed in the host source suite. This
  skip is not counted as a pass. Missing-crypto fail-closed coverage passed.
- Existing 52 independent checked-answer cases, separate 40 semantic cases and
  planner 28+8 cases remain unchanged and pass. Twenty-six routing test methods,
  independent 17-case arithmetic gold and a default-chat GUI regression cover
  malformed/mixed inputs, comments/trailing clauses, precision, units, relevance,
  contradictions, unavailable models, retries, interruptions, owner controls,
  tampering, source budgets and title/preface selection.
- Initial transitional full run: 250 executed, 246 passed, 3 failures and 1 error.
  Three real compatibility regressions were repaired without changing their tests;
  a new GUI assertion was corrected for Decimal representation 50.00 versus 50.
  Interrupted provisional qualification attempts remain nonpassing evidence.
  Earlier scoped batch 255/255 source and 254+1 skip installed results are retained.
- Complete pre-change corpus/preferences fingerprints and 18 existing history/table
  prefixes matched. All **1,000 literary editions, 1,288,804 passages, 22 scientific
  editions and 2,631 scientific text events** are preserved. All 4,587 live object
  hashes and independent safety-copy hashes matched, as did the fresh pre-routing
  database backup. Evaluation conversation/proof revisions are intentionally appended.
- Full database/schema/foreign-key/original/registered-record validation passed.
  The 64 MiB QA profile timed out at 1800s and is retained as a failure. The same full
  validation passed with a temporary 512 MiB read-only cache in
  1449.852s; QA peak RSS was
  579.50 MiB. Runtime database limits were not changed. The larger QA pass does not establish
  that normal lower-memory verification can finish within its original deadline;
  full-corpus verification remains slow on this hardware.
- Model/candidate and old-backup trees have unchanged metadata inventories; those
  comparisons are not fresh full-file model/backup hashes. Controlled restoration
  tests pass; the production database was not restored. Foundational Laws match
  baseline byte-for-byte, SHA256
  `059fd4e4193c92dbb6860d48a3050bdb66b8b3abaaa6fb4a37854950d808748d`.
- Mandatory offline seccomp, inference qualification, authority, configuration and
  model defaults are unchanged. No downloads, external access, owner override,
  training, new law, dependency or HELIX modification occurred. All 49 installed
  core modules are checked against the qualified source; no core module was added.

Evidence: [source suite](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/source-suite-selection-qualified.log),
[installed suite](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/installed-suite.log),
[preservation](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/preservation-after.json),
[retained timeout](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/preservation-after.log), and [final gate](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-routing-repair/FINAL.json).

## Scope, changed files and next step

Changed existing modules: reasoning.py, assistant.py, service.py, context.py,
literature.py, projects.py, portable.py, desktop.py and desktop_shell.py. Added
routing specifications/audit, tests/test_routing.py, tests/test_routing_desktop.py and
independent routing_cases.json; updated ARCHITECTURE.md and this measured report.
Tools, investigations, typed findings, knowledge, planner, memory and security
capabilities are reused. No independent cognitive engine or new persistence schema.

Arithmetic supports the established explicit grammar/tool bounds, not arbitrary
English or mathematics. Mixed calculation/source goals, unit-bearing continuation
without an explicit quantity method, unsupported functions, general diagnosis,
creative/neural reasoning and reliable document summaries are not newly qualified.
Lexical title/window/heading heuristics do not establish general semantic relevance.
Qualified summaries still need an unambiguous complete source package and sufficient
existing model context. Unsupported tasks remain visible rather than manufactured.

Next highest-leverage work: qualify a model-assisted interpretation/evidence-sufficiency
handoff to the existing planner and tools with independently controlled task tests,
while preserving checked outputs, uncertainty and explicit advanced authorization.
Do not change the default model as part of this repair. VECTOR is **not declared
release-ready**.
