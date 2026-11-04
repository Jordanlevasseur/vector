"""Local discovery/selection policy over the existing protected model executor.

AUTO is a preference, not a new execution-record format. Every run still freezes
exact model roles, prompt, configuration, digests and actual isolation evidence.
"""
from dataclasses import asdict
from vector_core.inference import GenerationConfig,InferenceError,OllamaAdapter
from vector_core.persistence import put,register
from vector_core.runtime_policy import hardware,plan,rank_models

AUTO_LABEL='AUTO — Recommended'

class LocalAdapter:
    simulated=False
    def __init__(self,manager):self.manager=manager;self.transport=manager.proxy
    def discover(self):
        return {'available':any(m.get('compatible') is not False for m in self.manager.models),'models':self.manager.models,'runtime_qualified':self.transport.qualified,'reason':'Approved local models discovered. Protected runtime starts when used; no model is loaded for browsing.'}
    def generate(self,prompt,config,cancellation=None,*,response_kind=None):
        if not self.transport.qualified:raise InferenceError('Execution has not qualified the protected worker.',code='WORKER_CLOSED')
        return OllamaAdapter(self.transport).generate(prompt,config,cancellation,response_kind=response_kind)

class AdaptiveRuntime:
    def __init__(self,app,proxy):
        self.app=app;self.proxy=proxy;self.models=proxy.boot['models'];self.host=proxy.boot['hardware'];self.active_plan=None;self.excluded=[];self.attempts=[]
        self.observations=self._observations();self.last_selection=None
        if app.preference('default_runtime_selection') is None:put(app.memory,'preferences','default_runtime_selection',{'mode':'auto'})
    def _observations(self):
        import json
        rows=self.app.memory.db.execute("SELECT payload FROM persistent_records WHERE contract='capabilities' AND record_key LIKE 'local-runtime:%' ORDER BY rowid DESC LIMIT 64").fetchall()
        return [json.loads(r[0]) for r in rows if isinstance(json.loads(r[0]),dict)]
    def selection(self):return self.app.preference('runtime_selection:'+self.app.session['conversation_id']) or self.app.preference('default_runtime_selection') or {'mode':'auto'}
    def automatic(self):return self.selection()['mode']=='auto'
    def execution_mode(self):
        s=self.selection();return s['mode'] if s['mode'] in {'a','b','both'} else 'a'
    def select(self,selection,scope='conversation',model=None):
        if scope not in {'conversation','default'} or selection not in {'auto','a','b','both','model'}:raise ValueError('Invalid local selection policy.')
        value={'mode':selection}
        if selection=='model':
            if model not in {m['name'] for m in self.models}:raise ValueError('Select an exact installed local model.')
            value['model']=model
        key='default_runtime_selection' if scope=='default' else 'runtime_selection:'+self.app.session['conversation_id']
        put(self.app.memory,'preferences',key,value);self.excluded=[];self.last_selection=None
        return value
    def manual_settings(self,saved):
        settings={**saved,'bindings':dict(saved['bindings']),'generation':dict(saved['generation'])}
        viable=[m for m in self.models if m.get('compatible') is not False]
        ordered=sorted(viable,key=lambda m:(m.get('parameter_count') or 0,m.get('name','')))
        for role in ('a','b'):
            if role in settings['bindings']:continue
            candidate=next((m for m in ordered if m['name'] not in settings['bindings'].values()),None)
            if candidate:settings['bindings'][role]=candidate['name']
        return settings
    def settings(self,saved,*,context_required=2048):
        settings=self.manual_settings(saved)
        if self.automatic():
            # Re-evaluate RAM on each new task. A previous error is not a
            # permanent disable flag; exclusions are scoped to one request.
            self.host=hardware(self.app.memory.config.data_dir)
            p=plan(self.models,self.host,context_required=context_required,observations=self.observations,exclude=self.excluded)
            settings['bindings']={'a':p['models'][0]};settings['synthesis']='a';settings['extra_reviews']=0
            settings['generation']=asdict(GenerationConfig('',p['context_tokens'],p['output_tokens'],300))
            self.last_selection=p
        elif self.selection()['mode']=='model':settings['bindings']={'a':self.selection()['model']};settings['synthesis']='a'
        return settings
    def prepare(self,names,config,progress=None):
        if progress:progress({'phase':'discovering','label':'Discovering approved local models and checking current hardware'})
        self.host=hardware(self.app.memory.config.data_dir)
        p=plan(self.models,self.host,context_required=config.context_tokens,output_tokens=config.output_tokens,observations=self.observations,manual_names=names,experimental=bool(not self.automatic() and self.proxy.boot.get('experimental_authorized')),manual_limit=self.proxy.boot.get('manual_limit') if not self.automatic() else None)
        p['selection']='auto' if self.automatic() else 'manual'
        p['tasks']=min(p['tasks'],self.proxy.boot.get('tasks_limit',p['tasks']))
        if self.automatic():
            # Execution receives an exact frozen role; recommendations still
            # constrain AUTO, even though manual attempts may exceed estimates.
            for participant in p['participants']:
                if participant['estimate']['estimated_bytes']>p['memory_bytes']:raise InferenceError('RESOURCE_BLOCKED: AUTO recommendation no longer fits current available RAM.',code='RESOURCE_LIMIT',stage='resource-protection')
        # Keep an already qualified service when its cap remains safe and the
        # exact model/context set matches. A larger new budget is not a reason
        # to restart a healthy worker before every message.
        same=self.proxy.qualified and self.active_plan and set(self.active_plan['models'])==set(names) and self.active_plan['context_tokens']==config.context_tokens and self.active_plan['memory_bytes']<=p['memory_bytes'] and self.active_plan['experimental']==p['experimental']
        if not same:
            if progress:progress({'phase':'verifying','label':'Verifying selected model files; starting and qualifying protected local inference'})
            self.proxy.ensure(p);self.active_plan=p;self.app.prepared_models.clear()
        self.app.startup_error=None
        # API/show proves metadata support in the installed runtime. Inference
        # completion is recorded separately; metadata alone is not success.
        actual=self.proxy.request({'operation':'discover'},60)
        discovered={m['name']:m for m in actual.get('models',[])}
        for name in names:
            row=next(m for m in self.models if m['name']==name)
            observed=discovered.get(name,{}).get('digest')
            if observed not in {row.get('source_manifest_sha256'),row.get('selector_sha256'),row.get('digest')} or not observed:raise InferenceError('Qualified runtime model digest differs from the verified local manifest/selector.',code='MODEL_INTEGRITY',stage='model-metadata')
            row.update(digest=observed,integrity_verified=True,availability='Selected file graph SHA-verified; protected runtime metadata inspected. Inference completion is recorded separately.')
            if not row.get('runtime_inspected'):
                info=self.proxy.request({'operation':'inspect','model':name},45)
                row.update(runtime_inspected=True,capabilities=info.get('capabilities',[]),tool_calling='tools' in info.get('capabilities',[]),runtime_version=self.proxy.runtime_version)
        if progress:progress({'phase':'ready','label':'Protected runtime ready; loading selected model for this response'})
        return p
    def observe(self,run):
        for step in run['steps']:
            generation=step.get('generation')
            if step['status']!='complete' or not generation or generation.get('simulated') is not False:continue
            resources=generation.get('resources') or {};peak=resources.get('peak_memory_bytes')
            if not peak:continue
            record={'id':run['id']+':'+step['phase'],'model':step['model'],'model_digest':step['model_digest'],'simulated':False,'inference_completed':True,'accuracy_operational_gate':False,'context_tokens':generation['configuration']['context_tokens'],'peak_memory_bytes':peak,'peak_swap_bytes':resources.get('peak_swap_bytes'),'hardware_fingerprint':self.host['fingerprint'],'runtime_version':generation.get('runtime_version'),'metrics':generation.get('metrics'),'resources':resources}
            put(self.app.memory,'capabilities','local-runtime:'+record['id'],record);self.observations.append(record)
            row=next((m for m in self.models if m.get('name')==step['model'] and m.get('digest')==step['model_digest']),None)
            if row is not None:row.update(compatible=True,real_inference_completed=True,availability='Genuine inference completed on this host; accuracy remains unverified.')
        self.observations=self.observations[-64:]
    def catalog(self):
        try:settings=self.app.model_controller.settings();reason=None
        except (RuntimeError,ValueError,OSError) as error:settings=None;reason=str(error)
        s=self.selection();label=AUTO_LABEL if s['mode']=='auto' else 'Manual: '+(s.get('model') or s['mode'].upper())
        actual=settings['bindings'] if settings else {}
        return {'selection':s,'default_selection':self.app.preference('default_runtime_selection'),'label':label,'active_models':actual,'hardware':self.host,'plan':self.last_selection if self.automatic() else self.active_plan,'reason':reason,'runtime_qualified':self.proxy.qualified,'automatic_fallback':'Maximum three distinct candidates, plus one restart for a transient worker failure; cancellation and accuracy never trigger fallback.','gpu':'Detected only; existing CPU-only security policy remains enforced.'}
