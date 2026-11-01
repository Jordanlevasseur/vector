# Stage6C evidence audit

Audited starting checkpoint: ede5ce68e40d56c1f9c2b5639689fa9b5b821c00.
Frozen evidence: `outputs/vector-stage6b/live-final-v2/comparison.json` in the
owner's Codex workspace; machine-readable audit in
`outputs/vector-stage6c/stage6b-live-audit.json`. Original hashes are recorded there.
These are the final Stage6B runs, not earlier discarded trial runs.

## Twelve integrated failures

All twelve completed with `done=true`, `done_reason=stop`. Actual input tokens
935–2514 plus the512 output allowance fit8192. Actual outputs41–270tokens;
none hit512. Therefore neither input truncation nor output exhaustion explains
these twelve failures. This does not exonerate context selection or packaging.
Every source/tool result separately met the original expected outcome and
original-source attestation checks (12/12). Every neural result failed the strict
candidate contract (0/12); these rejected outputs remain failures.

|Case|Precise observed mechanism|Other content failure/qualification|
|---|---|---|
|D1|Missing answer/citations; copied source-query, epistemic/status and task-instruction fields into output|Text starts a correct inertia definition but incorporates task instructions. Evidence-to-answer boundary confused.|
|D7|Answer oxygen, empty citations, extraneous source_id/span/quote/date fields at top level|Correct short value alone cannot establish provenance; historical medical qualifiers must remain visible.|
|D8|Answer beta cells, empty citations, extraneous annotation fields|Correct short value; copied semantic record rather than producing the required source-linked candidate.|
|Q1|285 with empty citations and extra status/source_qualifications|Numeric answer matches checked tool, but text mislabels formula as power=duration*time. Neural explanation is not a mathematical proof.|
|Q2|3 with empty citations and extra status/source_qualifications|Correct current value; source attribution absent.|
|J1|Missing answer/citations; text-only narrative|Mentions7.4 but invents component relationships/inverts the joins. Correct terminal number does not verify its explanation.|
|J2|Oxygen, empty citations, extra date fields|Sentence confuses what RBC stores and what protein binds. Terminal value happens to match; multi-hop narration is not reliable.|
|X1|Empty citations; extra semantic fields; selects20W|Substantive contradiction failure: core is disputed between10/20W. Structural repair would wrongly certify an arbitrary winner.|
|C1|Extra prior/request/step/strategy; empty citations; answer8Pa|Value/condition present, but falsely attributes the answer to task specification rather than source. Original bare-value scoring also rejects8Pa versus8.|
|T1|Extra prior/step/strategy; empty citations; answer5Pa|Date-specific content partly retained, but citations missing; original bare-value scoring also rejects5Pa versus5.|
|N1|Missing answer/citations; text-only irrelevant discussion|Sense contamination: fallback keyword retrieval of electrical current introduced ampere into a clinical-current question. Typed core correctly withheld a conclusion. Model failed to keep the negative result and irrelevant passage separate.|
|M1|Returns kind=calculate/operation/parameters; missing text/answer/citations|Copies a tool request rather than reporting the completed285J observation. A tool-call-looking object is data, not execution authority.|

No claim is made about invisible internal model reasoning. Input/output traces
support boundary confusion, record copying, missing attribution, and specific
reasoning/synthesis failures. Temperature0/seed0 make repetitions reproducible,
not correct. Successful independent source lookup is distinct from successful
answer construction; original candidate verification correctly refused all12.

## Prompt guard failure is a separate observation

The production full-provenance two-hop prompt was7761bytes against an existing
7424byte conservative guard. It was refused before generation, not silently
truncated. This is different from the twelve live fixture failures above.
Full SHA/span/quote, publication/rights metadata and annotations were repeatedly
serialized across context, premises and candidate instructions. Small models were
asked to reproduce trusted evidence after it was already checked. Making the
window larger alone does not fix conflict handling, copied records or invented
relationships.

Stage6C therefore composes checked findings directly and offers optional models
short local finding/source handles plus complete logical premises. Full original
provenance remains independently replayable. Inference is withheld if the complete
logical handoff exceeds its operation budget; checked output is not truncated.
