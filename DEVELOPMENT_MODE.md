# Development Mode — manual operation first

The current build defaults to Development Mode. Production release readiness and
reasoning accuracy are separate evaluations and do not authorize or block manual
inference. A genuine completed model reply passes functionality even if wrong,
unhelpful, a refusal or a repetition. No canned replies or simulated production
responses are substituted. Empty output, actual runtime failure and incomplete
output remain distinguishable technical failures, with returned partial text
shown when available. Failed collaboration displays completed participant output
without presenting it as a complete synthesized answer.

Desktop Send defaults to a direct manual response. The existing optional staged
reasoning and evidence/investigation workflows remain available. Both retains
independent A/B responses, reciprocal review and synthesis. Model output remains
unverified; literal-math discrepancies and other quality observations are recorded
separately and do not stop subsequent requests. New native chat validatorversion3
removes quality rejection. Historical validators1/2 remain replayable. Untrusted
JSON/citations displayed as prose never become trusted source links or operations;
structured evidence validators, hashes and authorization remain enforced.

Local AI / memory opens the startup options. Experimental memory is unchecked
until explicitly chosen by the user. Saving it requires a warning acknowledgment
about crashes and resource exhaustion. The owner selects a bounded256–2048MiB
kernel memory ceiling. Apply saves only this choice and the experimental flag to
the private, symlink-free owner profile, preserving authorized model directories,
pids settings and file permissions. Close/reopen VECTOR to apply: core processes
retain their no-exec/no-fork policy, so a stopped worker is not silently relaunched
through a weaker boundary. Configuration changes never activate owner override.

Conservative mode retains the old preflight reserve/asset-size estimates and
PSI/swap-out stops. Explicit experimental mode allows actual attempts despite
estimated size/available-memory mismatch; sustained PSI and host swap-out become
recorded advisories. It does not disable kernel memory.max, zero worker swap,
pids.max, CPU quota, namespace/user-namespace restrictions, seccomp, read-only
mounts, SHA-256 checks or network denial. The hard384MiB observed host reserve,
host OOM-counter stop and monitor-failure stop remain. Private Ollama loading is
bounded240seconds in experimental mode; request timeouts still apply. No guarantee
of successful loading or freedom from crashes is implied.

The normal desktop entry point now loads the existing inference profile even
when a data folder is specified/chosen. --no-inference is an explicit storage-only
session. Trusted startup progress reports file verification/qualification before
health completes. Installed names remain selectable after runtime closure; the
exact startup/loading error remains visible. No availability flag is derived
from an accuracy score or release decision. Model identity and isolation must
still qualify before an actual call can run.

User data, model weights, Foundational Laws, global default-model selection and
existing backups are preserved. Verification results are recorded separately in
DEVELOPMENT_MODE_REPORT.md; no factual-accuracy optimization is part of this stage.
