# Checked cognitive output contract v1

A `vector-cognitive-answer-v1` is a derived view over the existing versioned
investigation state/events, not an independent fact store. Its origin pins the
investigation state revision, selected steps, observation time and question.
The question must equal the pinned investigation goal; a changed question requires a recorded redirect. Every successful step reference precedes that state checkpoint. A stored answer
must replay byte-for-byte (canonical JSON), including rendered text and source
handles; a missing or changed result/status/unit/source/span fails closed.

Each typed finding preserves step/event references, conditional verification
status, subject/predicate, values/units/SI dimensions, operation, source premises
and their sense/scope/conditions/dates/polarity, relationships, source handles,
plan dependencies, observation time, simulation and unverified proposal text.
Supported statuses are checked computation, source-supported report, joined
source inference, dispute, unknown, owner assertion, hypothesis, unverified
proposal and simulation. Future engines can supply independent adapters without
routing all reasoning through a neural model. Unsupported observations are
unknown until an adapter can check their proof. Model claims alone cannot be
promoted by a verification-looking label.

Arithmetic is independently replayed and matched against the recorded requested
expression, explicit/bound variables and target unit. Grounded selectors and
source bindings must match the original request. Pinned semantic interpretations
and exact original source bytes/hash/span are verified. Checked arithmetic is
conditional on its premises and never claims empirical verification. A source
report is not automatically true. Joins preserve relationships, not causal
transitivity. Source dates, conditions, medical/historical qualifications,
original attribution and rights notices remain visible. A dispute never selects
a winner. Owner assertions/hypotheses remain usable without being certified.

Blocks compose these typed meanings into user-facing text; they are separate
from optional language contributions. Mixed checked/unknown answers are partial.
Failed, interrupted or unsupported steps cannot fabricate completed findings.
Historical answers survive restart/restore and later annotation revisions. Fresh
views warn on changed annotations/new disagreements; they do not rewrite history.

The optional handoff replaces repeated full source serialization with local F/S/P
handles and complete logical facts, relationships and applicability. Full quotes,
hashes and rights/provenance remain in the independent answer/store. If the full
packet does not fit the existing byte guard, generation is withheld entirely;
no dependency is clipped and no context window is enlarged. The fixed worker
schema allows only a permutation preserving ALL finding handles and at most four
unverified interpretation/hypothesis notes using existing source handles. Strict
JSON/duplicate-key/unknown-field/reference checks apply. Notes never become
checked findings, modify sources, issue commands or authorize operations.

Persistence reuses `investigations`/`investigation_events`; schema8 is unchanged.
A compose checkpoint and later optional commentary are independent events, so
model failure cannot roll back the completed answer. Portable restoration replays
cognitive-answer records with original sources, restoring the caller's SQLite
row-factory even when verification fails. Finite selection/result/prompt budgets
bound each operation; they are not total memory or lifelong reasoning limits.
