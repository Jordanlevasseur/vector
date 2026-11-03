# Response pipeline repair — measured investigation, 2026-11-03

Baseline installed/source commit: `c608ac2`. This report separates transport,
validation, actual model answers and independent correctness. Release readiness
is **not established**. Installation and final acceptance results will be recorded
below when completed; source-only tests are not installed desktop acceptance.

## Actual greeting failures

The real installed baseline was tested with its installed interpreter and model,
with no source override and a new private evaluation data folder. Minimal raw
Qwen0.5B inference answered “Hello! How can I assist you today?” The old Application
path imposed retrieval/large history metadata and a strict JSON reply. In a real
Application greeting trial, the actual JSON text “Hi” was rejected by the generic
request-echo validator. A salutation can legitimately equal the input. That
reproducible validation defect is fixed; a copied question remains rejected.

The latest saved production “hi” failed differently: selected roleA, no completed
generation stage, timeout during preparation/discovery. Its old prompt was2568
bytes against the2048/192 conservative1600-byte budget, an additional latent
context failure. The historical discovery stall was **not reproduced** in the
idle baseline; its deeper cause is unknown. Do not attribute that saved timeout
to model inability, RAM or JSON without further evidence. An earlier no-selection
path returned capability-unavailable; cancellation had also left workers closed.

During this repair another real trial hit the existing eight-second daemon
readiness deadline although Ollama logged “Listening”. Startup now waits at most
60seconds with bounded2second probes, preserving last-probe diagnostics; parent
qualification is bounded75seconds. A subsequent real trial completed. This does
not prove every historical timeout had that cause or establish unlimited startup
reliability. The failure evidence is retained.

## Implementation

See RESPONSE_PIPELINE_SPEC.md. Existing modules were extended; no duplicate
cognition engine, runtime, database or model was created.

| Files | Behavior |
| --- | --- |
| inference.py, inference_worker.py | Versioned native role messages to the isolated local `/api/chat`; no forced JSON for prose; nonempty/complete output required; typed failures; bounded readiness; rejected truncation metrics retained. |
| model_routing.py | Same durable ModelController; direct ordinary chat, optional answer/review/refinement, unchanged five-phase Both; complete peer handoffs; versioned immutable history/replay; prior work and failures preserved. |
| reasoning.py | Open-ended language scheduling hints, including linked operations; historical hintversion1 replay retained. Hints are not semantic entailment or a catalog of permitted subjects. |
| assistant.py | Existing independent calculations remain durable during model-response preparation/recovery. |
| service.py | Explicit legacy selection agrees with conversation mode; exact model root resolved among authorized stores; one request catalog reused for preparation. |
| worker_launcher.py | Failure/resource diagnostics; safe smaller startup ceiling replaces a binary1536-to768MiB fallback. Owner profile and384MiB reserve unchanged;16MiB extra headroom and launch recheck. |
| desktop.py, desktop_worker.py | Relevant failure/restart, history-selection and independent-calculation notices; error logs list parameter names rather than duplicate raw questions. Existing interface retained. |
| tools/evaluate_runtime_models.py | Fixed independent basic/reasoning/continuity/revision criteria; real resource sampler; optional actual desktop startup profile; expected answers never supplied to the model. |

Security boundaries remain unchanged: namespace/egress denial, user-namespace
restrictions, seccomp, read-only model mounts and hidden host homes, SHA-256/model
identity, CPU quota, pids.max, memory ceiling, zero worker swap, host reserve,
PSI/swap-out/OOM monitoring, inert model output and existing knowledge/citation
attestation. No automatic fact promotion, tool dispatch, model/default/profile
change, owner override or external networking is introduced.

## Actual model identities and trials

A is `qwen2.5-coder:0.5b`, runtime manifest
`4ff64a7f502a08b7616edb8ca0a79eb1853fc363d842b7df4b46915d11a3fb09`.
B is `vector-qwen35-local:2b-q4_k_m`, runtime manifest
`12aa08322906e5b057c85898dfc236f7a11e8fe39a1ea50b7ebbc00193ef6f7a`,
GGUF weightSHA256
`9a3d0aa6c920f096441139b6a254542da855223fdad06855ea00c6c087fd713d`.
B is the existing imported text-only GGUF package, not the full multimodal model.
No model downloaded, replaced or silently substituted.

A, native instructionversion2,2048context/192output/768MiB cap: all seven basic
requests completed actual inference. Only **2/7 fully correct** under independent
review: greeting and arithmetic. Alaska was incorrectly Anchorage; conversation
invented an OpenAI identity despite the identity instruction; engine explanation
was circular/incomplete; pressure omitted force-per-area; missing-problem request
received generic steps rather than clarification. Output delivery is not factual
verification. The earlier instructionversion1 trial also retained all failures,
including rejected engine truncation. No successful model response was fabricated.

A,4096context/256output/768MiB cap: **5/7 protocol complete,2/7 fully correct final
answers** (deduction and contradiction). Multi-step arithmetic returned2.5 instead
of5; ideal resistor current/power failed; mass uncertainty used false mass/volume
claims. Planning and alternatives were rejected for length-stopped output. The
correct deduction's self-critique falsely denied a supplied premise. Initial
rain-gauge alternatives were unsupported, and critique falsely agreed. These
failures preclude claims of reliable engineering, self-correction or discovery.

Linked-step retest,8192context/384output, now ran answer/review/refinement for the
same arithmetic question. It again returned2.5; review explicitly endorsed the
wrong intermediate20. This is measured controller execution, **not** an accuracy
improvement. The larger planning trial completed its initial384-token answer but the critique again length-stopped384tokens; no final plan was accepted. Continuity recovered both cobalt/rain-gauge entities, but the initial response was an unrelated refusal and the recall shifted speaker attribution. Revision initial and feedback turns both length-stopped256tokens, so self-correction was not verified. None of these retries is a successful reasoning qualification.

A final validation repair now rejects a narrowly recognized bare generic refusal as UNFULFILLED_RESPONSE, preserving its actual output. Reasoned uncertainty and explicit quotations remain allowed. Historical validationversion1 stays replayable; new requests useversion2. The real continuity retest produced a visible refusal failure followed by actual entity recall, demonstrating that an unhelpful decline is no longer called a completed answer. This structural validator does not certify the semantic relevance of arbitrary prose.

B: the first fixed1472MiB benchmark could not establish a quiet baseline with the
required384MiB reserve; loading was not attempted. The normal desktop profile
then chose a **smaller1377MiB** ceiling below the unchanged owner1536MiB maximum.
It passed isolation, verified the actual model and reached real loading, but was
stopped by full-memory PSI **70.89%**, above30% for15seconds. The live charged peak
was927543296bytes (~885MiB), below the ceiling; cgroup max/OOM/kill counters were
zero, worker swap zero and host swap-out ~28MiB. Available RAM remained about1.60GiB.
Thus the immediate blocker was sustained memory-pressure stalls during loading,
not a proven context overflow, cgroup-cap hit or simple zero-free-RAM condition.
HDD/reclaim/background demand cannot be causally separated by this one run.
No returned response means **no valid B load-time or tokens/s measurement**.
Scope cleanup passed. No further B workload escalation was attempted.

Full real Both-mode collaboration and B reasoning are **NOT RUN/BLOCKED** after
the failed safe individual-B prerequisite. Five real participant calls were not
replaced by simulations. Both control-flow regression fixtures are explicitly
simulated and do not qualify real collaboration. Both individual modes remain
selectable. Reduce paging demand or upgrade RAM, then rerun the unchanged safe
individualB acceptance before attempting Both; an upgrade is not a guarantee.

## Regression and installed qualification

The initial full source run's nine failures were classified rather than hidden:
actual native/legacy envelope echo/render defects were repaired; new fixture
setup was repaired; old tests for zero selected-model calls and old framing were
updated to the owner's explicit real-inference contract, retaining deterministic
checks, exact legacy v1–3 replay and security validation. Classification and logs
are preserved. Second full source run:331/331 passed in956.221seconds.

The focused response group passed31 tests in54.820seconds, including empty
and copied output, strict optional legacy envelopes/citations, complete handoffs,
wrong math remaining contradicted, idempotency, immutable context/version replay,
approved historical continuation, versioned bare-refusal validation, second-store selection and unmounted-model
rejection, readiness failure/dead daemon and rejected truncation measurements.
Final source suite: **341/341 passed in839.874seconds**, no skips. All113 frozen source/test/tool file hashes matched after the run. Installed-suite and actual desktop acceptance remain pending.

## Evidence and preservation

Private local evidence directory:
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-response-repair-20261103`.

Before work: coordinated consistent SQLite snapshot, original table fingerprints,
original-object metadata, installed-package rollback copy and Git bundle. Source
knowledge/default/profile/model files have not been used as trial output. All
real test data is separate. Final original-data comparison is pending.

This is a finite selected evaluation, not an intelligence benchmark certification.
Model prose, retrieved text, checked calculations and persistent memory are
separate evidentiary categories. No neural learning, human-level reasoning,
independent discovery, safeB reliability or release qualification is claimed.
