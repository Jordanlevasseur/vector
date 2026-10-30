# Inference, evidence and reasoning contracts

## Foundation batch
Default CLI security remains seccomp-offline-v1. The new inference adapter has no
remote URL or shared-daemon route: a trusted startup launcher starts a dedicated
Ollama broker under a transient user scope and Bubblewrap, then the core can retain
only explicit FIFO IPC descriptors while denying all sockets/new processes. Worker
qualification checks distinct loopback-only network namespace, absent external
routes, actual external connect failure, disabled nested user namespaces, absent
host home, read-only model blobs and actual cgroup memory.max/pids.max/cpu.max.
Limits default to 768 MiB, 64 tasks and one CPU. There is no RLIMIT_NPROC substitute.
The host RAM reserve is 384 MiB. A failed requirement prevents worker availability.
No global host setting or shared daemon is modified. Model directories are explicit.
Ollama v2 selector links are accepted only for bounded hash-verified manifest blobs
inside the selected blob directory; traversal/other links are rejected.

Replaceable adapters return structured configuration/model/runtime versions and
actual token metrics. Prompt size uses a conservative UTF-8 byte ceiling with
reserved output/template room. Actual runtime context capacity and prompt token
usage are checked; truncation fails closed. This is not an exact tokenizer. Timeout,
cancellation, malformed/excessive frames and crashes terminate the isolated worker.
Explicit test simulation has a separate type and visible simulated marker; it is
never production fallback. No-model operation returns original-linked evidence.

Context construction uses bounded literal multi-query retrieval, deterministic
term-overlap/FTS ranking and original-validated source excerpts. Relevant claims,
scoped disagreements, assessments and user overrides are distinct. Inputs are
untrusted quoted data, never tool/command requests. Model answers require strict
JSON and exact in-context source IDs, hashes, spans and quotes. Verbatim source
statements must match quotes. Generated inferences are labelled unverified:
citation validity is not semantic entailment or proof. Prompt injection can affect
model text; it cannot authorize tools, writes or bypass response validation.

Orchestration has 1–3 bounded attempts, bounded correction feedback and rejects
repeated identical invalid output. Trace records describe retrieval, attempts,
validation/errors/timings, not hidden chain-of-thought. Questions, contexts, outputs,
configuration/versions, uncertainty and operational traces use registered
conversations state and survive portable restore. No generated answer is silently
added as a fact.

Reviewable learning proposals validate original spans, literal subject/value,
typed fields and scope. Explicit approval atomically appends unverified claims,
proposal state and audit; replay is idempotent. Unsupported proposals fail before
any knowledge commit. Original materials remain unchanged.

## Deterministic tools foundation
User-authorized Decimal arithmetic uses a small AST interpreter, never eval/exec.
Known SI dimensions/conversions, affine temperature conversion, linear equations,
basic geometry, bounded statistics and versioned exact SI defining constants are
implemented. Precision/input/exponent/node/list bounds are explicit; nonfinite,
overflow, dimensional mismatch, arbitrary calls/attributes and unauthorized tools
fail. Results/errors and versions use registered tool_runs state. No model can set
the user authorization flag. No engineering-design safety certification or general
symbolic algebra, simulation or uncertainty-propagation claim is made.

## Qualification at the first batch
Existing 67-test baseline passed. Expanded actual-host suite: 81 passed/no skips,
including actual worker namespace/egress denial, per-worker PID exhaustion and
cleanup; evidence/citation/injection, explicit simulation, atomic approvals,
calculation/units/limits and portable new-state restore. Dedicated Ollama 0.40.12
read-only discovery found installed qwen2.5-coder:0.5b. Actual model generation and
desktop profile/workflows are subsequent qualification, not inferred from these tests.

## Integrated application updates
The worker profile is explicitly CPU-only. Ollama GPU discovery can delay readiness
when installed GPU libraries are exposed, so GPU backends are hidden rather than
relaxing startup/isolation checks. Loader/request deadlines are explicit; caller
budgets are bounded. Generation is streamed internally for bounded collection and
retained partial-failure evidence. A stream is accepted only after the runtime's
completion marker; truncated/partial JSON is never promoted to a successful answer.
Operational traces retain raw generation prefixes with SHA-256 and explicit
truncation markers. Model performance/accuracy remains a separate actual-host test.
`model_qualification` provides an independent two-source verbatim-attribution trial;
its expectations are controlled outside model output and it can exercise a complete
real-model managed export/restore before generation. This simple task does not
establish general multi-step reasoning ability, even if a model passes it.
