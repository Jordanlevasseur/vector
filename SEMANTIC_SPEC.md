# Stage 6B: qualified evidence and source-bound reasoning

Experimental, opt-in; ordinary Ask and model defaults are unchanged. This extends
Knowledge, Memory, context and Investigations rather than adding a graph database
or another controller. It requires no embeddings, model downloads or networking.

## Representation and authority

`semantic.py` stores versioned `semantic_claims` records through the existing
persistence registry. The key is an existing source-linked claim ID. There is no
SQL migration: database user_version remains 8. Claims, entities and source bytes
retain their existing identities. Qualification versions survive portable export,
restore, withdrawal and changed interpretations; duplicate identical reviews are
idempotent and stale revisions fail.

An explicit trusted-user review supplies sense namespaces, finite aliases,
predicate aliases, polarity, scope/conditions, date intervals and epistemic status.
Namespaces and aliases are case-preserving: a similar name does not establish
identity. Relationships refer to existing object entities with an explicit object
sense. Review certifies an interpretation was reviewed, not that its claim is true.
Model proposals remain candidate/unverified until explicit review. An owner
assertion, observation report, hypothesis, source assertion, inferred join and
verified computation remain distinct. Owner assumptions never overwrite sources.

No source text, model output or recognizable owner phrase is dispatched as an
operation. Existing authorization, original SHA/span checks, fail-closed network
policy, model isolation and approval semantics remain in force.

## Retrieval and reasoning

`context.build_context(..., semantic=True)` adds qualified source bundles and
bounded concept connections; ordinary passage retrieval remains independent and
available as fallback. `semantic.evidence` returns assertions, sources,
connections, disagreements, ambiguity, qualifications and explicitly requested
investigation observations. It reproduces historical calculations and marks
changed annotations; old observations do not silently become current conclusions.

Whole qualified sources precede keyword distractors. A known comparable conflict
is one atomic context bundle: a small window cannot retain only its convenient
side. Conditions, dates, negation, senses and scientific provenance notices are
not clipped to fit. Omitted bundles and incomplete catalog slices are explicit.
Pure source reasoning has its own evidence budget, independent of neural context;
model prompt and completion guards remain enforced.

`Semantics.lookup` takes an explicit subject, sense, predicate, scope, optional
conditions/date and relationship path. Positive joins have finite hop/node bounds;
negative or uncertain edges do not establish positive joins. Results say that a
terminal source reports a value after a join; association is never causal proof.
Equivalent supported quantities share an SI key. Comparable exclusive values or
opposite polarity retain all evidence and yield disputed, not an arbitrary winner.
Missing context, unsupported units, pending reviews, hypotheses and owner
assertions cannot supply definite calculation inputs.

`source_bindings` on the existing calculate strategy, or a `grounded` investigation
step, select quantities from reviewed source claims and feed the existing Decimal/
SI tools. The assembled result records selectors, annotation revisions, parameters,
source citations, dimensions and epistemic status. Source truth is not implied by
verified arithmetic. Imported/reused results are checked against their pinned
source interpretations and independently recomputed; labels alone confer no trust.

The existing controller routes `semantic_request` to evidence then grounded steps.
It retains checkpoints, crash detection, explicit resume, dependency planning,
cancellation, late-result discard and history. Generation can depend on evidence
and the grounded result using the existing adapter/proposal protocol. This does
not implement unrestricted natural-language planning or automatic scientific
extraction. The initial bridge uses reviewed annotations and structured requests.

## Interfaces and defaults

- Service: `semantic_qualify/get/catalog/evidence/reason`; qualification/reasoning
  retain explicit trusted control approval. Investigation create accepts
  `semantic_request`; existing calculate accepts `source_bindings`.
- CLI: `vector semantic ACTION PARAMETERS_JSON`; ordinary `ask --semantic` enables
  connected context for that request. Example read-only discovery:
  `vector semantic catalog '{"limit":32}'`.
- Desktop: Assistant's **Connected evidence (experimental)** checkbox starts false,
  is not persisted and shows disagreements/qualifications when selected. Existing
  source links remain usable. Structured source-bound calculations are exposed
  through service/CLI/investigations, not a new automatic GUI action.

A trusted request example (claim reviews must already exist):

```json
{"question":"Energy for Lumen test rig","approved":true,"request":{"kind":"calculate","operation":"arithmetic","parameters":{"expression":"p*t","target_unit":"J"},"bindings":{"p":{"subject":"Lumen test rig","sense":"equipment","predicate":"power","scope":"fixture"},"t":{"subject":"Lumen test rig","sense":"equipment","predicate":"duration","scope":"fixture"}}}}
```

Invoke as `vector semantic reason '<JSON above>'`. Fictional fixture equipment is
never installed into production knowledge as empirical science.

Operation defaults are 256 catalog claims, two hops, 32 nodes; validated request
limits allow up to 2048 claims/four hops/128 nodes. These bound an operation, not
collection size or future research. Catalog pagination is explicit. Large corpora
need indexed sense/relationship lookup before corpus-scale deployment. No mass
literary or scientific claim extraction occurs in this stage.

## Qualification and remaining limits

`tools/evaluate_stage6b.py` uses 40 external, human-inspectable gold cases in
`tests/fixtures/stage6b-corpus.json`. They mix exact local publication excerpts and
explicit fictional equipment premises. Gold answers never enter the cognitive
implementation or model prompts. All required citations, statuses, quantities,
negative controls and restart cases are independently scored. The same fixture
runs in regression tests. An optional `--science-pack` rehashes complete preserved
originals and checks excerpt spans against existing extraction artifacts.

Rights remain U.S.-only. Historical medical material is not current guidance;
unsupported natural-medicine claims remain negative controls. Mathematics excerpts
include actual basic calculus coverage discovered during source review, without
acquisition or a claim that formulas/figures are generally extracted reliably.

The completion report records actual A/B/C model scores and resource measurements,
source/installed suites, preservation hashes and limitations. Software integration,
verified fixture performance and measured neural improvement are separate claims.
The experimental path remains disabled by default pending broader qualification.

Checked model observations retain the complete durable result but project a
compact neural view: values/tool parameters, selectors, pinned polarity,
conditions, dates, epistemic/review status and source-span references remain;
repeated original quotes and lookup trees are not duplicated. Citation quotes
still must come from independently supplied context. Old changed annotations are
explicitly marked. The model byte guard is never increased or bypassed by this
projection. Evidence-only Ask (no available adapter) can display qualified bundles
with an independent 8192-byte evidence budget; it cannot dispatch inference.

Actual-model operator evaluation, in a fresh external directory:

```sh
PYTHONPATH=src python3 -B tools/evaluate_stage6b_live.py \
  --corpus tests/fixtures/stage6b-corpus.json \
  --directory /absolute/new/evaluation-directory \
  --models-directory /usr/share/ollama/.ollama/models
```

This uses only the existing0.5B, one request at a time, 8192 context/512 output,
zero temperature/seed, 300-second inference bound, 768MiB cgroup RAM and zero
worker swap. Baseline/resource monitoring stops on low memory, new OOM, material
swap-out, monitor failure or sustained full-memory pressure. Optional `--case`
and `--mode` evaluate an untouched cell after another cell's timeout closed its
worker; they do not retry a failed answer or alter expected criteria.

The production-scale pilot found that keyword retrieval could consume its entire
60-second slice before an already-qualified source query reached the grounded
step. Existing checkpoint resumption completed that saved query without repeating
retrieval. Fully specified selectors with matching reviewed evidence now assemble
that complete qualified package first, including all comparable alternatives and
original rights notices, without searching unrelated unannotated full text. This
choice is explicit in the returned qualifications; it makes no corpus-wide truth
or absence claim. General, unknown and incomplete catalog requests retain direct
passage search as fallback. This does not replace the independent direct baseline
or solve its known corpus-scale latency.
