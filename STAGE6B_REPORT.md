# Stage 6B measured completion record

Implementation and functional integration are verified. Final runtime checkpoint 92701d51f3ae633353facb009c7d01387de8cc1c; primary model comparison used stable runtime e7c11ef9359fa75a2fb0d800c9561ee8fc398512 with evaluation-tool checkpoint b74d7426bbd0cfa1960f91d757c4dc40282f102a. Subsequent precision hardening was checked with full source/installed suites, the same 40 gold cases and the additional actual production-model workflow. The subsequent report checkpoint changes documentation only. The experimental path remains disabled by default. Neural-model accuracy and verified source/tool results are reported separately.

The existing claims/entities, immutable originals, persistence registry, FTS/passage search, Decimal/SI tools, Stage 6A investigation controller, model adapter, approval boundary and protected desktop were reused. There is no replacement graph database, memory engine, agent framework, embedding model, model training or external service.

`semantic.py` adds reviewed, versioned source interpretations with explicit senses/aliases, scope, conditions, validity dates, polarity and epistemic status; bounded source joins; unit-aware disagreements; source quantity bindings; replayable source/tool results; and organized evidence plus investigation observations. Context/Ask, existing investigations, service, CLI and a default-false desktop checkbox consume it. Full provenance, qualifiers and rights notices remain attached; a model window cannot keep only one side of a known disagreement. Model text is never dispatched as an operation.

Changed runtime components: semantic.py (new), context.py, assistant.py, investigation.py, service.py, cli.py, desktop.py, projects.py and portable.py. Added semantic/corpus/desktop regression tests, the external 40-case fixture and deterministic/live evaluation tools. ARCHITECTURE.md, README.md and SEMANTIC_SPEC.md document the integration. Existing security, authority, inference, launcher, model and storage controls were not relaxed.

No SQL migration: user_version remains 8. `semantic_claims` is a registered version 1 append-only contract keyed by existing claim IDs. Reviewed means reviewed interpretation, not established truth. Old versions/withdrawals survive; duplicate identical reviews are idempotent. Calculations pin source-annotation revisions and are independently reproduced on use/restore. Missing/disputed/hypothetical/owner-asserted quantities do not become definite tool inputs.

**Software and external evaluation.** Final source suite: 187/187 passed in 357.203 s. Independent installed suite: 186 passed, one optional cryptography roundtrip skipped, in 390.129 s. The unchanged baseline source suite passed 158/158; earlier full integration batches and their failures remain in the evidence logs. The installed environment lacks optional cryptography; its positive encryption roundtrip is unverified there, while the source-host positive test passed. No dependency was downloaded and no skip is a pass. All 45 installed runtime modules match the reviewed local wheel and source bytes; wheel SHA-256: `97abb6393a98d4e2657c0e2c0966d758c4fe90ee8bd401e3ced833b12c4a44d6`. The evaluation-only per-case launcher typo was corrected separately and exercised by the actual model runs.

Final external deterministic corpus: 40/40 objective cases passed, zero model calls. Cases include direct facts, dimensional quantities, multi-source joins, counterevidence, conditions, temporal scope, missing evidence, namespace separation, pending/hypothetical status and restart continuation. Before the final model run, supporting-clause attribution rules were frozen at SHA-256 `1fe9b60ac0e0ff3e49b43f3f446431f6862703fa11cac10883e0e9ee1717346d`. Gold answers never enter model prompts or the cognitive implementation.

The corpus has 32 source premises and 37 claims: nine verified excerpts from six existing publications, plus explicitly fictional equipment premises. Fourteen real-source interpretations were added to existing production scientific events; fictional premises were not added to production. Complete original checksums and exact excerpt spans were rechecked against the existing local science package. U.S.-only rights remain recorded. Historical 2004/2005 medical material is not current guidance; natural-medicine coverage is not invented. The selected mathematics publication actually contains basic calculus material, a coverage correction established by source inspection without acquisition.

Existing direct retrieval found all required source identities for 30/32 sourced deterministic cases and complete gold excerpts for 27/32; missing-source cases were J1, J4. The new structured source results retained every required citation for 32/32. These are manually qualified source-selection results, not neural semantic-entailment or corpus-wide accuracy measurements. The remaining cases check missing information or epistemic distinctions.

**Actual installed 0.5B comparison.** A: the model receives the independently retrieved plain passage context, without derived claims/controller/tool results. B: existing investigation retrieve/generate, semantic mode off. C: qualified evidence plus checked source/tool observations, then the same model proposal protocol. All modes receive the same question and explicit selector/formula specification, never the gold answer. Context 8192, output 512, temperature 0, seed 0, timeout 300 s; 3500-byte evidence budget, one workload/request at a time, existing 768 MiB memory/64-task/one-CPU isolation and zero worker swap. Order rotates, and each request unloads. A is a supplied-evidence neural baseline, not a closed-book test. C has extra reviewed structure and tools; this is not a pure architecture ablation. All 12 C responses completed but failed the fixed proposal envelope: examples copy source_query/status keys (D1) or place source_id/quote outside the citations list (D7). This is observed schema/instruction failure, not proof of an intrinsic inability to reason.

| Mode | Actual model requests / planned 12 | Accepted objective model answers with supporting clauses | Valid proposal envelopes | C verified source/tool results |
|---|---:|---:|---:|---:|
| A | 12/12 | 1/12 | 2/12 | not applicable |
| B | 12/12 | 1/12 | 9/12 | not applicable |
| C | 12/12 | 0/12 | 0/12 | 12/12 |

Actual requests covered 12 distinct questions. All 36 planned cells completed, with no orchestration error. Unrun cells are never passes. Automatic protocol/value/source-ID scores before supporting-clause checks were A 1, B 1, C 0; final accepted-answer counts above also require relevant support phrases in checked citation quotes. Citation identity/hash/span validity alone is not semantic entailment.

| Case | A accepted | B accepted | C accepted model | C checked source/tool |
|---|---:|---:|---:|---:|
| D1 | fail | fail | fail | pass |
| D7 | fail | fail | fail | pass |
| D8 | fail | fail | fail | pass |
| Q1 | fail | fail | fail | pass |
| Q2 | fail | fail | fail | pass |
| J1 | fail | fail | fail | pass |
| J2 | fail | fail | fail | pass |
| X1 | fail | fail | fail | pass |
| C1 | fail | fail | fail | pass |
| T1 | fail | fail | fail | pass |
| N1 | pass | pass | fail | pass |
| M1 | fail | fail | fail | pass |

A correct fact in fluent prose still fails if it violates the requested contract or lacks supporting citations. Conversely, C's verified source/tool answer is never counted as a successful neural response. Negative-control unsupported-answer counts inspect definite nonempty short answers only, not the absence of an answer. This small corpus cannot establish a general unsupported-claim rate, scientific originality, empirical truth, autonomous planning or broad intelligence.

For the two negative controls, definite short-answer violations among protocol-valid proposals were A: 0/1 assessable proposal(s), 1 unassessable; B: 1/2 assessable proposal(s), 0 unassessable; C: 0/0 assessable proposal(s), 2 unassessable. Zero assessable C proposals gives no safety or hallucination-rate estimate. Invalid/timed-out output is a failure, and this metric does not grade every free-text assertion.

**Runtime and recovery.** Generation metrics are actual returned Ollama measurements; timeout cells without metrics are excluded from speed/load aggregates, not scored as successes.

| Mode | Median generated tokens/s | Returned speed measurements | Median load seconds | Mean complete cell seconds | Timeouts |
|---|---:|---:|---:|---:|---:|
| A | 3.48 | 10 | 4.72 | 166.66 | 2 |
| B | 2.66 | 12 | 4.75 | 101.14 | 0 |
| C | 2.44 | 12 | 4.82 | 146.96 | 0 |

Comparison elapsed 5505.26 s. Exact cgroup RAM peak 768.0 MiB (includes file cache); runner peak RSS 638.8 MiB; worker swap peak 0.0 MiB. Host swap already in use peaked at 1416.8 MiB; this is not model-owned swap. Minimum host available RAM 1252.9 MiB. New OOM kills 0; guard stops: none. Host full-memory PSI avg10 briefly reached 30.32 percent; longest sampled interval above 30 percent was 1.52 s, below the 15 s stop criterion. Total observed host swap-out across the primary comparison was 83.5 MiB. Mean baseline CPU utilization was 9.81 percent. Per-run baseline CPU counters and post-unload memory samples remain in raw reports; cgroup closure/removal and per-request runner unload are recorded. Resource aggregates cover 10882 samples. No memory limit, network boundary or prompt/completion guard was bypassed.

The production query first spent 70.45 s in legacy passage retrieval, exceeded a 60 s slice and paused before its grounded step. Explicit resumption reused that durable evidence and completed in 0.506 s. The optimized fully specified query completed in 0.780 s, with full scientific provenance and an explicit notice that unannotated full text was not searched. This is a single workflow observation across code/cache conditions, not a general latency benchmark. General/unknown queries retain independent passage fallback and its existing corpus-scale latency. See [production-integration.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/production-integration.json) and [production-resumed.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/production-resumed.json).

**Failures retained and diagnosed.** Initial new tests exposed a real frozen-SQLite row-factory assumption in portable validation; fixed without bypassing original checks. A new numeric-string test expected 100 rather than equivalent 1E+2; corrected to independent Decimal equality. A real desktop evidence-only bug hid qualified bundles inside a tiny neural window; evidence-only display now has a separate budget, while actual inference guards/defaults remain unchanged. Review found disputed relationships being traversed and distinct terminal entities being falsely treated as conflicts; both received behavioral tests and fixes. Scientific attribution/provenance is retained complete.

The early real-model pilot attempted five cells over two questions, with 0/5 accepted neural answers and 2/2 available C source results. One 180 s timeout correctly closed the worker; there were no resource guard incidents. Checked model observations now avoid duplicate quotes/lookup trees while preserving applicability and epistemic qualifications. The final common 300 s protocol is separate from that pilot. A later per-case evaluation-tool NameError occurred before model generation; empty runs are preserved, not counted as model tests. The one-line variable fix changed no runtime module. No failed answer was retried as progress; a fresh worker after timeout evaluated only previously unattempted cells.

The complete production two-hop J2 model prompt required 7761 bytes, exceeding the unchanged 7424-byte guard at 8192 context/512 output. No model call was made for that oversized prompt, and no provenance/conditions were removed. The extra production model check uses the complete D7 source question (6125 bytes) under the same model settings. The verified production two-hop source query itself completed; model narration of that full-provenance two-hop package remains blocked under this configuration. Raw sizing: [production-prompt-sizes.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/production-prompt-sizes.json).

A further numeric audit found two source values differing in the 30th decimal place collapsing under the ambient 28-digit Decimal context, although the existing 40-digit tool distinguishes them. Unsupported unit labels also disappeared from the fallback key. Final hardening uses an independent 256-digit exact-compatibility context with conservative literal-unit fallback, and parses output-unit conversion/replay inside the existing 40-digit tool context. Three new regressions cover high-precision disagreement, unknown units and reciprocal-unit conversion under ambient 12-digit precision. No calculation precision or acceptance criterion was lowered. The primary paired inputs use short quantities and are unaffected; all 40 gold cases passed again after this fix. Raw reproduction: [precision-boundary-before.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/precision-boundary-before.json).

Historical Stage 6A reported baseline 0/4 and adaptive 0/4 objective real-model tasks, and preserved a 385 answer to 15×19 despite correct 285 feedback. Those different tasks are historical context, not numerically pooled with this paired Stage 6B corpus. Complete response bodies, prompt/configuration data, failure feedback, hashes, timings and external grades remain in the local evidence directory.

**Preservation and recovery.** A consistent pre-stage 1,347,997,696-byte SQLite snapshot plus independently byte-verified copies of all 4587 registered managed objects was preserved (1,599,438,405 bytes total). Existing whole-system backups and both model installations remain untouched. This scoped checkpoint is not a fresh whole-system restore qualification. Small semantic fixture export/restore, actual subprocess interruption before metadata commit, in-flight grounded-step crashes, explicit resume and pinned-result forgery checks passed.

Post-stage full read-only portable/database validation passed, including SQLite integrity, foreign keys, original-object reconstruction/hashes, schema, registered records and new pinned observations. Runtime schema version 8; old managed objects unchanged 4587/4587. The exact old literary edition and passage fingerprints remain 1000 and 1,288,804; scientific edition and extracted-text fingerprints remain 22 and 2631. Preferences/default records are byte-identical, both model-store inventories unchanged, foundational laws unchanged and existing safety-backup inventories unchanged. Raw counts/checksums and duration are in [preservation-after.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/preservation-after.json) (full scan 456.813 s, including 320.483 s integrity/record validation). Production originals were not rewritten, re-ingested or regenerated. This work initiated no external-network operations, downloads, training, owner override or HELIX changes. VECTOR runtime network denial remains enforced.

The insufficient-evidence control was accepted in A and B but rejected in C. C's raw narration followed an unrelated electrical-current passage in a medical-current question and omitted required fields, although the typed core correctly returned insufficient. This exposes both the existing lexical fallback's relevance limitation and weak-model response handling; a richer evidence package does not itself improve the model.

**Limits and next development decision.** This is a reviewed-annotation and explicit-query bridge. It does not automatically derive trustworthy predicates, conditions, formulas or plans from arbitrary natural language. Aliases are explicit and case-preserving. One current interpretation exists per base claim; alternative interpretations need distinct scoped claims or historical versions. Catalog default 256 and finite traversal budgets bound an operation, mark incomplete results and fail closed; larger-scale indexed sense/relation lookup remains needed. Existing full-text/history scalability and general desktop investigation-control gaps remain. Learned neural quality, source truth, causal discovery and general scientific reasoning are unverified.

No improvement in accepted neural answers over B is established by this trial. The source/tool bridge is useful functional groundwork, but the runtime pathway remains disabled by default rather than being presented as an intelligence milestone.

The next highest-leverage batch is a bounded, auditable question-to-query interface plus server-owned typed proposals and short source handles, retaining independent source-span expansion/checks and tool verification. That addresses manual selector burden and weak-model JSON/citation copying without granting model authority. Add indexed qualified lookup before broad corpus deployment, then rerun held-out natural questions against unchanged objective criteria. No next stage or default-model change was implemented.

Local evidence: outputs/vector-stage6b under the Codex workspace. Key artifacts: AUDIT.md, before-stage6b.json, source-batch3-final-suite.log, installed-batch3-suite.log, deterministic-final/results.json, attribution-rubric.json, live-final-v2/comparison.json, [comparison-summary.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/comparison-summary.json), production-live-d7/result.json and [preservation-after.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/preservation-after.json).



Additional actual production 0.5B direct-source workflow (D7; outside the paired corpus): 1 model request(s), source/tool results 1/1, automatic neural contract/value/source-ID pass 0/1. It uses the real registered historical RBC page and all original provenance, a 5000-byte evidence budget, the same 8192/512/300 configuration, and no default-model change. Raw result/citations/failures are preserved; this extra workflow is not pooled into primary A/B/C scores. No runtime error or resource guard stop occurred.

Failed neural cells (the authoritative raw evidence remains in the comparison JSON):

| Case / mode | Failure recorded |
|---|---|
| D1 / A | InferenceError('Invalid candidate structure.') |
| D1 / B | short answer differs from the requested bare gold value or format |
| D1 / C | Invalid candidate structure. |
| D7 / B | short answer differs from the requested bare gold value or format |
| D7 / C | Invalid candidate structure. |
| D7 / A | InferenceError('Malformed candidate JSON: Duplicate manifest key.') |
| D8 / C | Invalid candidate structure. |
| D8 / A | InferenceError('Invalid candidate structure.') |
| D8 / B | required supporting source citation missing |
| Q1 / A | InferenceError('Invalid candidate structure.') |
| Q1 / B | Invalid candidate structure. |
| Q1 / C | Invalid candidate structure. |
| Q2 / B | short answer differs from the requested bare gold value or format |
| Q2 / C | Invalid candidate structure. |
| Q2 / A | short answer differs from the requested bare gold value or format |
| J1 / C | Invalid candidate structure. |
| J1 / A | exceeded 300 s; private worker closed |
| J1 / B | short answer differs from the requested bare gold value or format |
| J2 / A | InferenceError('Incomplete/truncated model generation.') |
| J2 / B | Invalid candidate structure. |
| J2 / C | Invalid candidate structure. |
| X1 / B | short answer differs from the requested bare gold value or format |
| X1 / C | Invalid candidate structure. |
| X1 / A | exceeded 300 s; private worker closed |
| C1 / C | Invalid candidate structure. |
| C1 / A | InferenceError('Invalid candidate structure.') |
| C1 / B | short answer differs from the requested bare gold value or format |
| T1 / A | InferenceError('Incomplete/truncated model generation.') |
| T1 / B | Invalid candidate structure. |
| T1 / C | Invalid candidate structure. |
| N1 / C | Invalid candidate structure. |
| M1 / C | Invalid candidate structure. |
| M1 / A | InferenceError('Invalid candidate structure.') |
| M1 / B | short answer differs from the requested bare gold value or format |

Verified artifacts: [source regression log](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/source-batch3-final-suite.log), [installed regression log](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/installed-batch3-suite.log), [raw paired model requests and responses](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/live-final-v2/comparison.json), [independent gold corpus](/home/mint/VECTOR/vector/tests/fixtures/stage6b-corpus.json), [additional production-model response](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6b/production-live-d7/result.json).
