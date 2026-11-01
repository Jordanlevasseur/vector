# Stage 6B source audit at 4053ec7

Main repository was clean at 4053ec7b261fe96a6f340be6e6208db0a4d37dbf; source and installed package will be checked separately. Work occurs in work/vector-stage6b, branch stage6b. No downloads, new models, training, law/default changes or HELIX edits.

| Capability | Classification and evidence | Actual gap |
|---|---|---|
| Original preservation / provenance | Implemented and previously host-verified: memory.py, storage.py, science.py; immutable events, SHA/source spans, full PDFs/archives, scientific manifest links. Baseline source suite158/158 passed. | Not semantic understanding or mathematical/figure extraction. |
| Claims / entities / relationships | Implemented, working narrow mechanisms: knowledge.py ClaimDraft and Knowledge; source-span checks, kinds, subject/object entities; learning.py proposal/atomic explicit approval. | Only automatic pipe-v1 extraction; no qualified concepts/explicit aliases, negation, applicability intervals or typed condition metadata. Source occurrence does not establish predicate entailment. |
| Contradictions / beliefs | Implemented scoped exclusive-value disagreements; versioned assessments and user assumptions retain evidence. | Literal comparison misses compatible unit conversions and richer qualifications; an override remains an assumption. |
| Retrieval / context | Implemented FTS5 and literary passages; context.py already expands exact entities one/two edges and related originals, with provenance and budget checks. | Not missing all graph traversal. Existing expansion mixes literal names and has no separate qualified sense/condition/polarity interpretation. It assembles passages without a reusable qualified query/result package. |
| Scientific corpus | Implemented 22 originals, 21 searchable publications/2631 segments; one atmospheric extraction deferred. | Curated claims/relations are not extracted automatically. Natural-medicine coverage is not demonstrated; negative controls must not invent it. Medical sources remain dated historical references. |
| Investigation controller | Implemented Stage 6A Investigations: checkpoint-before-step, atomic results, renewable budgets, DAG/dependencies, pause/resume/stale discard; service and CLI expose it. | Source retrieval, claim interpretation and quantitative binding are disconnected. No semantic retrieval flag or grounded quantity bindings. |
| Verified tools | Implemented Decimal/SI arithmetic, conversions, statistics, linear solving, finite constraints, independent numeric checks. | Calculate binds trusted explicit inputs/previous numeric results, not qualified source properties. This is a higher-value missing bridge than adding another graph/controller. |
| Model adapters | Implemented isolated replaceable adapter, strict JSON/citation/prompt/completion checks, private namespaces/cgroup resources. Actual0.5/2B tests establish weak-model limits separately. | Models can produce complete wrong arithmetic and invalid citations/JSON; source correctness cannot depend on their confidence. No new models or guard relaxation warranted. |
| User-visible flow | Implemented desktop/service ask, proposals, source links, project memory and tools. | Stage6A investigation has no desktop panel. New connected retrieval must enter ordinary Ask via an opt-in control and also existing investigation/service/CLI paths. |
| Persistence / recovery | Implemented append-only registered records, immutable originals, portable validation/restore. | New qualification and result references must participate in existing validation, not become an unregistered side database or self-certified calculation. |

Chosen integration: versioned semantic qualifications reference existing claim IDs; reuse existing entity IDs with explicit sense namespaces and aliases. Reviewed means reviewed interpretation, not fact. Qualified lookup and bounded joins preserve scope, conditions, dates, polarity, source IDs and contradictions. New source quantity bindings feed existing Decimal/SI tools. Existing context/Ask, investigations, service, CLI and a desktop opt-in use the capability. Default semantic runtime remains off during qualification. No replacement graph DB, memory engine, controller or embeddings.

Deterministic and actual-model comparative measurements must distinguish tool-assisted system performance, retrieval coverage, valid provenance and unaided model quality. A/B/C get common task specifications/budgets; gold expected answers are external to inference. Manually curated semantic knowledge and its effort are declared, not attributed to the model. No corpus-wide claim extraction or literary reprocessing is planned.

## First implementation checks

- Existing main source baseline:158/158 passed,333.183s,baseline-suite.log.
- Ordinary Codex sandbox smoke could not create VECTOR data because ancestor ownership is remapped; environment limitation. Native smoke retained ownership checks and passed source-to-tool285J, existing service/investigation completion and semantic context inclusion.
- First14 new tests:12passed,1error,1failure. Actual defect: frozen portable-export SQLite connections return tuples, while new semantic validation assumed named rows. Fixed tuple-safe metadata validation and narrowly scoped Row factories restored in finally around original/result validation. No portable checks bypassed.
- New test defect: expected numeric100 was compared with string'100', but the existing Decimal-based tool representation returned equivalent'1E+2'. Corrected the test to compare Decimal numeric equality; numeric/unit/independent recomputation requirements are unchanged. No pre-existing test was edited.

## Subsequent integration findings

- 40/40 external gold cases passed first execution, 7.99s controller time,
  with no model calls. Existing direct retrieval found all required sources for
  30/32 sourced cases and full gold excerpts for27/32; new source-linked results
  retained all required citations for32/32. Eight cases require withholding or
  epistemic distinctions; these are not invented subject coverage.
- Code review found two additional new-path defects before release: a disputed
  relationship could be traversed as if it were undisputed, and exclusive values
  from distinct terminal entities could be mislabeled as a conflict. Added bounded
  edge-dispute detection and per-entity terminal comparison, with dedicated tests.
- Restore/reuse validation now rejects forged lookup status/answer, missing source
  attributions, missing source premises and false calculation-tool labels.
- Expanded semantic tests first ran22/23 passing. The actual GUI failed because
  evidence-only Ask inherited the tiny default neural window and omitted the
  entire qualified bundle. Kept the test requirement. Evidence-only display now
  uses an independent8192-byte evidence budget when the adapter is unavailable;
  inference-enabled prompt guards and model defaults remain unchanged.
- Prototype live comparison:5 attempted cells across2 questions, strict model
  scores0/5; both available C source results correct. One C generation timed out
  at180s; worker closed, no OOM/swap-pressure guard stop. The early prompts repeated
  complete source-result trees. Compact checked model observations now retain all
  epistemic/applicability qualifications and span references without duplicate
  quotes; durable full records remain intact. All36 planned final prompt sizes
  fit the unchanged adapter guard (max6890 of7424bytes). Final comparative protocol
  uses a consistent300-second bound and distinct new cells after timeout closure;
  no failed cell is retried as progress. Prototype evidence remains separate.


## Measured completion and remaining priorities

Source implementation checkpoints: b3a2193 initial integration, e7c11ef qualified
source fast path/full provenance, b74d742 evaluation-only case-filter correction,
92701d5 precision hardening. Final source187/187 passed; installed186 passed and
one optional cryptography roundtrip skipped. The source-host encryption check
passed; no missing dependency was downloaded.

The independent40-case corpus passed before and after final hardening. The actual
installed0.5B paired trial ran36requests over12questions: A1/12, B1/12, C0/12
accepted neural proposals; C's separately checked source/tool results12/12.
A/B passed the insufficient-evidence control. C's failed narration followed an
irrelevant electrical-current passage in a medical-current question: qualified
lookup withheld correctly, but literal fallback and neural composition remain
important limitations. Raw responses also copy input keys into the output shape.
A richer evidence package alone does not establish a neural improvement.

A further confirmed source-comparison defect collapsed values differing in the 30th decimal place
under ambientDecimal28, unlike existing40-digit tools. Fixed with independent
exact-compatibility precision, literal unit retention when equivalence is unproved,
and40-digit target-unit conversion/replay. Added three independent regressions;
no calculation precision/acceptance requirement was reduced. Paired inputs are
unaffected; the same40goldcases passed again. See STAGE6B_REPORT.md for the final
preservation outcome and actual measured resources, and SEMANTIC_SPEC.md for scope.

Priority next work is a small typed proposal/source-handle protocol and a
reviewable question-to-query interface, with relevance checks for keyword fallback.
Then index qualified lookups beyond the bounded catalog slice and expose checked
results/explicit continuation clearly in the desktop. Manual review/typed requests,
not autonomous scientific interpretation, underpin the current source results.
The pathway remains experimental and disabled by default. No next stage started.
