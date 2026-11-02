"""Inspectable question planning over existing semantic/tool/investigation records.

Grounding is a conservative language frontend, not general entailment. Concepts,
aliases and relationships come from reviewed memory. Unknown methods and novel
objectives remain investigable; neither model text nor matching words authorize
an action. No second planner database or autonomous execution loop is created.
"""
import ast,hashlib,json,re
from uuid import uuid4
from vector_core.memory import canonical,now
from vector_core.projects import identity,text

FORMAT='vector-question-plan-v1'
LIMIT=256


def tokens(value):
    return tuple(w[:-1] if len(w)>4 and w.endswith('s') else w for w in re.findall(r'[^\W_]+',value.casefold(),re.UNICODE))


def contains(phrase,question):
    a,b=tokens(phrase),tokens(question)
    return bool(a) and any(b[i:i+len(a)]==a for i in range(len(b)-len(a)+1))


def _basis(memory,marker):
    if marker is None:return 0
    row=memory.db.execute('SELECT rowid FROM persistent_records WHERE id=?',(identity(marker),)).fetchone()
    if row is None:raise ValueError('Planning snapshot reference is missing.')
    return row[0]


def _catalog(memory,marker,after):
    from vector_core.semantic import Semantics
    cutoff=_basis(memory,marker)
    rows=memory.db.execute("SELECT id,rowid FROM persistent_records r WHERE contract='semantic_claims' AND rowid>? AND rowid<=? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key AND rowid<=?) ORDER BY rowid LIMIT ?",(after,cutoff,cutoff,LIMIT+1)).fetchall()
    items=Semantics(memory).snapshot([r['id'] for r in rows[:LIMIT]])['items']
    return [x for x in items if x['status']=='reviewed'],len(rows)>LIMIT


def _constraints(value):
    from vector_core.semantic import conditions,day
    if not isinstance(value,dict) or set(value)-{'scope','sense','conditions','at','choices','catalog_after','calculation','request'}:raise ValueError('Unsupported planning constraint; no arbitrary actions or source instructions.')
    p=dict(value)
    for k in ('scope','sense'):
        if k in p:text(p[k],160)
    if 'conditions' in p:conditions(p['conditions'])
    if 'at' in p:day(p['at'])
    if 'catalog_after' in p and (type(p['catalog_after']) is not int or p['catalog_after']<0):raise ValueError('Invalid catalog cursor.')
    if 'choices' in p:
        if not isinstance(p['choices'],dict) or len(p['choices'])>16:raise ValueError('Invalid interpretation choices.')
        for k,v in p['choices'].items():text(k,8);text(v,20)
    return p


LOOKUP_GRAMMAR=set('what which is are does do the a an of for in to on at as when and then follow report reported reports established proposed assert asserts its itself their please give tell me show use value how much'.split())


def _remaining_lookup_words(items,clause,requests):
    known=set(LOOKUP_GRAMMAR)
    from vector_core.semantic import Semantics
    for request in requests:
        selector=request['selector'];known.update(tokens(selector['subject']));known.update(tokens(selector['scope']));known.update(tokens(selector['sense']))
        for k,v in selector.get('conditions',{}).items():known.update(tokens(k));known.update(tokens(v))
        for predicate in selector['path']+[selector['predicate']]:known.update(tokens(predicate))
    for item in items:
        c=item['claim'];root=any(c['scope']==r['selector']['scope'] and item['sense']==r['selector']['sense'] and any(tokens(n)==tokens(r['selector']['subject']) for n in Semantics.names(item)) for r in requests)
        predicate=any(c['scope']==r['selector']['scope'] and c['predicate'] in r['selector']['path']+[r['selector']['predicate']] for r in requests)
        phrases=[]
        if root:phrases.extend(Semantics.names(item))
        if predicate:phrases.extend([c['predicate'],*item['predicate_aliases']])
        for phrase in phrases:known.update(tokens(phrase))
    clean=re.sub(r'\b\d{4}-\d{2}-\d{2}\b','',clause)
    return sorted(set(tokens(clean))-known)


def _request_id(request):return hashlib.sha256(canonical(request).encode()).hexdigest()[:16]


def _selectors(items,clause,whole,hints):
    """Enumerate from reviewed concepts, not a fixed topic/category dictionary."""
    from vector_core.semantic import Semantics
    roots={}
    for item in items:
        if any(contains(n,clause) for n in Semantics.names(item)):
            c=item['claim'];roots[(c['subject'],item['sense'],c['scope'])]=True
    if not roots:
        for item in items:
            if any(contains(n,whole) for n in Semantics.names(item)):
                c=item['claim'];roots[(c['subject'],item['sense'],c['scope'])]=True
    result=[];blocked=[]
    for subject,sense,scope in roots:
        if hints.get('scope',scope)!=scope or hints.get('sense',sense)!=sense:continue
        # A named scope/sense disambiguates; an absent name never licenses guessing
        # between multiple interpretations of the same mentioned concept.
        alternatives={k for k in roots if tokens(k[0])==tokens(subject)}
        if len(alternatives)>1 and not ('scope' in hints or 'sense' in hints):
            explicit=[k for k in alternatives if contains(k[1],clause) or contains(k[2],clause)]
            if explicit and (subject,sense,scope) not in explicit:continue
        frontier=[(subject,sense,[],frozenset())]
        for depth in range(5):
            following=[]
            for node,node_sense,path,seen in frontier:
                relevant=[x for x in items if x['sense']==node_sense and x['claim']['scope']==scope and any(tokens(n)==tokens(node) for n in Semantics.names(x))]
                for x in relevant:
                    c=x['claim'];pred=c['predicate'];names=[pred,*x['predicate_aliases']]
                    if any(contains(n,clause) for n in names):
                        # A join must be requested/confirmed, not assumed to be an
                        # intrinsic property of the root merely because units match.
                        if path and not all(contains(edge,clause) for edge in path):
                            blocked.append({'subject':subject,'predicate':pred,'path':path,'reason':'A component/relationship value is not automatically a property of the root.'});continue
                        query={'subject':subject,'sense':sense,'scope':scope,'predicate':pred,'path':path,'conditions':dict(hints.get('conditions',{}))}
                        available={}
                        for record in relevant:
                            if record['claim']['predicate']==pred:
                                for k,v in record['conditions'].items():
                                    if contains(v,clause):available.setdefault(k,set()).add(v)
                        for k,values in available.items():
                            if k not in query['conditions'] and len(values)==1:query['conditions'][k]=next(iter(values))
                        dates=re.findall(r'\b\d{4}-\d{2}-\d{2}\b',clause)
                        if hints.get('at'):query['at']=hints['at']
                        elif len(set(dates))==1:query['at']=dates[0]
                        result.append({'kind':'lookup','selector':query})
                    if depth<4 and c['kind']=='relationship' and x['polarity']=='affirmed' and x['claim_id'] not in seen:
                        following.append((c['value'],x['object_sense'],path+[pred],seen|{x['claim_id']}))
            if len(following)>64:blocked.append({'reason':'Relationship search slice is incomplete; narrow or explicitly select a path.','incomplete':True})
            frontier=following[:64]
    unique={canonical(r):r for r in result}
    values=list(unique.values())
    # An explicitly requested chain uses its terminal predicate. Independent
    # predicates with no prefix relationship remain independent subquestions.
    values=[r for r in values if not any(r['selector']['subject']==other['selector']['subject'] and r['selector']['sense']==other['selector']['sense'] and r['selector']['scope']==other['selector']['scope'] and len(r['selector']['path'])<len(other['selector']['path']) and (r['selector']['path']+[r['selector']['predicate']])==other['selector']['path'][:len(r['selector']['path'])+1] for other in values)]
    return values,blocked


def _math(clause,items,whole,hints,previous):
    """Compile explicit arithmetic grammar; never invent a physical law from units."""
    from vector_core.tools import compute,evaluate
    from vector_core.semantic import Semantics
    if 'calculation' in hints:
        c=hints['calculation']
        if not isinstance(c,dict) or set(c)!={'operation','parameters'}:raise ValueError('Invalid explicit calculation.')
        compute(c['operation'],c['parameters']);return {'strategy':'calculate','input':c,'method':'explicit trusted-user calculation','unit':c['parameters'].get('to','1')}
    if re.search(r'\b\d{4}-\d{2}-\d{2}\b',clause) and not re.match(r'\s*(?:calculate|compute|evaluate)\b',clause,re.I):return None
    match=re.fullmatch(r'\s*(?:please\s+)?convert\s+([-+\d.eE]+)\s+([^\s]+)\s+to\s+([^\s?.]+)[?.]?\s*',clause,re.I)
    if match:
        c={'operation':'convert','parameters':{'value':match[1],'from':match[2],'to':match[3]}};compute(c['operation'],c['parameters']);return {'strategy':'calculate','input':c,'method':'explicit unit conversion','unit':match[3]}
    q=clause.strip().rstrip('.?');target=None
    match=re.search(r'\s+in\s+([^\s]+)$',q)
    if match:target=match[1];q=q[:match.start()]
    q=re.sub(r'^then\s+','',q,flags=re.I)
    q=re.sub(r'^(?:then\s+)?(?:please\s+)?(?:calculate|compute|evaluate|use|what is)\s+','',q,flags=re.I)
    q=re.split(r'\s+(?:for)\s+',q,maxsplit=1,flags=re.I)[0]
    q=re.sub(r'\bthe\s+','',q,flags=re.I)
    for pattern,replacement in [(r'^multiply (.+) by (.+)$',r'(\1)*(\2)'),(r'^divide (.+) by (.+)$',r'(\1)/(\2)'),(r'^add (.+) to (.+)$',r'(\1)+(\2)'),(r'^subtract (.+) from (.+)$',r'(\2)-(\1)')]:q=re.sub(pattern,replacement,q,flags=re.I)
    if not re.search(r'(?:\s[+*/-]\s|[()+*/]|\d[+*/-])',q):return None
    bindings={};names={};rewritten=q
    for item in items:
        for name in [item['claim']['predicate'],*item['predicate_aliases']]:
            names[name]=None
            for subject in Semantics.names(item):
                names[subject+' '+name]=None;names[name+' of '+subject]=None
    for name in sorted(names,key=len,reverse=True):
        if not contains(name,rewritten):continue
        selectors,_=_selectors(items,name,whole,hints)
        selectors=[s for s in selectors if not s['selector']['path']]
        # One property can be backed by multiple agreeing/conflicting sources;
        # the independent semantic calculator resolves those, not this parser.
        unique={canonical(s['selector']):s['selector'] for s in selectors}
        if len(unique)!=1:raise ValueError('Arithmetic property is ambiguous: '+name)
        variable='v'+str(len(bindings)+1);bindings[variable]=next(iter(unique.values()))
        rewritten=re.sub(r'(?<!\w)'+re.escape(name)+r'(?!\w)',variable,rewritten,flags=re.I)
    dependency=None
    if re.search(r'\bresult\b',rewritten,re.I):
        if previous is None:raise ValueError('A previous numeric result is required.')
        if previous.get('strategy')!='calculate':raise ValueError('A source-bound result requires an explicit supported quantity binding before further arithmetic; no value or unit is assumed.')
        rewritten=re.sub(r'\bresult\b','previous',rewritten,flags=re.I);dependency={'previous':{'step':previous['id'],'field':'value','unit':previous['unit']}}
    # Validate arithmetic syntax using harmless dimensions/values. Actual source
    # values and dimensional checks happen independently during execution.
    placeholders={k:{'value':'1','unit':'1'} for k in bindings}
    if dependency:placeholders['previous']={'value':'1','unit':'1'}
    evaluate(rewritten,placeholders)
    if bindings and dependency:raise ValueError('Split source-bound arithmetic and prior-result arithmetic into separate steps.')
    if bindings:
        parameters={'expression':rewritten}
        if target:parameters['target_unit']=target
        return {'strategy':'grounded','input':{'request':{'kind':'calculate','operation':'arithmetic','parameters':parameters,'bindings':bindings}},'method':'explicit source-property arithmetic','unit':target}
    if target:raise ValueError('For literal quantities use explicit unit conversion or a source-bound expression.')
    args={'operation':'arithmetic','parameters':{'expression':rewritten}}
    if dependency:args['bindings']=dependency
    return {'strategy':'calculate','input':args,'method':'explicit arithmetic with independently replayed dependencies','unit':'1','dependency':previous['id'] if dependency else None}


def build(memory,question,*,constraints=None,clarification='',basis=None,freeze=True):
    text(question,2000)
    if clarification:text(clarification,2000)
    hints=_constraints(constraints or {})
    if freeze:
        row=memory.db.execute('SELECT id FROM persistent_records ORDER BY rowid DESC LIMIT 1').fetchone();basis=row[0] if row else None
    whole=question+(' '+clarification if clarification else '')
    clauses=[p.strip() for p in re.split(r'[;?]+|\band\s+(?=(?:what|which|how)\b)',question,flags=re.I) if p.strip()]
    literal_only='request' not in hints;prior=None
    for number,clause in enumerate(clauses):
        try:literal=_math(clause,[],whole,hints,prior)
        except (ValueError,KeyError,TypeError):literal=None
        if not literal or literal['strategy']!='calculate':literal_only=False;break
        prior={'id':'task-'+str(number+1),'unit':literal['unit'] or '1','strategy':'calculate'}
    items,truncated=([],False) if literal_only else _catalog(memory,basis,hints.get('catalog_after',0))
    if not literal_only and hints.get('catalog_after',0)>0:truncated=True
    if len(clauses)>16:raise ValueError('This planning slice supports sixteen objectives; continue in another slice without discarding history.')
    tasks=[];unresolved=[];alternatives=[];assumptions=['Reviewed source interpretations are not established empirical truth.','Language grounding proposes an interpretation; it does not prove general natural-language entailment.'];previous=None
    for index,clause in enumerate(clauses):
        key=str(index+1)
        try:
            calculation=_math(clause,items,whole,hints,previous)
            if calculation is None and clarification and len(clauses)==1:calculation=_math(clarification,items,whole,hints,previous)
        except (ValueError,KeyError,TypeError) as error:
            unresolved.append({'objective':clause,'reason':str(error),'choices':[]});continue
        if calculation:
            identifier='task-'+str(len(tasks)+1);dep=[calculation['dependency']] if calculation.get('dependency') else []
            tasks.append({'id':identifier,'strategy':calculation['strategy'],'depends':dep,'input':calculation['input'],'method':calculation['method'],'objective':clause});previous={'id':identifier,'unit':calculation['unit'] or '1','strategy':calculation['strategy']};continue
        if 'request' in hints:
            requests=[hints['request']];blocked=[]
        else:requests,blocked=_selectors(items,clause+(' '+clarification if clarification else ''),whole,hints)
        residual=[] if 'request' in hints else _remaining_lookup_words(items,clause+(' '+clarification if clarification else ''),requests)
        if requests and residual:
            unresolved.append({'objective':clause,'reason':'The matched facts do not resolve the remaining interpretation/method: '+', '.join(residual),'choices':[{'id':_request_id(r),'request':r} for r in requests[:8]]});continue
        alternatives.extend(blocked[:4])
        if any(b.get('incomplete') for b in blocked):
            unresolved.append({'objective':clause,'reason':'Relationship search slice is incomplete; no uniqueness claim is justified.','choices':[]});continue
        groups={}
        for request in requests:
            selector=request['selector'];groups.setdefault((selector['subject'],selector['predicate']),[]).append(request)
        if not groups:
            unresolved.append({'objective':clause,'reason':'No unique supported interpretation/method is available. Retrieve relevant sources, clarify the requested relationship or propose an unverified approach.','choices':blocked[:4]});continue
        for group in groups.values():
            choices=[{'id':_request_id(r),'request':r} for r in group]
            selected=hints.get('choices',{}).get(key)
            if selected:
                group=[c['request'] for c in choices if c['id']==selected]
                if not group:raise ValueError('Interpretation choice is not an offered source-grounded candidate.')
            if len(group)!=1:
                unresolved.append({'objective':clause,'reason':'Multiple senses, scopes or paths remain; select an interpretation rather than silently choosing.','choices':choices});continue
            request=group[0];selector=request['selector'];matching=[i for i in items if i['claim']['scope']==selector['scope'] and any(contains(n,whole) for n in [i['claim']['subject'],*i['aliases']])]
            missing={k for i in matching for k,v in i['conditions'].items() if k not in selector['conditions'] and i['claim']['predicate']==selector['predicate']}
            if missing:unresolved.append({'objective':clause,'reason':'Required source applicability is unspecified: '+', '.join(sorted(missing)), 'choices':choices});continue
            identifier='task-'+str(len(tasks)+1);tasks.append({'id':identifier,'strategy':'grounded','depends':[],'input':{'request':request},'method':'reviewed concept/alias grounding with explicit relationship paths','objective':clause})
    if truncated:unresolved.append({'objective':question,'reason':'The reviewed catalog slice is incomplete; advance the catalog cursor or narrow the scope. No completeness claim is established.','choices':[]})
    report={'format':FORMAT,'objective':question,'clarification':clarification,'constraints':hints,'basis':basis,'catalog_complete':not truncated,'catalog_consulted':not literal_only,'operational_scope':{'catalog_limit':LIMIT,'relationship_depth':4,'frontier':64,'objectives':16,'meaning':'Renewable bounded slice, not a ceiling on inquiry.'},'assumptions':assumptions,'tasks':tasks,'unresolved':unresolved,'alternatives':alternatives,'evidence_requirements':[{'objective':t['objective'],'request':t['input'].get('request'),'verification':'Original source hashes/spans, qualified applicability and independently replayed tool results.'} for t in tasks]+[{'objective':u['objective'],'request':None,'verification':'Additional applicable evidence, a method or clarification is required; no definite answer is established.'} for u in unresolved],'completion_criteria':['Every requested objective has an applicable checked finding or an explicit unresolved question.','A finished workflow does not certify hypotheses, source truth or novel discovery.'],'next_actions':['Inspect checked findings and unresolved evidence requirements.','Clarify or revise the investigation using new information.','Optionally request unverified neural hypotheses or supply an alternative approved plan.']}
    if len(canonical(report).encode())>14500:raise ValueError('Planning slice exceeds its existing step budget; narrow or split the question.')
    return report


def validate_analysis(memory,report):
    if not isinstance(report,dict) or report.get('format')!=FORMAT:raise ValueError('Unknown planning record format.')
    expected=build(memory,report['objective'],constraints=report['constraints'],clarification=report['clarification'],basis=report['basis'],freeze=False)
    if canonical(expected)!=canonical(report):raise ValueError('Planning record changed its objective, evidence grounding, constraints, dependencies or methods.')
    return report


def compile_steps(report,prefix='q1'):
    from vector_core.investigation import plan
    steps=[{'id':prefix+'-plan','strategy':'plan','depends':[],'input':{'analysis':report}}];translated={t['id']:prefix+'-'+t['id'] for t in report['tasks']}
    for task in report['tasks']:
        data=json.loads(canonical(task['input']))
        for binding in data.get('bindings',{}).values():binding['step']=translated[binding['step']]
        steps.append({'id':translated[task['id']],'strategy':task['strategy'],'depends':[translated[d] for d in task['depends']],'input':data})
    selected=list(translated.values())
    if report['unresolved'] or not selected:selected.append(prefix+'-plan')
    if not report['tasks']:steps.append({'id':prefix+'-evidence','strategy':'retrieve','depends':[prefix+'-plan'],'input':{'query':report['objective'][:512],'evidence_budget':3500}})
    steps.append({'id':prefix+'-answer','strategy':'compose','depends':selected,'input':{}})
    return plan(steps)


class Planner:
    def __init__(self,memory,adapter=None,config=None):
        from vector_core.investigation import Investigations
        self.memory=memory;self.inv=Investigations(memory,adapter,config)
    def create(self,question,*,constraints=None,clarification='',project_id=None,approved=False,identifier=None):
        self.inv.authority.ordinary(approved)
        report=build(self.memory,question,constraints=constraints,clarification=clarification)
        return self.inv.create(question,compile_steps(report),project_id=project_id,approved=approved,identifier=identifier)
    def run(self,key,*,budget=None,approved=False,cancellation=None):
        execution=self.inv.run(key,budget=budget,approved=approved,cancellation=cancellation)
        return {**self.view(key),'execution':execution}
    def revise(self,key,revision,*,clarification='',constraints=None,steps=None,approved=False):
        self.inv.authority.ordinary(approved);state=self.inv.get(key)
        if state['revision']!=revision:raise ValueError('Investigation changed; reload before revision.')
        if steps is not None:raise ValueError('Use explicit investigation_control for a manually approved alternative; model proposals are not executable plans.')
        previous=self.view(key)['analysis'];merged={**previous['constraints'],**(constraints or {})}
        report=build(self.memory,state['goal'],constraints=merged,clarification=clarification or previous['clarification'])
        results,_=self.inv._results(key);retained=[s for s in state['plan'] if s['id'] in results]
        prefix='q'+str(1+sum(s['strategy']=='plan' for s in retained))
        replacement=retained+(steps if steps is not None else compile_steps(report,prefix))
        if len(replacement)>128:raise ValueError('Current plan chunk is full; start a linked continuation. All previous state/evidence remains available.')
        return self.inv.control(key,'redirect',revision,steps=replacement,approved=approved)
    def explore(self,key,revision,*,approved=False):
        self.inv.authority.ordinary(approved);state=self.inv.get(key)
        if state['revision']!=revision:raise ValueError('Investigation changed; reload before exploration.')
        results,_=self.inv._results(key);retained=[s for s in state['plan'] if s['id'] in results]
        suffix=uuid4().hex[:8];evidence='explore-'+suffix;proposal='proposal-'+suffix
        steps=[*retained,{'id':evidence,'strategy':'retrieve','depends':[],'input':{'query':state['goal'][:512],'evidence_budget':1024}},
               {'id':proposal,'strategy':'synthesize','depends':[evidence],'input':{'planning_proposal':True}},
               {'id':'answer-'+suffix,'strategy':'compose','depends':[s['id'] for s in retained if s['strategy'] in {'grounded','calculate'}]+[proposal],'input':{}}]
        return self.inv.control(key,'redirect',revision,steps=steps,approved=approved)
    def view(self,key):
        from vector_core.findings import validate_document,current_notices
        state=self.inv.get(key);results,feedback=self.inv._results(key)
        planning=[s for s in state['plan'] if s['strategy']=='plan']
        if not planning:raise ValueError('This investigation has no question-planning record; its original interface remains available.')
        analysis=planning[-1]['input']['analysis'];validate_analysis(self.memory,analysis)
        boundary=max(i for i,s in enumerate(state['plan']) if s['strategy']=='plan')
        answers=[results[s['id']] for s in state['plan'][boundary:] if s['strategy']=='compose' and s['id'] in results]
        answer=answers[-1] if answers and analysis['objective']==state['goal'] else None
        if answer:validate_document(self.memory,answer)
        intermediate=None
        if answer is None and analysis['objective']==state['goal']:
            completed=[s['id'] for s in state['plan'][boundary:] if s['id'] in results and s['strategy'] in {'grounded','calculate'}]
            if completed:
                from vector_core.findings import compose
                intermediate=compose(self.memory,key,completed[-32:])
        unresolved=list(analysis['unresolved'])
        if analysis['objective']!=state['goal']:unresolved.append({'objective':state['goal'],'reason':'The goal changed outside the compiled interpretation; rebuild or revise the plan before treating earlier answers as current.','choices':[]})
        if answer:
            for f in answer['findings']:
                if f['status'] not in {'source-supported','inferred','verified-computation'}:
                    unresolved.append({'objective':f['subject'],'reason':'Finding status: '+f['status'],'choices':[]})
        if feedback:unresolved.extend({'objective':step,'reason':error,'choices':[]} for step,error in feedback.items() if step not in results)
        pending=[s['id'] for s in state['plan'] if s['id'] not in results]
        if pending:unresolved.append({'objective':state['goal'],'reason':'This investigation has unfinished work. Resume within its approved scope.','choices':[]})
        evidence=[];seen=set()
        for result in results.values():
            for source in result.get('context',{}).get('sources',[]):
                source_key=(source['event_id'],source['start'],source['end'])
                if source_key in seen:continue
                if self.memory.event(source['event_id'])['sha256']!=source['sha256'] or self.memory.read_text_span(source['event_id'],source['start'],source['end'])!=source['quote']:raise ValueError('Retrieved planning evidence changed its original attestation.')
                evidence.append(source);seen.add(source_key)
        from vector_core.context import display_notices
        notices=(current_notices(self.memory,answer or intermediate) if answer or intermediate else [])+[n['notice'] for n in display_notices(self.memory,list(dict.fromkeys(s['event_id'] for s in evidence)))]
        message=(answer['text'] if answer else 'Investigation prepared; no completed checked answer yet.')
        if intermediate:message+='\n\nCompleted intermediate findings (investigation unfinished):\n'+intermediate['text']
        if unresolved:message+='\n\nStill unresolved:\n'+'\n'.join('- '+u['objective']+': '+u['reason'] for u in unresolved)
        message+='\n\nPossible next steps: clarify the question or constraints, inspect sources, revise the plan, or request unverified hypotheses.'
        return {'id':key,'state':state,'analysis':analysis,'answer':answer,'evidence_sources':evidence,'intermediate_answer':intermediate,'intermediate_findings':(answer or intermediate or {}).get('findings',[]),'unresolved':unresolved,'pending':pending,'notices':notices,'next_actions':analysis['next_actions'],'completion':{'workflow_complete':state['status']=='complete','findings_complete':bool(answer) and not unresolved,'interpretation_status':'Proposed language grounding; general entailment is not certified.'},'message':message,'experimental':True,'limits':'Grounded interpretation and explicit arithmetic, not general natural-language entailment or verified discovery.'}


def chat(memory,question,*,conversation_id,project_id=None,adapter=None,config=None,request_id=None,investigation_id=None,revision=None,constraints=None,cancellation=None):
    """Ordinary query path with durable turn identity before plan creation/execution."""
    from vector_core.persistence import put
    from vector_core.investigation import Budget
    identity(conversation_id);turn=identity(request_id) if request_id is not None else uuid4().hex;key=conversation_id+':'+turn
    row=memory.db.execute("SELECT payload FROM persistent_records WHERE contract='conversations' AND record_key=? ORDER BY rowid DESC LIMIT 1",(key,)).fetchone()
    planner=Planner(memory,adapter,config)
    if row:
        record=json.loads(row[0])
        if record['question']!=question or record['project_id']!=project_id:raise ValueError('A request identity cannot be reused for another question/project.')
        if canonical(record['planning_ref']['constraints'])!=canonical(constraints or {}):raise ValueError('A request identity cannot be reused with different constraints.')
        target=record['planning_ref']['investigation_id']
    else:
        target=identity(investigation_id) if investigation_id else uuid4().hex
        record={'id':turn,'conversation_id':conversation_id,'project_id':project_id,'question':text(question,2000),'created':now(),'context':None,'outcome':{'status':'pending','answer':None,'generation':None,'errors':[]},'trace':[],'planning_ref':{'investigation_id':target,'constraints':_constraints(constraints or {}),'clarification_base':revision if investigation_id else None}}
        put(memory,'conversations',key,record)
        if investigation_id and revision is None:raise ValueError('A recorded revision is required for a follow-up clarification.')
    exists=memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='investigations' AND record_key=?",(target,)).fetchone()
    base=record['planning_ref']['clarification_base']
    if exists is None:
        if base is not None:raise ValueError('Missing investigation for saved clarification; no replacement is fabricated.')
        planner.create(question,constraints=constraints,project_id=project_id,approved=True,identifier=target)
    elif base is not None:
        current=planner.inv.get(target)
        if current['revision']==base:planner.revise(target,base,clarification=question,constraints=constraints,approved=True)
        elif planner.view(target)['analysis']['clarification']!=question:raise ValueError('Investigation changed before clarification; reload its actual state.')
    state=planner.inv.get(target)
    # Repeated turns and saved in-flight work do not silently repeat inference or
    # recompute completed steps; explicit lifecycle controls resume interruptions.
    if state['status']=='ready':view=planner.run(target,budget=Budget(64,0,30),approved=True,cancellation=cancellation)
    else:view=planner.view(target)
    record['outcome']['status']='checked-investigation' if view['completion']['findings_complete'] else 'investigation-unresolved'
    record['trace']=[{'stage':'question-planning','investigation_id':target,'state_revision':view['state']['revision']}]
    if row is None or canonical(record)!=row[0]:put(memory,'conversations',key,record)
    return {**record,'planning':view}


def materialize_turn(memory,record):
    if 'planning_ref' not in record:return record
    key=record['planning_ref']['investigation_id']
    found=memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='investigations' AND record_key=?",(key,)).fetchone()
    if found:return {**record,'planning':Planner(memory).view(key)}
    return {**record,'planning':{'id':key,'state':None,'answer':None,'message':'Saved question is pending plan creation. Retry this turn with the same request identity; no finding is fabricated.','unresolved':[],'pending':['plan creation'],'next_actions':[]}}
