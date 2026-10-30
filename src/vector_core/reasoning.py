"""Bounded observable task decomposition; no hidden reasoning or autonomous actions."""
import re


def plan(question,max_steps=4):
    if type(max_steps) is not int or not 1<=max_steps<=6:raise ValueError('Plan budget must be 1–6.')
    if not isinstance(question,str) or not 1<=len(question)<=2000:raise ValueError('Invalid question.')
    parts=[part.strip() for part in re.split(r'[;?]+|\s+and\s+',question,flags=re.I) if part.strip()]
    tasks=[{'id':index+1,'question_fragment':part[:400],'action':'retrieve-evidence-only','authorization':'no tool or filesystem actions'} for index,part in enumerate(parts[:max_steps])]
    return {'tasks':tasks,'truncated':len(parts)>max_steps,'method':'literal clause splitting, not semantic planning',
            'verification':['original hash/span attribution','strict answer schema','quote/source equality'],
            'not_verified':['semantic entailment','general multi-step reasoning correctness','model confidence calibration']}
