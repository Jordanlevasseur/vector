# Response pipeline repair — measured investigation, 2026-11-03

Baseline installed/source commit: `c608ac2`. This report separates transport,
validation, actual model answers and independent correctness. Release readiness
is **not established**. The repair is installed and actual desktop response
delivery is verified. Model correctness, safe2B inference and complete real
collaboration remain limited or blocked as measured below.

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
Final source suite: **341/341 passed in839.874seconds**, no skips. All 113 frozen source/test/tool file hashes matched after the run. Installed suite: **341 run,340 passed,1 skipped,0 failures in1077.241seconds**. The skipped positive encrypted-roundtrip requires the optional cryptography dependency absent from the installed interpreter; it is not a pass. The source/system interpreter completed that test. Copied tests/tools and all 50 installed module hashes match the frozen tested code; no source/src directory was present in the installed test root. Actual desktop results are recorded below.

## Evidence and preservation

Private local evidence directory:
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-response-repair-20261103`.

Before work: coordinated consistent SQLite snapshot, original table fingerprints,
original-object metadata, installed-package rollback copy and Git bundle. Source
knowledge/default/profile/model files have not been used as trial output. All
real test data is separate. Closing verification passed: the complete1,347,997,696-byte database snapshot is byte-identical before/after, SHA256 `b24a55dd4b0c5a16aad09eb8f14c1d377c05b171dd0d5a45dbbd4adeca76a745`. All rows in the nine frozen original/knowledge/state tables also match. All4,587 original-object size/mtime/inode records match; no new full original-object content rehash is claimed. Counts remain1,000 literary editions,1,288,804 passages and22 scientific editions. Active profile and Foundational Laws hashes match, as do the19/17 model-store entries and12,829 independent safety-backup entries. Model assets were streamed through SHA256 before real trials; the closing backup check is an inventory comparison, not a new backup content rehash.

The final evidence is `preservation-final.json` and `FINAL_VERIFICATION.json`. A field-format bug in the first audit helper assigned a database digest to the installed-source equality field. It was caught before closure; the initial report is retained. Independent recomputation confirmed all 50 installed hashes against both production source and frozen tested code, rehashed both complete database snapshots, and requires strict boolean checks in the superseding final preservation report. Runtime code and original data were unaffected.

This is a finite selected evaluation, not an intelligence benchmark certification.
Model prose, retrieved text, checked calculations and persistent memory are
separate evidentiary categories. No neural learning, human-level reasoning,
independent discovery, safeB reliability or release qualification is claimed.

## Installed desktop acceptance completed

Verified code checkpoint: `d2aaf3e`, installed by a locally built wheel under
kernel network denial (`pip --isolated --no-index --no-deps --no-compile`). All 50
installed module hashes match the tested build. The production checkout was
cleanly fast-forwarded using the local file transport only. Old installed files
and the previous Git history remain available for rollback.

The actual installed interpreter launched Desktop/bootstrap/backend/worker with
`PYTHONPATH` removed; no source adapter or fixture was substituted. Real model
selection used the Combobox event and submission used the normal Send widget.

| Actual installed check | Result |
| --- | --- |
| Seven basic questions plus repeat greeting |8/8 actual A generations complete and displayed; exact model identities/digests and simulationfalse verified. |
| Visual greeting |Actual window image captured by its X11 ID and inspected; “Hello! How can I assist you today?” is visible under the selected model's unverified-response label. |
| Original failed conversation |The preserved complete private data copy resumed conversatione88a8c34c91f4c8c854614d692f371e3 with the actual unchanged owner runtime profile. New Hi completed/displayed in18.847s, using four historical turns with none omitted. Actual qualified ceiling1390MiB; original working data was not used for test writes. |
| Restart |A separate installed desktop process reopened the prior test database, displayed another actual greeting and returned both saved turns. |
| B/Both/A selectors |All selectable through the actual installed widgets; this check performed no additionalB load or collaboration. |
| Refusal/error recovery |Actual0.5B generic decline is displayed as UNFULFILLED_RESPONSE, with its raw model output preserved. The next actual reply recovers both cobalt/rain-gauge entities from the saved user input; speaker attribution is imperfect. |
| Offline boundary/cleanup |New IPv4/IPv6/Unix socket creation denied in the frontend; model-worker qualification retained. Every desktop test scope cleaned up. |

All seven installed basic outputs were identical to the independently reviewed
source outputs, so semantic correctness remains **2/7**. Display acceptance does
not turn the wrong Alaska/physics/engineering statements into verified facts.
Greeted responses remained actual inference across fresh and restarted sessions.

The greeting image and complete raw responses are in the private evidence folder,
under `installed-desktop-basic`, `installed-original-history`,
`installed-desktop-restart`, and `installed-desktop-continuity`.

## Runtime measurements and limits

Measured source/service basic trial, not a dedicated idle-machine performance
benchmark: A context2048/output192, one inference at a time, CPU quotaonecore.
Actual generation4.43–5.83tokens/s; Ollama-reported load1.64–1.92s; full basic
request8.53–36.62s. First installed Hi14.66s; repeatHi8.51s. Application launch,
asset hashing and any wait for the private runtime are additional to generation.

A sampled aggregate worker RSS peak563404800bytes (~537MiB); charged cgroup peak
176390144bytes (~168MiB), worker swap0. RSS and cgroup charge differ because shared
file-cache pages can already be charged elsewhere; neither is a complete isolated
measurement of unique physical RAM. Host available memory at the quiet baseline
was1762062336bytes (~1.64GiB), minimum1742946304, after unload1863385088 (~1.74GiB).
Peak host swap1762586624bytes (~1.64GiB) includes pre-existing/background use;
worker swap stayedzero, host swap-out~2.16MiB, OOM-counterdelta0. Global memory
recovery values also reflect background activity; clean empty scopes prove
worker termination, not a universal leak-free guarantee.

B's135.16second request includes asset verification/preparation and the interrupted
load. No returned generation means no successful load-time or throughput figure.
Its maximum live charged observation was927543296bytes (~885MiB), sampled worker
RSS peak858771456bytes (~819MiB), worker swap0, peak host swap1785401344bytes
(~1.66GiB); host swap-out~30.6MiB across sampling (~28MiB in the guarded call).
`memory.events` max/OOM/kill counters remained zero. Sustained PSI, rather than those other
thresholds, stopped the run. Background contributors and HDD/reclaim effects were
not isolated, so this is not a proven minimum-RAM requirement for the model.

The controller still uses conservative language hints and a bounded recent-turn
candidate window (64). Tested entity recall and saved history do not qualify
arbitrarily long conversations, general semantic understanding, reliable
self-critique, original discovery or weight learning. Longer planning/revision
outputs remained rejected when incomplete, even with larger explicit budgets.

## Acceptance commands after memory conditions improve

Do not repeat the stoppedB workload in this session. After reducing paging demand
or completing the planned RAM upgrade, first run this unchanged conservative
individualB test. The normal private owner profile and every guard remain active;
no default is changed. Each output directory must be new.

```bash
/home/mint/VECTOR/vector/.venv/bin/python -I -B \
  /home/mint/VECTOR/vector/tools/evaluate_runtime_models.py \
  --store /usr/share/ollama/.ollama/models \
  --store /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-qwen35-evaluation-20261031/candidate-models \
  --runtime-profile /home/mint/.config/vector/local-inference.json \
  --output /home/mint/Documents/Codex/vector-after-memory-upgrade-b-hi \
  --context 768 --output-tokens 96 --modes b --tasks hi --service
```

Inspect `result.json` and `resources.ndjson`: exactB identity, real generated text,
independent semantic correctness, no guard/timeout/truncation failure and verified
cleanup are required. Exit zero means protocol completion only. Any pressure stop
ends escalation; do not change guards to obtain a pass. Successful small-context
loading alone does not qualify longer-context reliability.

Only after the individual trial succeeds safely, use the same command with a new
output directory and `--context 2048 --output-tokens 192 --modes b --suite basic`
in place of the last line. Compare against the unchanged external expectations.
Only after safe individualB operation is established, a new directory with
`--context 4096 --output-tokens 128 --modes both --tasks hi --service` tests all
five real collaboration phases. A successful greeting collaboration would still
require separate held-out reasoning and correctness evaluation. These later
commands were **not executed** during this pressure-blocked session.

## Closing decision

The installed response pipeline and original failed-greeting replay passed actual
Lenovo desktop acceptance. The current0.5B model did not demonstrate reliable
factual, engineering or advanced reasoning. The protected2B loading trial failed;
complete real collaboration is blocked and has no successful final output.
Release readiness remains **false**. Use independently checked tools/evidence for
conclusions; model agreement and fluent prose do not establish truth. Re-evaluate
individualB after memory conditions improve before attempting collaboration or
considering any separately authorized default-model change.

No runtime code changed after the final source/installed suites. The closing
checkpoint updates this report only; the installed code checkpoint is `d2aaf3e`.
Reopen an already-running VECTOR window to load the installed repair.

[Verified installed greeting image](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-response-repair-20261103/installed-desktop-basic/greeting.png)

[Machine-readable final verification](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-response-repair-20261103/FINAL_VERIFICATION.json)
