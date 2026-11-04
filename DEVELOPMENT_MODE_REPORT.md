# Development Mode functionality correction — 2026-11-03

Baseline4ee4c9e. The owner explicitly prioritizes experimental manual operation.
Functionality, reasoning accuracy and production readiness are independent.
Incorrect model content never constitutes a failed manual inference request.
No accuracy tuning, model training, downloads or default-model substitution is
part of this stage. See DEVELOPMENT_MODE.md for the operational/security policy.

## Actual availability diagnosis

No VECTOR desktop process was running at inspection. The installed menu launcher
points to the installed virtual-environment executable, and the private local
inference profile exists. Recent savedB attempts stopped before any generation
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
- Native chat validator3 accepts genuine incorrect, echoed or declined replies.
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
  SHA checks, offline denial, actual384MiB host reserve/OOM/monitor stops remain.
- Actual incomplete output and failed collaboration show returned partial/completed
  participant text clearly labelled, without fabricating a successful final result.
  Kernel OOM evidence, when available, is reported explicitly rather than guessed.

## Verification

Focused controls passed9 tests, including actual experimental-mode isolation and
pids exhaustion. Response group31 and collaboration group33 passed after explicit
contract migrations: echo/refusal quality is no longer an inference failure;
trusted citation validation is still tested independently. A startup-progress
framing regression was added afterward. Complete source/installed regressions,
real installed manual-mode attempts and closing preservation remain pending.

Tests use explicit simulated adapters for deterministic control regressions.
They do not count as real-model inference. Actual real attempts will be recorded
below by exact identities and completed stages, independently of factual content.
The active profile/default-model selection and original knowledge are preserved;
experimental settings are exercised on a separate private profile during testing.
