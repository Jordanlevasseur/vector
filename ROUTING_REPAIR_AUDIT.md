# Verified routing failure audit — before implementation

Baseline f880e871eb1066a96f285d3ea7b707d559e1c6b8, clean production and checkout.

Actual saved production evidence (read-only inspection):
- Conversation revision a850aa826c164f3596a44912a1ff7a39, 2026-11-02T05:57:03Z:
  question “what is 568 times 564”; outcome evidence-only, no answer or generation,
  error “No separately qualified inference worker selected.” Returned source was
  Workshop on Electronic Texts, a telephone/fax/address passage (564-6750 and
  564-6867), not a calculation. Source 0e5f61f611404e968d5122d384ae5d80,
  original SHA 085e254b52cde93a2adf8c20a2efa8f3ce4e5e467ee66dc85f43536524460c7b.
- Revision db1dc091deb94fbf901ee6996b8ed763, 2026-11-02T05:51:51Z:
  question “sum up the declaration of independence”; outcome evidence-only,
  no answer/generation, same unavailable-worker error. The selected quotation
  was only “The Declaration of Independence”, source 05ac1f599d234a7cae03fe91e35c462a,
  span 9306–9337, SHA ba2c2e011341fdefca027abafd069b135de6bbb826f6a2024efd98cdb41e976a.

## Exact path and causes

Desktop.send_chat sends ordinary ask with planning=False and semantic=False by
startup default. service.Application.handle('ask') enters planner.chat only when
planning is explicitly True; otherwise it calls prepare_inference then assistant.ask.
assistant.ask calls reasoning.plan, whose every task action is retrieve-evidence-only.
It always constructs retrieval context before generation, with no calculator or
checked-answer dispatch. Existing tools/Investigations/findings are disconnected
from this ordinary path; this is not an arithmetic-engine failure.

context.build_context tokenizes the whole request, tries an AND query then per-term
fallback. Thus numbers and ordinary operation words become source-search terms.
It ranks literal overlap, not fulfillment of the operation. Short queries also use
prior questions as retrieval context. A matching number cannot establish arithmetic.

Summarization is not classified or implemented as a distinct request. The same
literal pipeline finds a title/heading. An unavailable adapter cannot generate a
summary; the result remains evidence-only. Desktop.answer displays mandatory rights
notices before its status and then every retrieved quote, with no clear statement
that summarization was unfulfilled. The rights notice plus title is therefore
presented in place of the requested operation. Rights/provenance must remain
available; deleting them is not a remedy.

The experimental planner is separately functional and deliberately opt-in. Its
arithmetic frontend handles explicit symbols/operator sentences but not general
infix times/multiplied-by/percent wording or comma-then chaining. Simply turning
that experimental path on globally would neither justify broad qualification nor
fix all these language cases; historical plan replay must remain compatible.

## Small coherent repair direction

Recognize fully consumed safe arithmetic syntax before retrieval and use existing
Decimal/SI tools, durable investigations and checked composition. Extend the
existing language/decomposition module, not a second reasoning engine. Preserve
ordinary source retrieval as retrieval, distinguish generation requests from quotes,
and truthfully state missing-model/method limitations. Keep explicit planner and
neural pathways available, without globally enabling experimental reasoning or
promoting model proposals to verified findings. Add independent gold cases and
actual desktop replay before/after, including saved history and project context.

No source files were changed before documenting these causes. Full reproduction
and measurements will be retained with the implementation report.
