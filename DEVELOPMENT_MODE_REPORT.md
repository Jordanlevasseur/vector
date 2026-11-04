# Development Mode functionality correction — 2026-11-03

Baseline: 4ee4c9e. Implemented and installed code checkpoint: 1498b51.
The owner explicitly prioritizes experimental manual operation.
Functionality, reasoning accuracy and production readiness are independent.
Incorrect model content never constitutes a failed manual inference request.
No accuracy tuning, model training, downloads or default-model substitution is
part of this stage. See DEVELOPMENT_MODE.md for the operational/security policy.

## Actual availability diagnosis

No VECTOR desktop process was running at inspection. The installed menu launcher
points to the installed virtual-environment executable, and the private local
inference profile exists. Recent saved B attempts stopped before any generation
stage with MODEL_UNAVAILABLE and a cancelled-runtime-startup reason. Older errors
also identify a closed/unqualified worker after cancellation. This is runtime
initialization/recovery state, not evidence of an accuracy gate.

A second confirmed code path could cause the same label: the desktop backend
skipped implicit inference configuration when a data-directory argument was
supplied. The normal desktop entry point now resolves the existing profile even
when opening/choosing a data folder; --no-inference explicitly requests storage
only. No claim is made that the owner necessarily used that path. Startup now
reports file verification/qualification progress instead of an unexplained wait.
Cancelled startup is not misreported as a cancellation of every later request.

## Implemented operation

- Development Mode is the current default build; production readiness is metadata,
  never an operational gate. Functionality and accuracy have separate result fields.
- Desktop manual requests default to one direct generation. Optional existing
  investigation/review flows remain available; Both retains five sequential real
  phases. No model is substituted because another performs poorly.
- Native chat validator 3 accepts genuine incorrect, echoed or declined replies.
  Quality observations and independent math discrepancies are retained separately.
  Model text is displayed as unverified; generated citations do not become trusted
  links or evidence. Historical validators and structured evidence attestation,
  path/hash/model identity checks and operation authorization remain intact.
- Installed local names remain selectable after a stopped runtime, with the actual
  technical reason visible. A stopped/unqualified runtime still requires fresh
  qualification through close/reopen. No exec/fork/network permission is added to
  the protected frontend/core to work around this boundary.
- Local AI / memory exposes a bounded memory ceiling and explicit experimental
  checkbox. Save requires acknowledgment of possible crashes/resource exhaustion.
  The private profile retains authorized roots/tasks/permissions. Reopen applies
  the choice. Experimental mode makes estimates, PSI and host swap-out advisory;
  kernel memory/pids/CPU/zero-worker-swap, namespaces, seccomp, read-only mounts,
  SHA checks, offline denial, actual 384 MiB host reserve/OOM/monitor stops remain.
- Actual incomplete output and failed collaboration show returned partial/completed
  participant text clearly labelled, without fabricating a successful final result.
  Kernel OOM evidence, when available, is reported explicitly rather than guessed.

## Real installed desktop verification

All calls below used the installed virtual-environment package on this Lenovo,
actual Tk model selectors and Send controls, actual private Ollama, and genuine
model output. Tests ran serially using private test databases; no responses were
simulated or substituted. Both used one model at a time and unloaded between
stages. The active owner profile and default model were not changed.

| Desktop mode | Actual result | End-to-end request time |
| --- | --- | --- |
| A: `qwen2.5-coder:0.5b` | Two consecutive real `Hi` replies displayed | 19.426 s, 10.008 s |
| B: `vector-qwen35-local:2b-q4_k_m` | Real `Hi` reply displayed | 215.850 s |
| Both | All five real stages complete; final model response displayed | 324.945 s |

A returned `Hello! How can I assist you today?` twice. B returned `Hello! I am
ready to assist you. Please let me know how I can help.` Both completed independent
A (15.119 s), independent B (106.278 s), review A (29.684 s), review B (70.688 s),
and synthesis B (90.064 s). Its final reply declined to evaluate previous outputs.
That is unhelpful content, but is a completed inference and a functionality pass.
It is not evidence of accurate reasoning or useful collaboration quality.

B and Both used an explicitly enabled **private test profile**, 2048 MiB kernel
cap, 64-task limit, zero worker swap, CPU quota of one core, and unchanged isolation.
The actual desktop warning dialog was acknowledged through its Yes button, the
private settings were saved, and the application was reopened before B/Both.
No active owner-profile change or owner override was made by these tests.

| Measurement | B alone | Both (maximum across stages) |
| --- | --- | --- |
| Sampled worker cgroup memory peak | 1,581,404,160 bytes (1508 MiB) | 1,830,625,280 bytes (1745.82 MiB) |
| Worker swap peak | 0 | 0 |
| Worker kernel OOM / OOM-kill events | 0 / 0 | 0 / 0 |
| Maximum full-memory pressure | 84.40% | 55.57% |
| Lowest observed host available memory | 1,956,114,432 bytes | 2,129,833,984 bytes |

B recorded 318,652,416 bytes of host swap-out during its request. This is an
explicit experimental advisory, not worker swap or a kernel OOM. Its Ollama load
time was 82.896 s; 19 output tokens took 11.570 s (about 1.64 tokens/s). Request
time also includes model verification/preparation and monitoring, so it is not
interchangeable with Ollama's generation duration. Both's final B generation
produced 60 tokens in 39.104 s (about 1.53 tokens/s). Memory figures include charged
file cache and are sampled peaks, not the model's private anonymous allocation.

The installed frontend denied IPv4, IPv6 and Unix socket creation. Worker
qualification verified no routes/external access, nested-user-namespace denial,
read-only model blobs and hidden host/shared model homes. All three desktop
sessions closed with their inference scopes empty. Model identities/digests were
recorded and all generation records report `simulated: false`.

## Regression and preservation verification

The complete source regression suite passed **351/351**, with no skips, in
845.703 s. This includes real namespace, process-exhaustion, offline and resource
controls. A prior interrupted run is retained as interrupted, not counted as a
pass; its sole observed failure was an obsolete UI-label assertion. That assertion
now checks the stopped-runtime label and unavailable flag while retaining all
layout, draft and network checks.

Response and collaboration tests intentionally changed their quality contract:
an echo/refusal/wrong answer is a completed inference; trusted citation validation
continues to reject forged evidence independently. New tests cover continued
operation after wrong/declined replies, startup-profile resolution, startup
progress, stale cancellation diagnosis, explicit warning acknowledgment/private
settings, actual experimental isolation/process exhaustion, and hard resource/OOM
stops. Deterministic adapter fixtures are unit tests, not real-model evidence.

Installed targeted regression passed **89/89**, with no skips, in 228.755 s:
development controls, response pipeline, collaboration, dual runtime and desktop
tests. This is a targeted installed run, not a second complete 351-test run.
The installed package's 50 source modules match the frozen tested build;
installed tests use a copied test tree without `src`.
Earlier reports are historical measurements under conservative policies and do
not disable this build's manual operation.

Closing checks independently confirmed the original active database's complete
byte hash is unchanged, with 4,722 events and 7,987 persistent records. The corpus
still contains 1,000 literary editions, 1,288,804 passages and 22 science editions.
All 4,587 original-object metadata entries, active private profile and Foundational
Laws are unchanged. Both model-store inventories (19 and 17 entries) and existing
independent backup inventory (12,829 entries) are unchanged. Inventory comparisons
cover metadata; they are not a new complete backup-content rehash. Private test
conversations were not imported into owner memory. Previous installed package
bytes were retained separately for rollback.

Raw evidence is in the private workspace directory
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-development-mode-20261103`:
`source-suite.log`,
`installed-controls.log`, `installed-suite-binding.json`, `installation.json`,
`installed-a-and-options/result.json`, `installed-b/result.json`,
`installed-both/result.json`, `preservation-final.json` and
`FINAL_VERIFICATION.json`. These contain actual identities, stages, measurements,
display checks and security/preservation results. No external network was used.

## Owner operation

Open VECTOR normally. Development Mode and direct manual responses are defaults.
Choose A, B or Both on Home / Chat. For an experimental B/Both attempt on this
machine, open **Local AI / memory**, check **Experimental memory estimates (user
controlled)**, set the kernel cap to **2048 MiB**, Save and acknowledge the warning,
then close/reopen VECTOR. This opt-in is deliberately left for the owner on the
active profile. Kernel/OS and offline protections remain active.

The measured B test used context 768, output 96 and timeout 300 seconds. The
measured Both test used context 4096, output 256 and timeout 300 seconds per stage.
These are reproducible test settings, not guaranteed limits for every question.
Use the desktop model settings to select them; submit `Hi` and allow startup and
generation to finish. Both needs five sequential calls. If a runtime stops, its
technical error is shown; close/reopen to qualify a fresh protected worker.
Incorrect replies need no restart and do not block the next request.

This is a functioning experimental build, not a production-qualified product.
No accuracy benchmark, training or factual-answer improvement was attempted.
No claim of broad reliability follows from these short functionality trials.
