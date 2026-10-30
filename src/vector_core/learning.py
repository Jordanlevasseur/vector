"""Reviewable model-proposed claims, with atomic explicit approval and provenance."""
from dataclasses import asdict
from uuid import uuid4
from vector_core.coordination import write_operation
from vector_core.knowledge import ClaimDraft,Knowledge,bounded,KINDS
from vector_core.memory import canonical,now
from vector_core.persistence import register,put


def validate_drafts(memory,drafts):
    if not isinstance(drafts,list) or not 1<=len(drafts)<=32:raise ValueError('Proposal requires 1–32 claims per review batch.')
    result=[]
    for spec in drafts:
        if not isinstance(spec,dict):raise ValueError('Claim proposal must be an object.')
        try:draft=ClaimDraft(**spec)
        except TypeError as error:raise ValueError('Invalid claim proposal fields.') from error
        quote=memory.read_text_span(draft.event_id,draft.start,draft.end)
        bounded(draft.subject,'Subject',200);bounded(draft.predicate,'Predicate',120);bounded(draft.value,'Value');bounded(draft.scope,'Scope',120)
        if (draft.kind not in KINDS or type(draft.exclusive) is not bool or not isinstance(draft.unit,str) or len(draft.unit)>32
            or draft.subject not in quote or draft.value not in quote):raise ValueError('Proposed subject/value must occur in the original quote; no unsupported extraction.')
        result.append((draft,quote))
    return result

@write_operation
def propose(memory,drafts,*,origin):
    bounded(origin,'Proposal origin',500)
    validated=validate_drafts(memory,drafts)
    if memory.db.execute("SELECT 1 FROM persistence_contracts WHERE name='learning_proposals'").fetchone() is None:
        register(memory,'learning_proposals','Reviewable source-linked unverified knowledge proposals')
    identity=uuid4().hex
    record={'id':identity,'status':'pending','origin':origin,'drafts':[asdict(d) for d,q in validated],'created':now()}
    put(memory,'learning_proposals',identity,record)
    return record

@write_operation
def approve(memory,identity,*,approved=False):
    if approved is not True:raise PermissionError('Explicit approval required for proposed knowledge changes.')
    import json
    row=memory.db.execute("SELECT payload FROM persistent_records WHERE contract='learning_proposals' AND record_key=? ORDER BY rowid DESC LIMIT 1",(identity,)).fetchone()
    if row is None:raise ValueError('Proposal not found.')
    record=json.loads(row[0])
    if record['status']=='applied':return record
    validated=validate_drafts(memory,record['drafts']);knowledge=Knowledge(memory)
    memory.db.execute('BEGIN IMMEDIATE')
    try:
        ids=[knowledge._insert(draft,None,'model-proposed; explicitly user-approved; unverified',original_quote=quote) for draft,quote in validated]
        record.update(status='applied',claim_ids=ids,approved_at=now())
        previous=memory.db.execute("SELECT id FROM persistent_records WHERE contract='learning_proposals' AND record_key=? ORDER BY rowid DESC LIMIT 1",(identity,)).fetchone()[0]
        memory.db.execute('INSERT INTO persistent_records VALUES (?,?,?,?,?,?)',(uuid4().hex,'learning_proposals',identity,canonical(record),previous,now()))
        memory.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',(now(),'proposal-approved',canonical({'proposal_id':identity,'claim_ids':ids})))
        memory.db.commit()
    except Exception:memory.db.rollback();raise
    return record
