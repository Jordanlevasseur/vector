"""Source-linked unverified claims, scoped disagreements and versioned authority.

Only explicit pipe statements are extracted. There is no general language
understanding, automatic truth certification or model-weight training here.
"""
from dataclasses import dataclass
import math
import sqlite3
import unicodedata
from uuid import uuid4

from vector_core.memory import canonical,now

KINDS={'claim','hypothesis','definition','observation','procedure','event','measurement','attribute','relationship'}


def normalized(value):
    return ' '.join(unicodedata.normalize('NFC',value).split())


def bounded(value,name,maximum=1000):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:
        raise ValueError(name+' must be bounded nonempty text.')
    return value.strip()


@dataclass(frozen=True)
class ClaimDraft:
    event_id: str
    start: int
    end: int
    subject: str
    predicate: str
    value: str
    scope: str
    unit: str=''
    kind: str='claim'
    exclusive: bool=False


class Knowledge:
    def __init__(self,memory):
        self.memory=memory;self.db=memory.db

    def _entity(self,name):
        key=normalized(name)
        row=self.db.execute('SELECT id FROM entities WHERE normalized=?',(key,)).fetchone()
        if row:return row[0]
        identity=uuid4().hex
        self.db.execute('INSERT INTO entities VALUES (?,?,?)',(identity,name,key))
        return identity

    def _insert(self,draft,text,origin):
        if type(draft.start) is not int or type(draft.end) is not int or not 0<=draft.start<draft.end<=len(text):
            raise ValueError('Claim span outside original text.')
        quote=text[draft.start:draft.end]
        if len(quote)>4000:raise ValueError('Claim quote exceeds 4000 characters.')
        subject=bounded(draft.subject,'Subject',200)
        predicate=normalized(bounded(draft.predicate,'Predicate',120))
        value=bounded(draft.value,'Value')
        scope=bounded(draft.scope,'Scope',120)
        if not isinstance(draft.unit,str) or len(draft.unit)>32 or draft.kind not in KINDS or type(draft.exclusive) is not bool:
            raise ValueError('Invalid unit, kind or comparability flag.')
        subject_id=self._entity(subject)
        object_id=self._entity(value) if draft.kind=='relationship' else None
        key=normalized(value)
        params=(draft.event_id,draft.start,draft.end,subject_id,predicate,key,scope,draft.unit,draft.kind,int(draft.exclusive))
        found=self.db.execute('SELECT id FROM claims WHERE event_id=? AND start_char=? AND end_char=? '
            'AND subject_id=? AND predicate=? AND value_key=? AND scope=? AND unit=? AND kind=? AND exclusive=?',params).fetchone()
        if found:return found[0]
        identity=uuid4().hex
        self.db.execute('INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (identity,draft.event_id,draft.start,draft.end,quote,subject_id,predicate,value,key,
             scope,draft.unit,draft.kind,int(draft.exclusive),object_id,origin,now()))
        return identity

    def add_claim(self,draft):
        text=self.memory.original(draft.event_id).decode('utf-8')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            identity=self._insert(draft,text,'user-proposed interpretation; unverified')
            self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                            (now(),'claim-proposed',canonical({'claim_id':identity})))
            self.db.commit()
        except Exception:self.db.rollback();raise
        return self.claim(identity)

    def claim(self,identity):
        row=self.db.execute('SELECT c.*,s.name AS subject,e.source_id,e.sha256 FROM claims c '
            'JOIN entities s ON s.id=c.subject_id JOIN events e ON e.id=c.event_id WHERE c.id=?',(identity,)).fetchone()
        if row is None:raise KeyError('Claim not found.')
        result=dict(row)
        text=self.memory.original(result['event_id']).decode('utf-8')
        if text[result['start_char']:result['end_char']]!=result['quote']:
            raise ValueError('Claim quote does not match its original event.')
        result['verification']='unverified source-linked claim'
        return result

    def integrate(self,event_id,scope,exclusive=False):
        scope=bounded(scope,'Scope',120)
        text=self.memory.original(event_id).decode('utf-8')
        if self.db.execute('SELECT status FROM texts WHERE event_id=?',(event_id,)).fetchone()[0]!='utf8-extracted':
            raise ValueError('No supported text representation; original remains stored.')
        proposals=[];offset=0;skipped=0
        for physical in text.splitlines(keepends=True):
            line=physical.rstrip('\r\n')
            if line.strip():
                parts=line.split('|')
                if len(parts)==3 and all(part.strip() for part in parts):
                    proposals.append(ClaimDraft(event_id,offset,offset+len(line),*map(str.strip,parts),scope,exclusive=exclusive))
                    if len(proposals)>100:raise ValueError('Extraction exceeds 100 claims; original retained.')
                else:skipped+=1
            offset+=len(physical)
        identities=[]
        self.db.execute('BEGIN IMMEDIATE')
        try:
            for proposal in proposals:identities.append(self._insert(proposal,text,'deterministic pipe-v1; unverified'))
            status=('partial' if skipped else 'extracted-unverified') if identities else 'no-supported-claims'
            detail={'claim_ids':identities,'unsupported_lines':skipped,'original_retained':True}
            self.db.execute('INSERT INTO extraction_runs VALUES (?,?,?,?,?,?,?)',
                (uuid4().hex,event_id,'pipe-v1',scope,status,canonical(detail),now()))
            self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                (now(),'extraction',canonical({'event_id':event_id,'status':status,'claims':len(identities)})))
            self.db.commit()
        except Exception:self.db.rollback();raise
        return {'status':status,**detail}

    def contradictions(self,limit=20):
        if type(limit) is not int or not 1<=limit<=50:raise ValueError('Conflict limit must be 1-50.')
        groups=self.db.execute('SELECT subject_id,predicate,scope,unit,count(*) AS claims,count(DISTINCT value_key) AS values_count '
            'FROM claims WHERE exclusive=1 GROUP BY subject_id,predicate,scope,unit '
            'HAVING count(DISTINCT value_key)>1 ORDER BY subject_id,predicate,scope,unit LIMIT ?',(limit,)).fetchall()
        results=[]
        for group in groups:
            item=dict(group)
            ids=self.db.execute('SELECT id FROM claims WHERE subject_id=? AND predicate=? AND scope=? AND unit=? AND exclusive=1 '
                'ORDER BY created,id LIMIT 20',tuple(group[:4])).fetchall()
            item['evidence']=[self.claim(row[0]) for row in ids]
            item['truncated']=item['claims']>20
            item['status']='potential scoped disagreement; not independent truth determination'
            results.append(item)
        return results

    def entity(self,name,limit=30):
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('Entity result limit must be 1-100.')
        row=self.db.execute('SELECT * FROM entities WHERE normalized=?',(normalized(bounded(name,'Entity',1000)),)).fetchone()
        if row is None:return None
        claims=self.db.execute('SELECT id FROM claims WHERE subject_id=? OR object_id=? ORDER BY created,id LIMIT ?',
                              (row['id'],row['id'],limit)).fetchall()
        return {**dict(row),'claims':[self.claim(item[0]) for item in claims]}

    def relationships(self,entity_name,limit=30):
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('Relationship limit must be 1-100.')
        rows=self.db.execute('SELECT c.id FROM claims c JOIN entities e ON e.id=c.subject_id '
            'WHERE e.normalized=? AND c.kind=? ORDER BY c.created,c.id LIMIT ?',
            (normalized(entity_name),'relationship',limit)).fetchall()
        return [self.claim(row[0]) for row in rows]

    def assess(self,claim_id,state,confidence,reason,evidence=()):
        self.claim(claim_id)
        if state not in ('unverified','hypothesis','supported','disputed','superseded'):
            raise ValueError('Assessment state not supported; no automatic verified-fact flag.')
        if type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<=confidence<=1:
            raise ValueError('Confidence must be a finite 0-1 assessment, not calibrated proof.')
        reason=bounded(reason,'Assessment reason',2000)
        if not isinstance(evidence,(tuple,list)) or len(evidence)>20:raise ValueError('At most 20 evidence references.')
        for identity in evidence:self.claim(identity)
        identity=uuid4().hex
        self.db.execute('BEGIN IMMEDIATE')
        try:
            previous=self.db.execute('SELECT id FROM assessments WHERE claim_id=? ORDER BY rowid DESC LIMIT 1',(claim_id,)).fetchone()
            self.db.execute('INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?)',
                (identity,claim_id,previous[0] if previous else None,state,confidence,reason,'explicit user assessment',now()))
            for reference in set(evidence):self.db.execute('INSERT INTO assessment_evidence VALUES (?,?)',(identity,reference))
            self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                (now(),'assessment',canonical({'claim_id':claim_id,'assessment_id':identity})))
            self.db.commit()
        except Exception:self.db.rollback();raise
        return dict(self.db.execute('SELECT * FROM assessments WHERE id=?',(identity,)).fetchone())

    def override(self,claim_id,value,scope,reason,*,approved=False):
        if approved is not True:raise PermissionError('Explicit user authorization required for an override.')
        claim=self.claim(claim_id)
        if scope!=claim['scope']:raise ValueError('Override must match the explicitly selected claim scope.')
        value=bounded(value,'Operating conclusion');reason=bounded(reason,'Override reason',2000)
        identity=uuid4().hex
        self.db.execute('BEGIN IMMEDIATE')
        try:
            previous=self.db.execute('SELECT id FROM assessments WHERE claim_id=? ORDER BY rowid DESC LIMIT 1',(claim_id,)).fetchone()
            previous_override=self.db.execute('SELECT id FROM overrides WHERE claim_id=? AND scope=? ORDER BY rowid DESC LIMIT 1',
                (claim_id,scope)).fetchone()
            self.db.execute('INSERT INTO overrides VALUES (?,?,?,?,?,?,?,?,?)',
                (identity,claim_id,scope,value,reason,previous[0] if previous else None,
                 previous_override[0] if previous_override else None,'explicit user override; not established fact',now()))
            self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                (now(),'override',canonical({'claim_id':claim_id,'override_id':identity,'scope':scope})))
            self.db.commit()
        except Exception:self.db.rollback();raise
        return self.effective(claim_id,scope)

    def effective(self,claim_id,scope):
        claim=self.claim(claim_id)
        if scope!=claim['scope']:
            return {'evidence':claim,'assessment':None,'override':None,'operating_conclusion':None,'conclusion_kind':'outside requested scope'}
        assessment=self.db.execute('SELECT * FROM assessments WHERE claim_id=? ORDER BY rowid DESC LIMIT 1',(claim_id,)).fetchone()
        override=self.db.execute('SELECT * FROM overrides WHERE claim_id=? AND scope=? ORDER BY rowid DESC LIMIT 1',
            (claim_id,scope)).fetchone()
        return {'evidence':claim,'assessment':dict(assessment) if assessment else None,
                'override':dict(override) if override else None,
                'operating_conclusion':override['value'] if override else claim['value'],
                'conclusion_kind':'user-authorized assumption' if override else 'unverified source statement'}


def learn(memory,submission,scope,exclusive=False):
    event=memory.ingest(submission)  # Preserve original before optional extraction.
    try:
        knowledge=Knowledge(memory).integrate(event['event_id'],scope,exclusive)
        return {'original_committed':True,'event':event,'knowledge':knowledge}
    except (ValueError,UnicodeError,TypeError,RuntimeError,OSError,sqlite3.Error) as error:
        detail={'event_id':event['event_id'],'error':str(error)[:1000]}
        try:
            memory.db.execute('INSERT INTO extraction_runs VALUES (?,?,?,?,?,?,?)',
                (uuid4().hex,event['event_id'],'pipe-v1',str(scope)[:120],'failed-original-retained',canonical(detail),now()))
            detail['failure_audit_recorded']=True
        except sqlite3.Error:
            detail['failure_audit_recorded']=False
        return {'original_committed':True,'event':event,'knowledge':{'status':'failed-original-retained',**detail}}
