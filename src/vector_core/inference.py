"""Model-independent bounded inference; simulation is explicit, never a fallback."""
from dataclasses import dataclass,asdict
import json
import math
import time

# Fixed server-owned schema. It controls syntax, never fills answers/citations.
CITATION_SCHEMA={'type':'object','properties':{'event_id':{'type':'string'},'sha256':{'type':'string'},
    'start':{'type':'integer'},'end':{'type':'integer'},'quote':{'type':'string'}},
    'required':['event_id','sha256','start','end','quote'],'additionalProperties':False}
ANSWER_SCHEMA={'type':'object','properties':{
    'statements':{'type':'array','maxItems':20,'items':{'type':'object','properties':{
        'text':{'type':'string'},'kind':{'type':'string','enum':['source','inference']},
        'citations':{'type':'array','minItems':1,'maxItems':8,'items':CITATION_SCHEMA}},
        'required':['text','kind','citations'],'additionalProperties':False}},
    'uncertainty':{'type':'string'},'insufficient':{'type':'boolean'}},
    'required':['statements','uncertainty','insufficient'],'additionalProperties':False}

CLAIM_SCHEMA={'type':'object','properties':{'drafts':{'type':'array','maxItems':32,'items':{
    'type':'object','properties':{'event_id':{'type':'string'},'start':{'type':'integer'},'end':{'type':'integer'},
        'subject':{'type':'string'},'predicate':{'type':'string'},'value':{'type':'string'},'scope':{'type':'string'},
        'unit':{'type':'string'},'kind':{'type':'string','enum':['claim']},'exclusive':{'type':'boolean'}},
    'required':['event_id','start','end','subject','predicate','value','scope','unit','kind','exclusive'],
    'additionalProperties':False}}},'required':['drafts'],'additionalProperties':False}

class InferenceError(RuntimeError):pass

@dataclass(frozen=True)
class GenerationConfig:
    model: str=''
    context_tokens: int=2048
    output_tokens: int=256
    timeout_seconds: float=30
    temperature: float=0
    seed: int=0
    def validate(self):
        if not isinstance(self.model,str) or len(self.model)>200:raise ValueError('Invalid model name.')
        if type(self.context_tokens) is not int or not 512<=self.context_tokens<=32768:raise ValueError('Context must be 512–32768 tokens.')
        if type(self.output_tokens) is not int or not 16<=self.output_tokens<=min(4096,self.context_tokens//2):raise ValueError('Invalid generation budget.')
        if type(self.timeout_seconds) not in (int,float) or not math.isfinite(self.timeout_seconds) or not 0.1<=self.timeout_seconds<=300:raise ValueError('Timeout must be 0.1–300 seconds.')
        if type(self.temperature) not in (int,float) or not math.isfinite(self.temperature) or not 0<=self.temperature<=1:raise ValueError('Invalid temperature.')
        if type(self.seed) is not int or not 0<=self.seed<2**31:raise ValueError('Invalid seed.')
        return self
    @property
    def prompt_bytes(self):return max(128,self.context_tokens-self.output_tokens-256)

class Cancellation:
    cancelled=False
    def cancel(self):self.cancelled=True

class UnavailableAdapter:
    simulated=False
    def discover(self):return {'available':False,'models':[],'reason':'No separately qualified inference worker selected.'}
    def generate(self,prompt,config,cancellation=None,*,response_kind=None):
        config.validate()
        raise InferenceError(self.discover()['reason'])

class SimulatedAdapter:
    """Deterministic framework tests only; never selected by production routing."""
    simulated=True
    def __init__(self,responses):self.responses=iter(responses)
    def generate(self,prompt,config,cancellation=None,*,response_kind=None):
        config.validate()
        if cancellation and cancellation.cancelled:raise InferenceError('Cancelled.')
        response=next(self.responses)
        if isinstance(response,Exception):raise response
        return checked_result(response,config,simulated=True,runtime='explicit-test-simulation',model_version='fixture')


def checked_result(text,config,*,simulated=False,runtime='',model_version='',metrics=None):
    if not isinstance(text,str) or len(json.dumps(text,ensure_ascii=False).encode())>min(1024*1024,config.output_tokens*64):
        raise InferenceError('Malformed or excessive generation output.')
    return {'text':text,'simulated':simulated,'model':config.model,'runtime_version':runtime,
            'model_version':model_version,'configuration':asdict(config),'metrics':metrics or {}}

class OllamaAdapter:
    simulated=False
    def __init__(self,transport):
        if not transport.qualified:raise InferenceError('Inference isolation is not qualified.')
        self.transport=transport
    def discover(self):return self.transport.request({'operation':'discover'},10)
    def generate(self,prompt,config,cancellation=None,*,response_kind=None):
        config.validate()
        if not isinstance(prompt,str) or len(prompt.encode())>config.prompt_bytes:raise InferenceError('Prompt exceeds conservative byte budget.')
        if cancellation and cancellation.cancelled:raise InferenceError('Cancelled.')
        response=self.transport.request({'operation':'generate','prompt':prompt,'config':asdict(config),'response_kind':response_kind},config.timeout_seconds,cancellation)
        if not isinstance(response,dict) or response.get('done') is not True or response.get('done_reason')=='length':
            error=InferenceError('Incomplete/truncated model generation.')
            error.raw_generation=response.get('response') if isinstance(response,dict) else None
            raise error
        if type(response.get('prompt_eval_count')) is not int or response['prompt_eval_count']+config.output_tokens>config.context_tokens:
            raise InferenceError('Actual prompt token count exceeds the accepted context budget.')
        result=checked_result(response.get('response'),config,runtime=self.transport.runtime_version,
                              model_version=response.get('model_digest','unknown'),metrics={k:response.get(k) for k in ('prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration')})
        result['response_format']=response_kind or 'json'
        return result
