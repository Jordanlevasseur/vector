# Native conversation and durable reasoning execution

This repair extends the existing Application and ModelController. It introduces
no second cognition engine, model, database, default selection or network path.
Foundational Laws remain unchanged. Implementation is not a claim of measured
reasoning accuracy or release acceptance; see RESPONSE_REPAIR_REPORT.md.

Ordinary conversation uses an internal versioned `chat-text-v1` packet containing
native system/user/assistant messages. The worker sends those messages only to
its isolated local Ollama `/api/chat`, with thinking disabled per request. Plain
text requires no JSON response envelope or archive retrieval. An exact legacy
four-field response envelope is optionally parsed under its original strict
validator, including citation attestation. Evidence-backed summaries, explicit
retrieval and opted-in semantic investigations retain their existing validators
and historical version1–3 prompt replay. No model text dispatches an operation.

Task interpretation provides open-ended scheduling hints rather than an approved
subject catalog. Short requests use one generation; more complex requests may use
an initial answer, critique and refinement. Both mode retains two independent
answers, reciprocal reviews and synthesis, using actual bound identities. Every
peer handoff is complete and budget-checked. Agreement is not verification.
Generated conclusions stay unverified persistent records, never automatic claims.

Every current request is saved before preparation. Input/output provenance,
manifest identities, stage attempts, immutable hashes and completed work survive
restart. History uses a declared bounded selection of complete previous messages;
full originals remain saved. Omitted turns are disclosed. Current instructions,
request and peer output are never silently shortened to fit. Excess context,
empty/echoed questions, length-stopped output and forged citations fail closed.
A greeting equal to a salutation is legitimate; a copied question is not. New
validationversion2 rejects a narrowly recognized bare generic refusal as
unfulfilled; specific uncertainty and requested quotations remain eligible.
Version1 historical outcomes stay readable under their original validator.
This is a structural screen, not a general relevance or truth certification.

With a selected model, supported literal arithmetic invokes that real model and
also retains the existing independent computation from the original user input.
A wrong model answer remains visible and contradicted, never replaced by the
computed answer or used to authorize a model-proposed tool. Other prose is not
certified merely because it completed transport validation.

Failures distinguish preparation, discovery, metadata, generation, context,
response validation, worker closure and live resource protection. Rejected
truncation retains partial-output hashes, completion reason, runtime metrics and
resource observations. Cancellation preserves completed stages and closes the
worker; restart requalifies isolation before explicitly authorized continuation.
Desktop error logging records parameter names, not a duplicate raw question.

External-model selection resolves the exact model only within already authorized
mounted stores, checks conflicting manifests and preserves SHA-256 registration.
The startup fallback may select only a smaller memory ceiling than the owner
profile, below current available RAM minus the unchanged384MiB reserve plus an
extra16MiB margin. Launch rechecks the reserve. Namespace, seccomp, filesystem,
CPU, pids, memory/no-worker-swap, OOM, host swap-out and PSI guards are unchanged.
No permanent profile, default-model, knowledge or backup changes are part of this
repair. A model that cannot operate within these limits remains blocked.
