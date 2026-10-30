# Knowledge specification
A source statement is evidence that the source says something, not proof it is true.
Claims must reference exact original event/text spans. Entities, attributes and
relationships form derived source-linked data. Assessments are append-only versions
with uncertainty, reasons and cited evidence. Contradictions are supported only for
explicitly comparable scopes and predicates; ambiguous language, temporal changes
and different units must not be collapsed into contradiction. Overrides append an
explicit user-authorized operating assumption and scope while preserving previous
assessments and conflicting evidence. No neural fine-tuning is implemented. Model
extraction, if later supported, proposes claims but never silently rewrites evidence.

## Implemented Stage 4 and limitations
`entities` uses exact NFC/whitespace-normalized, case-preserving labels; no fuzzy
entity resolution or semantic equivalence is claimed. `claims` retains event,
character span, exact quote, predicate, value, kind, explicit scope/unit and origin.
Typed kinds cover claims, hypotheses, definitions, observations, procedures, events,
measurements, attributes and relationships. Classification alone is not understanding.

`learn` commits the raw event first, then parses at most 100 explicit
`subject | predicate | value` lines into unverified claims. Unsupported lines remain
in the archive and are counted. Failure records retain the event ID. Repeat parser
runs are idempotent for a given event/scope; repeated submissions remain distinct.
Manual ClaimDraft proposals are explicitly user interpretations, not verified
extractions. Quotes are checked against original bytes on retrieval.

Potential disagreement requires both claims explicitly exclusive and identical
subject/predicate/scope/unit, with different literal values. Different dates/scopes
or units are not silently treated as contradictions; equivalent numeric/linguistic
values are not inferred. Case-sensitive scientific values remain distinct.
No N-squared materialized conflict graph is created; bounded grouped queries return
original-linked competing evidence. One-hop relationship and exact entity lookup
are supported; general graph reasoning is not.

Assessments retain prior IDs, uncertainty, reasons, actor and cited claim IDs.
Overrides require explicit authorization and exact scope, retain previous assessment
and override IDs, and never change evidence. Latest correction follows append order,
not wall-clock order. The operating value is marked a user-authorized assumption;
conflicting source claims remain visible. No neural training or automatic truth
certification, unrestricted extraction or general reasoning is implemented.
