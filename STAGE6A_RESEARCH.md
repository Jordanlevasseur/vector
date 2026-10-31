# Stage 6A comparative research and engineering decisions

Authoritative requirements: [FOUNDATIONAL_LAWS.md](FOUNDATIONAL_LAWS.md). Research
was performed through the development assistant's reference tools, not by granting
VECTOR or the separate offline assistant network access. No referenced project was
installed, run alongside VECTOR, or copied into the runtime. These are primary-source
claims and engineering inferences, not reproduced external results. Accessed during
this milestone; upstream default-branch links are mutable, not pinned releases.

| Approach / inspected evidence | Mechanism, reported benefit | Limits, model/resource dependence, offline fit | VECTOR decision |
| --- | --- | --- | --- |
| [ReAct paper](https://arxiv.org/html/2210.03629), [official README](https://github.com/ysymyth/ReAct) | Interleave proposed reasoning/actions with environment observations; reported QA and interactive-task improvements. | Capable models and reliable feedback matter; bad actions/retrieval propagate errors. Calls grow with steps. Original setup uses API models; method can use local inference if separately isolated. | Adapt observation/checkpoint cycles and allowlisted pure tools. Model text cannot dispatch actions. No free-form agent shell. |
| [Tree of Thoughts paper](https://arxiv.org/html/2305.10601), [BFS implementation](https://github.com/princeton-nlp/tree-of-thought-llm/blob/master/src/tot/methods/bfs.py) | Generate alternatives, evaluate partial candidates, select branches with search/backtracking; reported Game-of-24 benefit with GPT-4. Inspected code's generation/evaluation/selection loop, caches and duplicate handling. | Branch width, evaluation samples and depth multiply calls/memory; weak self-evaluators can prune correct paths. No evidence that Qwen 0.5B inherits published gains. Fully local execution is conceptually possible. | Adapt alternative DAG branches and independent numeric selection, not mandatory tree expansion or a learned/self-rated universal value function. |
| [LATS proceedings](https://proceedings.mlr.press/v235/zhou24r.html), [official README](https://github.com/lapisrocks/LanguageAgentTreeSearch) | MCTS joins LM value estimates, reflections and external feedback; reported programming/interactive gains with substantially stronger models. | Rollouts and state storage expensive, reward quality critical; cloud examples do not qualify offline operation. README/proceedings inspected, implementation/benchmarks not reproduced. | Retain tests/observations/failures as feedback; defer MCTS until independent local evidence justifies cost. |
| [Reflexion paper abstract](https://arxiv.org/abs/2303.11366), [official README](https://github.com/noahshinn/reflexion) | Episodic textual feedback informs later attempts without weight updates; reported improvements on coding and interaction tasks. | Reflection can memorize erroneous feedback, adds calls/context; strong generator/evaluator needed. Framework can run locally but reference examples use API keys. Not an implementation reproduction. | Retain failed attempts and bounded correction feedback across explicit resumption. Do not promote reflection to fact or claim weight training. |
| [Self-Refine abstract](https://arxiv.org/abs/2303.17651), [README](https://github.com/madaan/self-refine) | Same model generates, critiques and revises; reported aggregate improvements across several tasks using strong models. | Correlated self-errors, extra inference and weak feedback can worsen results. Offline-capable method with local model; external results do not qualify this model. | Critique is an optional strategy; objective verification is distinct and required before claiming objective correctness. No automatic “critique means improved” score. |
| [Hindsight demonstration abstract](https://aclanthology.org/2026.acl-demo.27/), [project README](https://github.com/vectorize-io/hindsight) | Separate world/experience/observation/opinion networks; retain/recall/reflect plus temporal, graph, vector and keyword retrieval. Authors report improved long-context memory, not general discovery. | PostgreSQL/pgvector and extraction/embedding/model dependencies add operational cost; configuration-dependent local feasibility. Abstract/README/license inspected, not internal implementation or reproduced scores. | Reuse VECTOR's original/evidence/assumption distinction and persistent episodes; no new parallel memory server or unverified belief consolidation. |
| [Cognee README](https://github.com/topoteretes/cognee), [cognify implementation](https://github.com/topoteretes/cognee/blob/main/cognee/api/v1/cognify/cognify.py) | Chunk/extract concepts, provenance and graph/vector pipelines support relational recall. Inspected pipeline orchestration imports/tasks, not every backend. | Extraction/embedding quality, graph mistakes and schema evolution affect retrieval. Dependencies and provider configuration matter; README usefulness claims are not independent reasoning evidence. | Add typed interpreted links between investigation results; reuse original-linked context and existing graph records. Defer automatic concept extraction/hybrid semantic retrieval. |
| [MemGPT abstract](https://arxiv.org/abs/2310.08560), [Letta README](https://github.com/letta-ai/letta) | Tiered context and persistent memory with control-flow interrupts; evaluated document analysis and multi-session memory. Current README points to letta-code and historical archive branch. | Requires capable memory management, source retention and bounded context; summaries may lose detail. Local deployment needs qualification; current server/cloud/channel integrations not adopted. | Versioned investigation history plus bounded working context, safe restart and explicit resumption. Do not replace authoritative originals with editable summaries. |
| [Project NOMAD README](https://github.com/Crosstalk-Solutions/project-nomad) | Offline-content management stack integrates local AI/RAG and knowledge/education tools. | Installation/download/update/network behavior and container services are outside VECTOR's current boundary; knowledge availability is not demonstrated reasoning. README/license only, no implementation inspection/reproduction. | Keep offline provenance/content availability, reject installing a second full AI stack or its network/update pathways. |
| [Select-then-Solve paper](https://arxiv.org/html/2604.06753) | Reports task-dependent gains/losses from reasoning scaffolds and benefits of trained routing across multiple stronger models. | Training labels/embedding router and task distribution affect results; even the reported self-routing fails for weaker models. Additional calls are not always useful. No local reproduction. | Transparent task/capability routing: explicit calculation directly; otherwise retrieve then generate/synthesize. Explicit strategy plans refine this. No claim of a learned semantic router. |
| Deterministic verification and finite constraints: existing `tools.py` inspected | Decimal/SI evaluation and finite numeric constraint enumeration provide externally testable results without asking a model to grade itself. | Correctness is conditional on supplied premises/domains, not empirical or general semantic truth. Enumeration grows combinatorially; process in bounded cursor chunks. | Reuse Decimal tools; add chunked finite search, dependent computations, independent numeric checks, and preserve failed candidates. No arbitrary Python evaluation. |

## Licensing and evidence scope

No third-party source code was incorporated; adaptations are original code over
VECTOR's own components. Checked upstream license texts: [ReAct](https://raw.githubusercontent.com/ysymyth/ReAct/master/LICENSE),
[ToT](https://raw.githubusercontent.com/princeton-nlp/tree-of-thought-llm/master/LICENSE),
[LATS](https://raw.githubusercontent.com/lapisrocks/LanguageAgentTreeSearch/master/LICENSE),
[Reflexion](https://raw.githubusercontent.com/noahshinn/reflexion/main/LICENSE) and
[Hindsight](https://raw.githubusercontent.com/vectorize-io/hindsight/main/LICENSE)
are MIT; [Self-Refine](https://raw.githubusercontent.com/madaan/self-refine/main/LICENSE),
[Cognee](https://raw.githubusercontent.com/topoteretes/cognee/main/LICENSE),
[Letta](https://raw.githubusercontent.com/letta-ai/letta/main/LICENSE),
[current letta-code](https://raw.githubusercontent.com/letta-ai/letta-code/main/LICENSE)
and [NOMAD](https://raw.githubusercontent.com/Crosstalk-Solutions/project-nomad/main/LICENSE)
are Apache-2.0 at the inspected paths. Future copying must pin the actual revision,
retain required license/copyright/notices and modified-file notices as applicable;
model weights, datasets, plugins and transitive components require separate review.
Paper licenses do not license every associated implementation. No license clearance
for undisclosed dependencies or models is implied.

Earlier guessed LATS raw paths were unavailable; the proceedings identified the
correct official repository above. No missing source was silently treated as read.
Implementation inspection was limited to the specifically linked ToT/Cognee files
and VECTOR code; other project mechanisms rely on the stated paper/README evidence.
No paper benchmark, external system or published headline score was reproduced.
