"""Qualified interpretations over existing claims; bounded joins, never graph truth.

No second entity/graph store, learned embeddings, model commands or source rewrite.
A reviewed annotation means reviewed interpretation, not an established fact.
"""
from dataclasses import dataclass
from datetime import date
import hashlib,json,re,time
from vector_core.coordination import write_operation
from vector_core.knowledge import Knowledge,normalized
from vector_core.memory import canonical,now
from vector_core.projects import append,identity,latest,text

CONTRACT='semantic_claims'
EPISTEMIC={'source-assertion','observation-report','owner-assertion','untested-hypothesis','unverified-interpretation'}
FIELDS={'claim_id','sense','object_sense','aliases','object_aliases','predicate_aliases','polarity','conditions','valid_from','valid_until','epistemic','status','reason','updated'}

def label(value):return normalized(text(value,200))
def conditions(value):
    if not isinstance(value,dict) or len(value)>8:raise ValueError('At most eight explicit conditions.')
    for k,v in value.items():text(k,80);text(v,160)
    return value

def day(value):
    if value is not None:
        if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError('Explicit ISO calendar date required.')
        date.fromisoformat(value)
    return value

def validate_record(db,key,p):
    if not isinstance(p,dict) or set(p)!=FIELDS or identity(p['claim_id'])!=key:raise ValueError('Invalid semantic annotation fields.')
    claim=db.execute('SELECT kind,object_id FROM claims WHERE id=?',(key,)).fetchone()
    if claim is None:raise ValueError('Semantic annotation lost its source claim.')
    text(p['sense'],160);text(p['reason'],1600);text(p['updated'],64)
    if claim[0]=='relationship':
        if claim[1] is None:raise ValueError('Relationship has no object entity.')
        text(p['object_sense'],160)
    elif p['object_sense'] is not None or p['object_aliases']:raise ValueError('Only relationship claims have a qualified object concept.')
    for key in ('aliases','object_aliases','predicate_aliases'):
        if not isinstance(p[key],list) or len(p[key])>8 or len({label(v) for v in p[key]})!=len(p[key]):raise ValueError('Explicit distinct bounded aliases required.')
    if p['polarity'] not in {'affirmed','negated','uncertain'} or p['epistemic'] not in EPISTEMIC or p['status'] not in {'candidate','reviewed','withdrawn'}:raise ValueError('Unknown semantic epistemic/review status.')
    conditions(p['conditions']);day(p['valid_from']);day(p['valid_until'])
    if p['valid_from'] and p['valid_until'] and p['valid_from']>p['valid_until']:raise ValueError('Inverted validity interval.')
    if len(canonical(p).encode())>12000:raise ValueError('Semantic annotation exceeds record budget.')

@dataclass(frozen=True)
class Limits:
    claims:int=256
    hops:int=2
    nodes:int=32
    def validate(self):
        if type(self.claims) is not int or not 1<=self.claims<=2048 or type(self.hops) is not int or not 0<=self.hops<=4 or type(self.nodes) is not int or not 1<=self.nodes<=128:raise ValueError('Invalid bounded semantic retrieval limits.')
        return self

class Semantics:
    def __init__(self,memory):self.memory=memory;self.db=memory.db;self.knowledge=Knowledge(memory)
    @write_operation
    def qualify(self,claim_id,spec,*,approved=False,revision=None):
        if approved is not True:raise PermissionError('Explicit approval required for semantic interpretation/review.')
        claim=self.knowledge.claim(identity(claim_id))
        if not isinstance(spec,dict) or set(spec)- (FIELDS-{'claim_id','updated'}):raise ValueError('Unknown semantic qualification.')
        p={'claim_id':claim_id,'sense':spec.get('sense'),'object_sense':spec.get('object_sense'),'aliases':spec.get('aliases',[]),'object_aliases':spec.get('object_aliases',[]),'predicate_aliases':spec.get('predicate_aliases',[]),'polarity':spec.get('polarity','uncertain'),'conditions':spec.get('conditions',{}),'valid_from':spec.get('valid_from'),'valid_until':spec.get('valid_until'),'epistemic':spec.get('epistemic','unverified-interpretation'),'status':spec.get('status','candidate'),'reason':spec.get('reason','Explicit pending interpretation; not a fact.'),'updated':now()}
        validate_record(self.db,claim_id,p)
        from vector_core.persistence import register
        if not self.db.execute('SELECT 1 FROM persistence_contracts WHERE name=?',(CONTRACT,)).fetchone():register(self.memory,CONTRACT,'Qualified, versioned interpretations of existing source-linked claims; never established facts')
        old=self.db.execute('SELECT id,payload FROM persistent_records WHERE contract=? AND record_key=? ORDER BY rowid DESC LIMIT 1',(CONTRACT,claim_id)).fetchone()
        if old:
            previous=json.loads(old['payload'])
            if revision is not None and revision!=old['id']:raise ValueError('Semantic interpretation changed; reload.')
            if {k:v for k,v in p.items() if k!='updated'}=={k:v for k,v in previous.items() if k!='updated'}:return {**previous,'revision':old['id'],'already_present':True}
        return append(self.memory,CONTRACT,claim_id,p,expected=revision or (old['id'] if old else None),new=not bool(old))
    def get(self,claim_id):
        p=latest(self.memory,CONTRACT,identity(claim_id));validate_record(self.db,claim_id,{k:v for k,v in p.items() if k!='revision'});return {**p,'claim':self.knowledge.claim(claim_id)}
    def catalog(self,*,after=0,limit=256):
        if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=2048:raise ValueError('Invalid semantic catalog slice.')
        rows=self.db.execute("SELECT id,rowid,payload FROM persistent_records r WHERE contract=? AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key) ORDER BY rowid LIMIT ?",(CONTRACT,after,limit+1)).fetchall()
        items=[]
        for row in rows[:limit]:
            p=json.loads(row['payload']);validate_record(self.db,p['claim_id'],p)
            if p['status']!='withdrawn':items.append({**p,'revision':row['id'],'claim':self.knowledge.claim(p['claim_id'])})
        return {'items':items,'truncated':len(rows)>limit,'next_cursor':rows[min(limit,len(rows))-1]['rowid'] if rows else after}
    def snapshot(self,annotation_ids,limit=256):
        if not isinstance(annotation_ids,list) or len(annotation_ids)>limit or len(set(annotation_ids))!=len(annotation_ids):raise ValueError('Invalid bounded semantic snapshot references.')
        items=[]
        for record_id in annotation_ids:
            row=self.db.execute('SELECT record_key,payload FROM persistent_records WHERE id=? AND contract=?',(identity(record_id),CONTRACT)).fetchone()
            if row is None:raise ValueError('Missing historical semantic qualification.')
            p=json.loads(row['payload']);validate_record(self.db,row['record_key'],p)
            items.append({**p,'revision':record_id,'claim':self.knowledge.claim(p['claim_id'])})
        return {'items':items,'truncated':False,'next_cursor':0}
    def citation(self,item):
        c=item['claim'];event=self.memory.event(c['event_id'])
        result={'event_id':c['event_id'],'source_id':event['source_id'],'sha256':event['sha256'],'start':c['start_char'],'end':c['end_char'],'quote':c['quote'],'name':event['submission_name'],'occurred':event['occurred']}
        if event['metadata'].get('resource_type')=='scientific-extracted-text':
            from vector_core.science import provenance
            result['scientific_provenance']=provenance(self.memory,c['event_id'])
        return result
    @staticmethod
    def names(item,object=False):
        c=item['claim'];return [label(c['value'] if object else c['subject']),*(label(v) for v in item['object_aliases' if object else 'aliases'])]
    @staticmethod
    def applicable(item,selector):
        c=item['claim']
        if item['status']!='reviewed':return False,'Interpretation has not been reviewed.'
        if c['scope']!=selector['scope']:return False,'Source scope differs.'
        if any(selector['conditions'].get(k)!=v for k,v in item['conditions'].items()):return False,'Required source conditions are missing or different.'
        if item['valid_from'] or item['valid_until']:
            if selector['at'] is None:return False,'An explicit date is required for temporally qualified evidence.'
            if (item['valid_from'] and selector['at']<item['valid_from']) or (item['valid_until'] and selector['at']>item['valid_until']):return False,'Source validity interval differs.'
        return True,''
    def lookup(self,selector,*,limits=None,annotation_ids=None):
        limits=(limits or Limits()).validate();selector=validate_selector(selector)
        if len(selector['path'])>limits.hops:raise ValueError('Explicit path exceeds this request hop budget.')
        catalog=self.catalog(limit=limits.claims) if annotation_ids is None else self.snapshot(annotation_ids,limits.claims);items=catalog['items'];paths=[];blocked=[];disputed_edges=[]
        nodes={(x['claim']['subject_id'],x['sense']):[] for x in items if selector['subject'] in self.names(x) and x['sense']==selector['sense']}
        nodes.update({(x['claim']['object_id'],x['object_sense']):[] for x in items if x['claim']['kind']=='relationship' and selector['subject'] in self.names(x,object=True) and x['object_sense']==selector['sense']})
        if len(nodes)>limits.nodes:raise ValueError('Too many semantic seed nodes; refine the selector.')
        for predicate in selector['path']:
            following={}
            groups={}
            for x in items:
                c=x['claim'];node=(c['subject_id'],x['sense'])
                if node in nodes and c['kind']=='relationship' and label(predicate) in [label(c['predicate']),*(label(v) for v in x['predicate_aliases'])] and self.applicable(x,selector)[0]:groups.setdefault(node,[]).append(x)
            disputed_nodes={node for node,claims in groups.items() if disagrees(claims)}
            for node in disputed_nodes:disputed_edges.extend(nodes[node]+groups[node])
            for x in items:
                c=x['claim'];node=(c['subject_id'],x['sense']);ok,why=self.applicable(x,selector)
                if node not in nodes or c['kind']!='relationship' or label(predicate) not in [label(c['predicate']),*(label(v) for v in x['predicate_aliases'])]:continue
                if node in disputed_nodes:continue
                if not ok or x['polarity']!='affirmed':blocked.append(why or 'Negated/uncertain relationship is not a positive join.');continue
                target=(c['object_id'],x['object_sense']);trail={v['claim_id']:v for v in following.get(target,[])+nodes[node]+[x]};following[target]=list(trail.values())
                if len(following)>limits.nodes:raise ValueError('Semantic path exceeds node budget.')
            nodes=following
        selected=[]
        for x in items:
            c=x['claim'];node=(c['subject_id'],x['sense'])
            if node not in nodes or selector['predicate'] not in [label(c['predicate']),*(label(v) for v in x['predicate_aliases'])]:continue
            ok,why=self.applicable(x,selector)
            if ok:selected.append(x);paths.extend(nodes[node])
            else:blocked.append(why)
        paths=list({x['claim_id']:x for x in paths}.values());relevant=list({x['claim_id']:x for x in paths+selected+disputed_edges}.values())
        status='source-supported';warnings=list(dict.fromkeys(blocked))
        if catalog['truncated']:warnings.append('Semantic catalog slice is incomplete; no exhaustive conclusion.');status='insufficient'
        if not selected:status='insufficient';warnings.append('No matching reviewed claim for all requested qualifications.')
        if any(x['polarity']=='uncertain' for x in selected):status='insufficient';warnings.append('Uncertain polarity cannot support a definite answer.')
        if any(x['epistemic'] in {'untested-hypothesis','unverified-interpretation'} for x in relevant):status='hypothetical'
        elif any(x['epistemic']=='owner-assertion' for x in relevant):status='owner-assertion'
        groups={}
        for x in selected:groups.setdefault((x['claim']['subject_id'],x['sense']),[]).append(x)
        if disputed_edges or any(disagrees(claims) for claims in groups.values()):status='disputed';warnings.append('Comparable source assertions conflict, including any disputed relationship step; neither was discarded.')
        if paths and status=='source-supported':status='inferred'
        return {'status':status,'selector':selector,'values':[{'value':x['claim']['value'],'unit':x['claim']['unit'],'polarity':x['polarity'],'claim_id':x['claim_id'],'annotation_id':x['revision'],'epistemic':x['epistemic']} for x in selected],'claim_ids':[x['claim_id'] for x in relevant],'annotation_ids':[x['revision'] for x in relevant],'citations':[self.citation(x) for x in relevant],'connections':[{'claim_id':x['claim_id'],'predicate':x['claim']['predicate'],'status':'reviewed source relationship used for a join; association is not causal proof'} for x in paths],'qualifications':warnings,'epistemic_status':'Source-linked interpretations and bounded joins; source truth and general entailment are not independently established.'}
    def calculate(self,operation,parameters,bindings):
        from vector_core.tools import compute,number,unit
        if operation!='arithmetic' or not isinstance(parameters,dict) or set(parameters)-{'expression','variables','target_unit'}:raise ValueError('Source bindings support existing arithmetic quantities only.')
        if not isinstance(bindings,dict) or not 1<=len(bindings)<=16:raise ValueError('Select 1–16 source quantity bindings.')
        variables=dict(parameters.get('variables',{}));premises={};citations={};problems=[];status='insufficient'
        for name,selector in bindings.items():
            if name in variables:raise ValueError('Source binding cannot replace an explicit variable.')
            if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}',name):raise ValueError('Invalid source quantity variable.')
            found=self.lookup(selector);premises[name]=found
            for cite in found['citations']:citations[(cite['event_id'],cite['start'],cite['end'])]=cite
            if found['status']=='disputed':status='disputed'
            if found['status'] not in {'source-supported','inferred'} or not found['values'] or any(v['polarity']!='affirmed' for v in found['values']):problems.append('Unresolved source quantity: '+name);continue
            keys={value_key(self.get(v['claim_id'])) for v in found['values']}
            if len(keys)!=1:problems.append('Multiple quantities remain for '+name);continue
            spec=found['values'][0]
            try:number(spec['value']);unit(spec['unit'] or '1')
            except ValueError:problems.append('Source quantity/unit is not supported: '+name);continue
            variables[name]={'value':spec['value'],'unit':spec['unit'] or '1'}
            for cite in found['citations']:citations[(cite['event_id'],cite['start'],cite['end'])]=cite
        if problems:return {'kind':'grounded-calculation','status':status,'premises':premises,'citations':list(citations.values()),'qualifications':problems,'epistemic_status':'Calculation withheld for unresolved premises; hypotheses remain available for investigation.'}
        args={'expression':parameters['expression'],'variables':variables};result=compute('arithmetic',args)
        if 'target_unit' in parameters:
            destination=unit(parameters['target_unit'])
            if list(destination.dimensions)!=result['si_dimensions']:raise ValueError('Requested result unit is dimensionally inconsistent.')
            from decimal import localcontext
            with localcontext() as context:
                context.prec=40;result.update(value=str(number(number(result['value'])/destination.value)),unit=parameters['target_unit'])
        return {'kind':'grounded-calculation','status':'tool-verified','tool':'arithmetic','parameters':args,'result':result,'value':result['value'],'answer':result['value'],'premises':premises,'citations':list(citations.values()),'qualifications':['Verified computation over source assertions, not verified empirical premises.'],'epistemic_status':'tool-verified for the stated source premises; model output supplied neither values nor authority'}

def validate_selector(p):
    if not isinstance(p,dict) or set(p)-{'subject','sense','predicate','scope','conditions','at','path'} or not {'subject','sense','predicate','scope'}<=set(p):raise ValueError('Explicit subject, sense, predicate and scope selector required.')
    result={'subject':label(p['subject']),'sense':text(p['sense'],160),'predicate':label(p['predicate']),'scope':text(p['scope'],120),'conditions':conditions(p.get('conditions',{})),'at':day(p.get('at')),'path':p.get('path',[])}
    if not isinstance(result['path'],list) or len(result['path'])>4:raise ValueError('At most four explicit relationship joins per request.')
    for value in result['path']:text(value,120)
    return result

def value_key(item):
    from vector_core.tools import quantity
    c=item['claim']
    try:
        q=quantity(c['value'],c['unit'] or '1');value=('quantity',str(q.value.normalize()),q.dimensions)
    except ValueError:value=('literal',normalized(c['value']),item['object_sense'])
    return (value,item['polarity'])

def disagrees(items):
    keys=[value_key(x) for x in items]
    return (any(x['claim']['exclusive'] for x in items) and len(set(keys))>1) or any(a[0]==b[0] and a[1]!=b[1] for a in keys for b in keys)

def reason(memory,request):
    if not isinstance(request,dict) or request.get('kind') not in {'lookup','calculate'}:raise ValueError('Explicit grounded lookup/calculation request required.')
    semantic=Semantics(memory)
    if request['kind']=='lookup':
        if set(request)!={'kind','selector'}:raise ValueError('Unknown grounded lookup input.')
        result=semantic.lookup(request['selector']);result.update(kind='grounded-lookup',answer=lookup_answer(result))
        return result
    if set(request)!={'kind','operation','parameters','bindings'}:raise ValueError('Unknown grounded calculation input.')
    return semantic.calculate(request['operation'],request['parameters'],request['bindings'])

def lookup_answer(result):
    answer='; '.join(('not ' if v['polarity']=='negated' else '')+v['value']+(' '+v['unit'] if v['unit'] else '') for v in result['values']) if result['status'] not in {'disputed','insufficient'} else ''
    return ('Terminal source after the requested relationship joins reports: '+answer) if answer and result['selector']['path'] else answer

def evidence(memory,question,*,selector=None,limits=None,project_id=None,project_only=False,investigation_id=None):
    """Full reviewable package; associations are retrieval paths, never proof."""
    text(question,2000);limits=(limits or Limits()).validate();sem=Semantics(memory);catalog=sem.catalog(limit=limits.claims);items=catalog['items'];warnings=[]
    if project_only and not project_id:raise ValueError('Project-only semantic evidence needs a project.')
    if project_id:
        from vector_core.projects import Projects
        Projects(memory).get(project_id)
    def in_project(item):return not project_only or memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='project_sources' AND record_key=?",(project_id+':'+item['claim']['event_id'],)).fetchone() is not None
    items=[x for x in items if in_project(x)]
    if selector:
        chosen=validate_selector(selector);seeds={(x['claim']['subject_id'],x['sense']) for x in items if chosen['subject'] in sem.names(x) and x['sense']==chosen['sense']}
        seeds.update({(x['claim']['object_id'],x['object_sense']) for x in items if x['claim']['kind']=='relationship' and chosen['subject'] in sem.names(x,object=True) and x['object_sense']==chosen['sense']})
    else:
        def mentioned(name):return re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',question) is not None
        seeds={(x['claim']['subject_id'],x['sense']) for x in items if any(mentioned(n) for n in sem.names(x))}
        seeds.update({(x['claim']['object_id'],x['object_sense']) for x in items if x['claim']['kind']=='relationship' and any(mentioned(n) for n in sem.names(x,object=True))})
    if len(seeds)>limits.nodes:raise ValueError('Too many matching concepts; specify sense/selector.')
    # A label shared by senses is reported, never merged into an equivalent node.
    ambiguities={}
    for x in items:
        if (x['claim']['subject_id'],x['sense']) in seeds:ambiguities.setdefault(x['claim']['subject'],set()).add(x['sense'])
    ambiguous=[{'label':name,'senses':sorted(senses)} for name,senses in ambiguities.items() if len(senses)>1]
    if ambiguous:warnings.append('Ambiguous concept senses remain separate; select a sense for a definite lookup.')
    visited=set(seeds);selected={};connections=[];frontier=seeds
    for depth in range(limits.hops+1):
        following=set()
        for x in items:
            c=x['claim'];left=(c['subject_id'],x['sense']);right=(c['object_id'],x['object_sense']) if c['kind']=='relationship' else None
            if left not in frontier and right not in frontier:continue
            selected[x['claim_id']]=x
            if right and x['status']=='reviewed' and depth<limits.hops:
                connections.append({'claim_id':x['claim_id'],'left':{'entity_id':left[0],'sense':left[1]},'right':{'entity_id':right[0],'sense':right[1]},'predicate':c['predicate'],'polarity':x['polarity'],'status':'source relationship used for retrieval only; association is not proof'})
                following.update((left,right))
        following-=visited
        if len(visited|following)>limits.nodes:warnings.append('Node budget reached; refine or resume a narrower request.');break
        visited|=following;frontier=following
        if not frontier:break
    if selector:
        selection=sem.lookup(selector,limits=limits);warnings.extend(selection['qualifications'])
        if selection['claim_ids']:
            selected={k:v for k,v in selected.items() if k in set(selection['claim_ids'])};connections=[c for c in connections if c['claim_id'] in selected]
    assertions=[];sources={};groups={}
    for x in selected.values():
        c=x['claim'];cite=sem.citation(x);sources[(cite['event_id'],cite['start'],cite['end'])]=cite
        effective=sem.knowledge.effective(c['id'],c['scope'])
        assertions.append({'claim_id':c['id'],'subject':c['subject'],'predicate':c['predicate'],'value':c['value'],'unit':c['unit'],'kind':c['kind'],'scope':c['scope'],'sense':x['sense'],'object_sense':x['object_sense'],'conditions':x['conditions'],'valid_from':x['valid_from'],'valid_until':x['valid_until'],'polarity':x['polarity'],'epistemic':x['epistemic'],'review':x['status'],'citation':cite,'owner_assumption':effective['override'],'assessment':effective['assessment']})
        # Only exactly comparable contexts/intervals are grouped automatically.
        group=(c['subject_id'],x['sense'],c['predicate'],c['scope'],canonical(x['conditions']),x['valid_from'],x['valid_until'])
        groups.setdefault(group,[]).append(x)
    conflicts=[]
    for group,claims in groups.items():
        if disagrees(claims):
            conflicts.append({'subject':claims[0]['claim']['subject'],'predicate':group[2],'scope':group[3],'claim_ids':[x['claim_id'] for x in claims],'status':'disputed source assertions; no winner selected'})
    if catalog['truncated']:warnings.append('Catalog slice incomplete; absence of a match is not a corpus-wide proof.')
    if not assertions:warnings.append('No reviewed/annotated semantic connection found; direct passage retrieval remains available.')
    if any(x['status']!='reviewed' for x in selected.values()):warnings.append('Pending interpretations are included as unverified candidates, not trusted calculation premises.')
    memories=[]
    if investigation_id:
        from vector_core.investigation import Investigations
        inv=Investigations(memory);state=inv.get(investigation_id)
        if project_only and state['project_id']!=project_id:raise ValueError('Investigation is outside the selected project.')
        results,_=inv._results(investigation_id)
        for step,result in results.items():
            if result.get('kind')=='deterministic-computation':
                from vector_core.tools import compute
                expected=compute(result['tool'],result['parameters'])
                if any(result.get(k)!=v for k,v in expected.items()):raise ValueError('Historical tool observation no longer reproduces.')
                memories.append({'step':step,'kind':result['kind'],'status':'tool-verified','answer':expected.get('value',expected.get('x',canonical(expected))),'citations':[],'historical':True,'simulated':result.get('simulated',False),'epistemic_status':'Reproduced pure calculation for explicitly supplied historical premises; not empirical truth.'})
            elif result.get('status') in {'tool-verified','source-supported','inferred','disputed','insufficient','hypothetical','owner-assertion'}:
                validate_result(memory,result)
                references=result.get('annotation_ids',[])+[ref for p in result.get('premises',{}).values() for ref in p['annotation_ids']]
                changed=False
                for item in sem.snapshot(list(dict.fromkeys(references)))['items']:
                    if sem.get(item['claim_id'])['revision']!=item['revision']:changed=True
                memories.append({'step':step,'kind':result.get('kind'),'status':result['status'],'answer':result.get('answer',''),'citations':result.get('citations',[]),'historical':True,'current_annotations_changed':changed,'simulated':result.get('simulated',False),'epistemic_status':'Historical observation; changed premises require a new grounded query. '+result.get('epistemic_status','Unverified investigation observation')})
        if len(memories)>8:warnings.append('Only the most recent eight relevant current-plan observations included.')
    return {'format':'vector-semantic-evidence-v1','question':question,'sources':list(sources.values()),'assertions':assertions,'connections':list({x['claim_id']:x for x in connections}.values()),'conflicts':conflicts,'ambiguities':ambiguous,'qualifications':list(dict.fromkeys(warnings)),'investigation_memory':memories[-8:],'catalog_truncated':catalog['truncated'],'next_catalog_cursor':catalog['next_cursor'],'epistemic_status':'Retrieved source assertions and interpreted relationships, not inferred facts or causal proof.'}

def build_context(memory,question,*,budget_bytes=8192,limit=8,scope=None,project_id=None,conversation_id=None,project_only=False,selector=None,investigation_id=None):
    """Project whole qualified sources first; never clip conditions or dissent."""
    from vector_core.context import build_context as direct
    started=time.perf_counter()
    if type(project_only) is not bool:raise ValueError('Project-only flag must be boolean.')
    package=evidence(memory,question,selector=selector,project_id=project_id,project_only=project_only,investigation_id=investigation_id)
    # Fully specified source queries need not search 1.2M unrelated literary
    # passages first. All matching qualified alternatives remain in the package.
    # Unknown/general queries retain the independent full-text baseline/fallback.
    matching=Semantics(memory).lookup(selector)['claim_ids'] if selector else []
    qualified=bool(matching and set(matching)<={a['claim_id'] for a in package['assertions']} and not package['catalog_truncated'])
    if qualified:
        # Keep the same public input validation even when no FTS work is needed.
        if type(budget_bytes) is not int or not 128<=budget_bytes<=131072 or type(limit) is not int or not 1<=limit<=20:raise ValueError('Invalid context/source budget.')
        package['qualifications'].append('Qualified source selection used; unannotated full text was not searched. Independent passage retrieval remains available; no corpus-wide truth or absence claim.')
        base={'context':{'question':question,'sources':[],'claims':[],'scope':scope,'conflicts':[],'truncated':False,'policy':'Untrusted source assertions; overrides are user assumptions.'},'display_notices':[]}
    else:base=direct(memory,question,budget_bytes=budget_bytes,limit=limit,scope=scope,project_id=project_id,conversation_id=conversation_id,project_only=project_only,semantic=False)
    ctx=base['context'];old_sources=ctx['sources'];old_claims=ctx['claims'];old_conflicts=ctx['conflicts']
    ctx.update(sources=[],claims=[],conflicts=[])
    semantic={'format':package['format'],'assertions':[],'connections':[],'conflicts':[],'ambiguities':package['ambiguities'],'qualifications':package['qualifications'],'investigation_memory':[],'status':'Source interpretations and associations, not independent conclusions.'}
    ctx['semantic']=semantic
    if len(canonical(ctx).encode())>budget_bytes:raise ValueError('Semantic qualifications exceed the model context budget; narrow the question or increase its budget.')
    groups={};claim_events={}
    for a in package['assertions']:
        event_id=a['citation']['event_id'];groups.setdefault(event_id,[]).append(a);claim_events[a['claim_id']]=event_id
    bundles=[{event_id} for event_id in groups]
    # Comparable disagreement is one atomic model-context bundle. A small window
    # cannot accidentally select just the convenient side of a known conflict.
    for conflict in package['conflicts']:
        merged={claim_events[c] for c in conflict['claim_ids']};remaining=[]
        for bundle in bundles:
            if bundle&merged:merged|=bundle
            else:remaining.append(bundle)
        bundles=remaining+[merged]
    omitted=0
    for bundle in bundles:
        new_sources=[];new_assertions=[];invalid=False
        for event_id in sorted(bundle):
            items=groups[event_id];cite=items[0]['citation'];left=min(a['citation']['start'] for a in items);right=max(a['citation']['end'] for a in items)
            if right-left>4000:invalid=True;break
            source={**cite,'start':left,'end':right,'quote':memory.read_text_span(event_id,left,right)}
            new_sources.append(source)
            for item in items:
                projected={k:v for k,v in item.items() if k!='citation'}
                projected['citation']={k:item['citation'][k] for k in ('event_id','sha256','start','end')}
                new_assertions.append(projected)
        old_count=len(ctx['sources']);old_assertions=len(semantic['assertions'])
        ctx['sources'].extend(new_sources);semantic['assertions'].extend(new_assertions)
        if invalid or len(ctx['sources'])>limit or len(canonical(ctx).encode())>budget_bytes:
            del ctx['sources'][old_count:];del semantic['assertions'][old_assertions:];omitted+=sum(len(groups[e]) for e in bundle)
    included={a['claim_id'] for a in semantic['assertions']}
    for category in ('connections','conflicts','investigation_memory'):
        for item in package[category]:
            refs={item['claim_id']} if 'claim_id' in item else set(item.get('claim_ids',[]))
            if refs and not refs<=included:continue
            allowed={s['event_id']:s for s in ctx['sources']}
            if any(c['event_id'] not in allowed or not allowed[c['event_id']]['start']<=c['start']<c['end']<=allowed[c['event_id']]['end'] for c in item.get('citations',[])):continue
            semantic[category].append(item)
            if len(canonical(ctx).encode())>budget_bytes:semantic[category].pop();omitted+=1
    # Independent passage fallback survives for unannotated sources. Annotated
    # assertions omitted atomically above cannot leak back as unqualified snippets.
    selected={s['event_id'] for s in ctx['sources']}
    for source in old_sources:
        if source['event_id'] in selected or source['event_id'] in groups:continue
        if len(ctx['sources'])>=limit:omitted+=1;continue
        ctx['sources'].append(source)
        if len(canonical(ctx).encode())>budget_bytes:ctx['sources'].pop();omitted+=1
        else:selected.add(source['event_id'])
    for claim in old_claims:
        if claim['claim_id'] in claim_events or claim['event_id'] not in selected:continue
        ctx['claims'].append(claim)
        if len(canonical(ctx).encode())>budget_bytes:ctx['claims'].pop();omitted+=1
    legacy_ids={c['claim_id'] for c in ctx['claims']}
    for conflict in old_conflicts:
        if not set(conflict['claim_ids'])<=legacy_ids:continue
        ctx['conflicts'].append(conflict)
        if len(canonical(ctx).encode())>budget_bytes:ctx['conflicts'].pop();omitted+=1
    if omitted:
        ctx['truncated']=True
        semantic['status']='Some qualified evidence omitted; no exhaustive conclusion.'
    from vector_core.context import display_notices
    return {**base,'display_notices':display_notices(memory,[s['event_id'] for s in ctx['sources']]),'context':ctx,'bytes':len(canonical(ctx).encode()),'sha256':hashlib.sha256(canonical(ctx).encode()).hexdigest(),'seconds':time.perf_counter()-started,'ranking':'Qualified source bundles and explicit relationships, with independent passage fallback; no embeddings','semantic_omissions':omitted}

def validate_result(memory,result):
    """Recheck grounded observations on restore/use; an imported label is no proof."""
    from vector_core.tools import compute,number,unit
    if result.get('kind') not in {'grounded-lookup','grounded-calculation'}:return
    sem=Semantics(memory)
    for cite in result.get('citations',[]):
        event=memory.event(cite['event_id'])
        if cite['sha256']!=event['sha256'] or memory.read_text_span(cite['event_id'],cite['start'],cite['end'])!=cite['quote']:raise ValueError('Grounded observation citation differs from original.')
    def lookup(p):
        replay=sem.lookup(p['selector'],annotation_ids=p['annotation_ids'])
        for field in ('values','claim_ids','citations','connections'):
            if sorted(map(canonical,replay[field]))!=sorted(map(canonical,p[field])):raise ValueError('Grounded lookup differs from its pinned source interpretations.')
        # A catalog slice may conservatively withhold a conclusion; replaying its
        # pinned subset cannot establish that the original catalog was complete.
        conservative=p['status']=='insufficient' and any('catalog slice is incomplete' in q.lower() for q in p['qualifications'])
        if p['status']!=replay['status'] and not conservative:raise ValueError('Forged grounded lookup status.')
    if result['kind']=='grounded-lookup':
        lookup(result)
        if result['answer']!=lookup_answer(result):raise ValueError('Grounded answer differs from its source interpretations.')
        return
    if not isinstance(result.get('premises'),dict) or not 1<=len(result['premises'])<=16:raise ValueError('Grounded calculation needs explicit source premises.')
    for p in result.get('premises',{}).values():lookup(p)
    citations={canonical(c) for p in result['premises'].values() for c in p['citations']}
    if citations!={canonical(c) for c in result['citations']}:raise ValueError('Grounded calculation lost or invented source citations.')
    if result['status']!='tool-verified':
        if result['status'] not in {'insufficient','disputed'} or result.get('answer') or result.get('result'):raise ValueError('Unresolved calculation cannot assert a verified answer.')
        return
    if result.get('tool')!='arithmetic':raise ValueError('Unknown grounded verification tool.')
    for name,p in result['premises'].items():
        if p['status'] not in {'source-supported','inferred'} or not p['values']:raise ValueError('Unresolved grounded calculation premise.')
        v=p['values'][0];actual=result['parameters']['variables'][name]
        if actual!={'value':v['value'],'unit':v['unit'] or '1'} or any(x['polarity']!='affirmed' for x in p['values']):raise ValueError('Calculation variables differ from source bindings.')
    expected=compute('arithmetic',result['parameters']);stored=result['result'];value=number(stored['value'])
    if 'unit' in stored:
        destination=unit(stored['unit'])
        if list(destination.dimensions)!=expected['si_dimensions']:raise ValueError('Grounded result dimensions changed.')
        from decimal import localcontext
        with localcontext() as context:
            context.prec=40;expected_value=number(expected['value'])/destination.value
    else:expected_value=number(expected['value'])
    if value!=expected_value or stored['si_dimensions']!=expected['si_dimensions'] or number(result['answer'])!=number(stored['value']) or number(result['value'])!=number(stored['value']):raise ValueError('Grounded calculation does not reproduce under the verified tool.')

def model_observation(memory,result):
    """Project verified records without duplicating source text in model prompts.

    Full records remain durable. All epistemic/applicability qualifications stay;
    exact citation text must come from the independent supplied source context.
    """
    validate_result(memory,result)
    projected={k:result[k] for k in ('kind','status','answer','qualifications','epistemic_status') if k in result}
    references=[]
    def premise(p):
        references.extend(p['annotation_ids'])
        # The answer/tool parameters already contain values; selectors retain
        # the requested joins and applicability. Pinned qualifications below
        # retain source polarity/scope without repeating the whole lookup tree.
        return {k:p[k] for k in ('status','selector','qualifications')}
    if result['kind']=='grounded-lookup':projected['source_query']=premise(result)
    else:
        projected['premises']={key:premise(p) for key,p in result['premises'].items()}
        for field in ('tool','parameters','result'):
            if field in result:projected[field]=result[field]
    sem=Semantics(memory);items=sem.snapshot(list(dict.fromkeys(references)))['items']
    projected['source_qualifications']=[{k:x[k] for k in ('claim_id','revision','sense','object_sense','polarity','conditions','valid_from','valid_until','epistemic','status')} for x in items]
    projected['current_annotations_changed']=any(sem.get(x['claim_id'])['revision']!=x['revision'] for x in items)
    projected['citations']=[{k:c[k] for k in ('event_id','sha256','start','end')} for c in result['citations']]
    projected['citation_policy']='References identify checked original spans. Copy citation quotes only from the supplied context; this projection grants no additional citation authority.'
    return projected
