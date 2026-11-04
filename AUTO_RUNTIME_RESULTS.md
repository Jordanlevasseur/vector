# VECTOR automatic hardware-adaptive local model management

Completed on the Lenovo, November 4, 2026. Runtime checkpoint **f22b2c8**; installed Python package contains **56 modules**. Development Mode remains the build mode; production release readiness is **false** and does not block manual operation.

## Outcome

AUTO is the recommended persistent default for normal desktop startup. The final installed desktop discovered both existing models without model registration or permission dialogs. It used Qwen2.5-Coder 0.5B for one real message, released the worker, reassessed resources, then selected Qwen 3.5 2B for the next message under the **normal**, nonexperimental profile. Both genuine responses appeared in the desktop. No model was downloaded, replaced, upgraded or made the permanently pinned default.

Actual Both mode completed independent A/B responses, cross-model reviews and synthesis using five genuine calls. Its final response was a refusal. **Execution functionality passed; useful collaborative reasoning was not established by this greeting test.** Accuracy remains separate from availability and operational permission.

## 1. Why manual startup was previously necessary

The old desktop could qualify a private runtime yet still have no selected generation model. Its A/B discovery contained fixed Qwen identifiers, and no AUTO policy resolved an empty selection. The fixed memory profile, one-CPU worker settings and conservative resource checks could make B unavailable. A stopped worker could not be recreated after the core activated its mandatory no-execution filter, so reopening VECTOR was the recovery path.

The advanced “External model dependency” acknowledgment meant weights were outside VECTOR's managed portable store. It was a backup/export obligation, **not internet permission**. The private owner-controlled startup profile approved particular model directories for read-only access. This distinction is documented in [STARTUP_AUDIT.md](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/STARTUP_AUDIT.md).

## 2. Authorization boundary

Existing approved roots remain unchanged: `/usr/share/ollama/.ollama/models` and the existing Qwen 3.5 candidate store. Normal selection within them needs no renewed acknowledgment. Required external-file obligations are still recorded using the existing provenance/portability system.

No approval for local weights grants internet access. No arbitrary home-directory mount, downloaded executable, remote registry, cloud inference or externally reachable private worker endpoint is introduced. A **new model root** still requires one explicit narrowly scoped local grant and a fresh protected startup. A new experimental resource grant also requires explicit acknowledgment; it remains manual-only. Applying a new grant/profile is exceptional setup, not routine per-message operation.

The owner profile, launchers and Foundational Laws are byte-for-byte unchanged. The separate pre-existing experimental test profile was reused for the labelled manual B/Both trials; the production profile was not changed to experimental.

## 3. Discovery and compatibility

The generic catalogue reads only approved local Ollama stores. It supports canonical local model/tag, author/model/tag and supported registry namespaces, bounded manifest/configuration parsing and bounded scalar GGUF metadata. It records names, architecture, quantization, parameters, native context, weight size and availability reasons. Unsupported or damaged packages remain diagnostic entries; an unavailable store does not hide a separate valid approved store. No remote registry is queried.

Inventory presence is provisional. Complete selected dependency hashes remain a launch gate; private runtime `/api/tags` and `/api/show` establish actual local metadata support. Tool capabilities are runtime-advertised metadata, not proof of reliable tool use or authorization to execute tools. Only genuine completed inference sets functional observations. Simulated tests never count as real model success.

An actual first trial exposed Ollama's v2 identity distinction: the legacy source manifest and linked v2 selector have different hashes. The implementation retains both and permits only identities in the verified graph; generation must match the frozen actual runtime identity. A regression caught an overly broad selector check; it was fixed to require a verified **manifest** dependency, not any dependency blob. The rejection test was left unchanged. No digest check was weakened.

The 2B package remains the locally imported **text-only GGUF**; these results do not validate an official full multimodal Ollama distribution.

## 4. Actual hardware and AUTO selection

Observed physical RAM: **3.706 GiB**. Swap: **3.926 GiB**. CPU: **x86_64**, **4** affinity CPUs, effective CPU allowance **4.0**. Observed filesystem capacity/free space: **145.156 GiB / 64.736 GiB** at the sampled data location. The detector also reads CPU flags, disk capacity/free space, ancestor cgroup memory/CPU/pids limits, memory pressure and GPU descriptors. This Lenovo's Intel device `8086:0126` has no qualified compute backend or reported dedicated VRAM in this implementation.

AUTO refreshes hardware at startup and before tasks. It selects among exact installed candidates using relevant capability/owner preferences, a provisional ranking and safe resource estimates. Parameter count is not evidence of reasoning quality. Accuracy scores do not exclude a model. When current full-memory PSI reaches the existing 30 percent threshold, AUTO prefers the lowest-memory viable candidate; manual choices remain exact.

Estimates include weights, runtime/generation buffers and context-dependent state. Genuine measured peaks may raise the estimate but cannot erase the weight floor: warm/shared page-cache charge can be much smaller than physical model requirements. Swap is never counted as model RAM. Memory budgets preserve at least384 MiB host headroom, increasing with host size; actual cgroup/host limits are checked again at launch. Normal AUTO never borrows experimental consent.

Valid complete requests can increase context automatically in bounded steps. Required instructions and the current question are not truncated. The existing2000-character question limit remains enforced. The trusted context protocol remains512–32768 tokens. Manual memory ceilings can scale above the previous fixed 2 GiB limit on capable hardware, while effective host/cgroup bounds and reserves still constrain execution. An8 GiB profile on a simulated 16 GiB host and clamping after movement to a smaller host are policy tests, **not actual upgraded-hardware inference**.

## 5. Startup and recovery architecture

The normal desktop starts a small data-blind offline controller before the core's mandatory filter. Its private namespace has no IP sockets or host process directories; code and approved model mounts are read-only. It retains only the fixed local user-manager control path. Host-root-owned executable fingerprints are verified across the user-namespace ownership mapping.

The desktop/core retain explicit pipes, including a bounded diagnostic pipe; their original socket/execution denial remains enforced. The controller accepts fixed named operations and exact approved model identities, never model-generated commands, paths, endpoints or environment variables. Each inference service still receives full namespace/seccomp/filesystem qualification and independently checked memory, zero-swap, CPU and pids limits. Worker services are bound to the controller's lifetime.

Discovery, verification/startup/qualification, model loading and readiness are surfaced as progress. Failed or cancelled requests do not save a permanent AI-disable flag. Worker stops, crashes and cancellation can qualify a fresh worker within the session. Unverified cleanup retains the exact old unit identity and prevents replacement until cleanup succeeds. A **controller-process crash itself** still requires a new application startup; it is now reported distinctly with bounded original diagnostics rather than as a misleading ready state.

AUTO resource fallback preserves the failed run and creates a new parent-linked run with the same complete request/evidence and exact new model binding. It is limited to three distinct candidates plus one transient worker restart. Integrity/qualification failures, malformed/incomplete outputs, cancellation and inaccurate answers do not cause silent substitution. Explicit manual A/B/model/Both selections never substitute another model.

## 6. Real inference results

All rows below use actual installed Ollama 0.40.12 and genuine responses, with worker swap0. End-to-end time includes verification, provenance work and startup; generation speed alone does not describe the cold-start wait.

| Test | Actual model | Context/output | End-to-end | Ollama load | Generated tokens/s | Maximum sampled cgroup charge | Experimental |
|---|---|---:|---:|---:|---:|---:|---|
| Final AUTO message 1 | qwen2.5-coder:0.5b | 2048/192 | 25.82s | 1.44s | 18.03 | 154.5 MiB | False |
| Final AUTO message 2 | vector-qwen35-local:2b-q4_k_m | 2048/192 | 243.84s | 34.30s | 6.34 | 1414.5 MiB | False |
| Manual B, existing experimental profile | vector-qwen35-local:2b-q4_k_m | 768/96 | 182.15s | 66.98s | 6.21 | 1258.6 MiB | True |

Final normal AUTO B used MemoryMax **1651.0 MiB**, with actual CPU quota400percent, four configured threads and pids maximum64. Its maximum observed full PSI during generation was **7.6**, and host swap-out during that generation was **8.6 MiB**. No experimental waiver was active.

Both mode completed in **481.83s**, context4096/output256, under the existing 2 GiB experimental test ceiling. Maximum sampled worker charge was **1782.2 MiB**, with zero worker swap. All five stages were genuine and used A,B,A,B,B in order, with runner unloading before each subsequent stage. These manual B/Both trials ran at checkpoint 3dc0a4d; the final f22b2c8 change adds AUTO-only pressure preference and truthful controller availability. The inference worker, manual generation controller and protected launcher are unchanged between these checkpoints. Final AUTO independently reverified actual A and B generation at f22b2c8.

Cgroup figures are sampled charges, not a claim that the full physical model needs only that RAM. Shared/warm file cache may be charged elsewhere. Total host swap includes pre-existing application usage. During the Both trial total system swap reached **1.663 GiB**; it must not be attributed entirely to the models. Latencies varied considerably on this machine; these are observations, not isolated performance benchmarks.

Evidence: [final AUTO](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-final-auto/result.json), [manual B](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-manual-b-experimental/result.json), [five-stage Both](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-both-experimental/result.json).

## 7. Failures and limits were kept visible

A normal-profile manual B attempt failed after225.13s when the controller exited; the original stderr was unavailable and qualification remained stale. Code review also found that an error-path cancellation write could mask the original diagnostic. Those diagnostic/state defects were corrected: EOF clears qualification, original stderr is retained, cancellation does not replace the original error, and cleanup failures remain fail-closed. **The original controller exit's underlying cause could not be reconstructed because its stderr had not been retained.** It is not labelled an OOM or a model-quality failure.

A diagnostic repeat failed after180.78s with the exact normal-policy cause: full-memory PSI above30 percent for15 seconds, observed avg10=51.2. Worker swap, host OOM increments and cgroup OOM counts were zero. This was a measured resource-protection block, not evidence of unsupported architecture. Later genuine B inference succeeded with the scoped experimental profile, and the final normal AUTO B trial also succeeded with its freshly derived budget. The evidence does not support a claim that2B is always unavailable on3.7 GiB RAM or always reliable under load.

Three protocol fixtures exceeded their unchanged3-second startup deadlines while targeted regressions ran alongside Both mode. The identical57-test isolated rerun passed. This is recorded as environment contention; fixture deadlines were not increased or skipped to manufacture a pass. The complete installed suite runs with inference stopped.

The existing profile test's fixed4 GiB-invalid assumption was replaced by an actual protocol-overflow case, because4 GiB is valid on a larger host. New tests also reject a profile consuming the simulated host's entire RAM and exercise host-reserve clamping. This updates the test to the hardware-adaptive contract rather than weakening resource enforcement.

## 8. Final verification

- Corrected source milestone: **396 passed**, no skips, at c854be5; this includes the source interpreter's optional encryption round trip.
- Final installed suite: **405 passed, 1 skipped, 0 failures, 0 errors**, 406 total. The copied test tree has no `src` fallback; every installed module hash is bound to the final wheel snapshot.
- Skipped reason: **Optional offline cryptography dependency absent; encrypted roundtrip not verified in this interpreter**. A skip is not a pass, and the optional dependency was not downloaded.
- Final desktop AUTO and cancellation recovery passed. Cancellation stopped only the current request; the next real message succeeded without reopening.
- Actual installed process-exhaustion probe denied excess children and cleaned **52** of them. Killed-worker restart, client-EOF cleanup and controller-crash dependency cleanup passed.
- Final installed Library opened the preserved original **Frankenstein; or, The modern Prometheus**, displaying **15725** original characters in a bounded read, with no model runtime. Home/Chat, Projects, History and Library navigation remained present.
- Final preservation: database bytes unchanged, stored original files verified **4587**, no stored-byte or object-metadata changes. The previously verified4588 raw original streams remain valid because both the stored bytes and their database descriptors are identical. No repeated full passage extraction or corpus reimport was needed.
- Catalogue entries **4722**; schema **8**; active counts **{'events': 4722, 'sources': 2069, 'persistent_records': 8258, 'claims': 14, 'entities': 15}**. The1022 editions and1288804 indexed literary passages remain in the unchanged database.
- Profile, both launchers and Foundational Laws match their pre-change hashes. No HELIX, Essential SOP, model, original document, knowledge-index or backup changes were made.

Details: [installed-suite-result.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-suite-result.json), [installed-suite-binding.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-suite-binding.json), [preservation-final.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/preservation-final.json), [installed-library-smoke.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/installed-library-smoke.json), [control-faults.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/control-faults.json).

## 9. Exact files and storage changes

- [AUTO_RUNTIME.md](/home/mint/VECTOR/vector/AUTO_RUNTIME.md)
- [src/vector_core/adaptive_runtime.py](/home/mint/VECTOR/vector/src/vector_core/adaptive_runtime.py)
- [src/vector_core/desktop.py](/home/mint/VECTOR/vector/src/vector_core/desktop.py)
- [src/vector_core/desktop_worker.py](/home/mint/VECTOR/vector/src/vector_core/desktop_worker.py)
- [src/vector_core/inference_worker.py](/home/mint/VECTOR/vector/src/vector_core/inference_worker.py)
- [src/vector_core/model_routing.py](/home/mint/VECTOR/vector/src/vector_core/model_routing.py)
- [src/vector_core/models.py](/home/mint/VECTOR/vector/src/vector_core/models.py)
- [src/vector_core/runtime_policy.py](/home/mint/VECTOR/vector/src/vector_core/runtime_policy.py)
- [src/vector_core/runtime_supervisor.py](/home/mint/VECTOR/vector/src/vector_core/runtime_supervisor.py)
- [src/vector_core/service.py](/home/mint/VECTOR/vector/src/vector_core/service.py)
- [src/vector_core/worker_launcher.py](/home/mint/VECTOR/vector/src/vector_core/worker_launcher.py)
- [tests/test_adaptive_runtime.py](/home/mint/VECTOR/vector/tests/test_adaptive_runtime.py)
- [tests/test_development_mode.py](/home/mint/VECTOR/vector/tests/test_development_mode.py)
- [tests/test_runtime_policy.py](/home/mint/VECTOR/vector/tests/test_runtime_policy.py)
- [tests/test_runtime_supervisor.py](/home/mint/VECTOR/vector/tests/test_runtime_supervisor.py)
- [AUTO_RUNTIME_RESULTS.md](/home/mint/VECTOR/vector/AUTO_RUNTIME_RESULTS.md)

New runtime components are `runtime_policy`, `runtime_supervisor` and `adaptive_runtime`. Existing asset validation, inference worker, durable model controller and desktop were reused. There is **no database migration, new knowledge system or new dependency**. Runtime selection preferences and actual observations use existing persistence contracts; acceptance conversations were kept in private test databases. Forty-six previous application modules, including Library readers and the core network filter, remain byte-for-byte unchanged.

## 10. Rollback and remaining authorization

The pre-change package is preserved in `/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/before-installed` and matches all53 modules in the verified rollback wheel `/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-library-implementation-20261103/wheels/vector_offline-0.1.0-py3-none-any.whl`. Source history is preserved in `/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/before-auto.bundle`. The existing complete verified data snapshot was reused only after matching its identity and checksum; no working data was restored or overwritten. See [preservation-before.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/preservation-before.json) and [rollback-wheel-verification.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-auto-runtime-20261103/rollback-wheel-verification.json).

Normal current-root operation needs no new owner authorization. New model roots and new experimental grants still require explicit scoped approval. No such grant can authorize networking. Fatal controller failure requires reopening, while ordinary worker recovery does not. Close VECTOR before applying any rollback package; package rollback does not require modifying the original-data store.

## 11. Remaining limitations and recommendation

Use AUTO now. It has genuinely executed both installed models on this Lenovo, and it can prefer the smaller model under pressure. Keep manual B and Both available for experiments; they are slow and can encounter resource-protection stops. The16 GiB upgrade should improve headroom and reduce contention, but it is not a prerequisite for manual inference and has not been physically tested here.

GPU execution and parallel collaboration remain unqualified. The registry/plans support additional names/participants, while the current collaboration executor retains two sequential roles. AUTO conservatively selects one model rather than automatically forcing Both. Managed-model import/launch retains its existing explicit workflow; arbitrary directories are not silently authorized. Installed models added within approved stores are rediscovered at the next startup.

The final Both refusal and known small-model limitations remain accuracy/utility evidence for later work. This stage did not train models, alter Foundational Laws, enable owner override or begin a new cognition stage. **This is a working experimental build, not a production-ready release.**
