# Verified question-to-investigation planning

Status: experimental, opt-in. Original Ask and investigation interfaces remain
available. No model selection, permission, schema or Foundational Law change.

## User path and scope

The Assistant's **Plan and investigate question** checkbox routes the same
ordinary question entry through `Application.handle('ask', planning=True)`.
CLI: `vector ask 'Calculate (13 + 7) * 2; then divide the result by 8.' --plan`.
The result is 40 followed by 5, with an independently replayed dependency. Simple
literal arithmetic bypasses the semantic catalog and never requires inference.
`vector question plan|get|run|revise|explore PARAMETERS` exposes the same durable
records. Parameters are trusted user controls, never model instructions.

`planner.py` compiles conservative language into existing investigation steps.
Reviewed subjects, aliases, predicates, conditions, senses, scopes and explicit
relationship paths come from semantic memory, not a fixed list of subject areas.
Explicit arithmetic uses the existing safe expression/unit tools. Source-bound
quantities followed by further arithmetic currently need an explicit supported
binding or a revised method; the frontend never assumes their value or unit. The frontend
does not infer an unstated physical formula, silently select an ambiguous sense,
or treat a component property as an intrinsic property of its parent.

Unconsumed meaningful words, missing applicability, incomplete catalog/path
slices, unknown methods and unfamiliar ideas remain explicit unresolved
objectives. This is a limited language frontend, not general language entailment.
A completed workflow can correctly report that it has no answer. A positive
finding means checked source attribution or computation for stated premises;
it does not certify the source's empirical truth.

## Plan, verification and revision

`vector-question-plan-v1` records the full objective, clarification, constraints,
assumptions, pinned semantic-record basis, methods, evidence requirements,
dependencies, unresolved interpretations, alternatives, completion criteria and
next actions. Existing `investigations` and `investigation_events` store the plan
and results. No planner database, second event log or schema migration is added.

The deterministic compiler is replayed against the historical reviewed catalog
at its pinned basis. Replay detects changed metadata and dependencies; it is
not an independent proof that English was correctly understood. Existing typed
findings, original SHA-256/span checks, semantic applicability/conflict checks,
unit arithmetic, prior-result verification and answer composition provide the
operation-specific validation. Planning metadata cannot contribute factual
values. Portable imports and saved history reconstruct checked views rather
than trusting cached answer text. New interpretations preserve negation,
hypotheses, owner beliefs and conflicting evidence under the existing contracts.

Revisions retain completed records and append a new plan boundary and answer.
Answers from an earlier boundary are not displayed as the new result. Completed
intermediate source/calculation findings are reconstructed and explicitly labeled
as unfinished work when a run pauses before answer composition. Changing
a goal through the original controller invalidates its old interpretation until
rebuilt. Human-approved alternative methods remain available through the
original investigation controller. Model suggestions cannot call it.

Catalog pages (256 records), path depth (4), frontier (64), objective slices (16),
step sizes and existing workflow limits bound resource use. Truncation is
reported as incomplete coverage. Narrowing, cursor continuation or a linked
investigation permits further work without discarding earlier evidence. These
are operational slices, not a limit on permissible ideas or fields of inquiry.

## Recovery and authority

A conversation saves its pending turn and selected investigation UUID before
creation/execution. Retrying that request UUID reuses logical work. Completed
steps are recovered from existing events; paused/cancelled/running investigations
use the original explicit resume/revision controls. A saved pending creation can
be retried without inventing an answer. Reusing a request identity for a different
question, project or constraints is rejected. No exactly-once guarantee is made
for an in-flight model computation interrupted before its result is committed;
its recorded completed work is never silently rerun.

Planning grants only the existing ordinary pure-local-reasoning delegation.
It does not enable privileged owner authentication, overrides, external access,
shell execution, project edits or self-modification. Ordinary source and model
text is untrusted data throughout.

## Optional neural exploration

The explicit **Explore unverified ideas** action retrieves bounded evidence and
uses the existing qualified model adapter/worker once. `proposal-text-v1` permits
ordinary prose so hypothesis generation need not satisfy a brittle JSON schema.
Existing answer/claim/notes JSON contracts remain unchanged. Prompt and output
budgets remain bounded; essential objective/evidence is not silently truncated.
The real response and runtime attestation remain in investigation evidence.

Proposals are typed unverified findings with no automatic citations, factual
replacement, plan execution, authorization or promotion to established truth.
A valid response format is not a correct hypothesis. User inspection, a revised
method and independent verification are still necessary. Larger future models
can use the same adapter; no model is required for checked routine operations.

## Evaluation

`tools/evaluate_question_planning.py` scores frozen, external fixture expectations
for outcomes, units, exact source fidelity, required attribution, explicit gaps,
operation selection and real multistep dependencies. Gold does not enter the
planner or prompt. Two explicitly structured user controls are supplied equally
to the old/new pathways. The original direct and investigation outcomes were
captured at unchanged `945c9aa` before the new implementation. A separate transfer
set uses new subjects, domains and values. Results measure this tested scope,
not general intelligence or autonomous discovery. A/B lack the new plan metadata,
so their plan-quality field is not applicable; all three have the same outcome
criteria. Neural protocol success, actual proposal usefulness and verified
findings must be reported separately. Previously passing 52 model-disabled
checked cases remain part of the full regression suite.
