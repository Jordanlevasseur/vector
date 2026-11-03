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

# Language frontend only. Execution, precision, units, state and independent
# verification remain in tools/investigation/findings. Unknown language is kept.
ROUTING='vector-capability-route-v1'
OPERATORS=[(r'\bmultiplied\s+by\b','*'),(r'\bdivided\s+by\b','/'),(r'\bto\s+the\s+power\s+of\b','**'),(r'\b(?:times)\b','*'),(r'\bplus\b','+'),(r'\bminus\b','-'),(r'\bpercent(?:age)?\s+of\b','/100*'),(r'%\s*of\b','/100*')]


def processing(question,version=2):
    """Open-ended scheduling hints, not answers or a catalog of allowed topics.

    The legacy capability grammar stays immutable for saved calculation/evidence
    replay. Unknown requests remain eligible for ordinary selected-model inference.
    """
    if not isinstance(question,str) or not question.strip():raise ValueError('Enter a complete request.')
    if type(version) is not int or version not in (1,2):raise ValueError('Unknown processing-hint version.')
    q=question.strip();kind='general';workflow='direct'
    if re.fullmatch(r'(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening)|how\s+are\s+you)[.!?\s]*',q,re.I):kind='conversation'
    elif re.search(r'\b(?:investigat\w*|research|hypothes\w*|experiment|study)\b',q,re.I):kind='research';workflow='reflect'
    elif re.search(r'\b(?:brainstorm|invent|creative|ideas|alternatives|ways\s+to)\b',q,re.I):kind='creative';workflow='reflect'
    elif re.search(r'\b(?:compare|analyse|analyze|tradeoffs?|trade-offs?|design|plan)\b',q,re.I):kind='analysis';workflow='reflect'
    elif re.search(r'\b(?:deduc\w*|contradict\w*|logic\w*|prove|reason\w*)\b|\bif\b.+\bthen\b|\bevery\b.+\b(?:no|does)\b',q,re.I):kind='reasoning';workflow='reflect'
    elif re.match(r'^(?:explain|describe|how)\b',q,re.I):kind='explanation'
    elif re.match(r'^(?:what|where|who|when|which)\b',q,re.I):kind='factual'
    # A short request usually needs a direct answer or a model-generated
    # clarification, rather than three automatic deliberation calls.
    words=len(re.findall(r'[^\W_]+',q))
    linked=version==2 and words>=8 and bool(re.search(r'\b(?:then|afterwards|subsequently)\b',q,re.I))
    if linked and kind!='conversation':kind='reasoning';workflow='reflect'
    if workflow=='reflect' and words<12 and not linked:workflow='direct'
    return {'version':version,'task_type':kind,'workflow':workflow,'basis':'Conservative language scheduling hint; not semantic entailment, verification or an action authorization.'}


def literal_math(clause,previous=False):
    """Fully consumed numeric grammar, not a search for numbers in prose."""
    import ast
    from vector_core.tools import number
    q=clause.strip().rstrip('?.!').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',q):raise ValueError('This looks like an ISO date, not an unambiguous arithmetic request.')
    q=re.sub(r'^(?:please\s+)?(?:what\s+is|what[’\x27]s|how\s+much\s+is|calculate|compute|evaluate)\s+','',q,flags=re.I)
    conversion=re.fullmatch(r'convert\s+([-+\d.eE,]+)\s+([^\s]+)\s+to\s+([^\s]+)',q,re.I)
    if conversion:
        value=conversion[1]
        if ',' in value:
            if not re.fullmatch(r'[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?',value):raise ValueError('Ambiguous digit grouping; use a decimal point and groups of three.')
            value=value.replace(',','')
        number(value);return {'operation':'convert','parameters':{'value':value,'from':conversion[2],'to':conversion[3]}}
    q=q.replace('×','*').replace('÷','/').replace('−','-').replace('^','**')
    q=re.sub(r'\b(?:the\s+)?(?:result|that)\b','previous',q,flags=re.I)
    q=re.sub(r'^then\s+','',q,flags=re.I)
    if previous:
        for word,operator in [('divide','/'),('multiply','*')]:q=re.sub(r'^'+word+r'\s+by\s+(.+)$',r'previous'+operator+r'(\1)',q,flags=re.I)
        q=re.sub(r'^add\s+(.+)$',r'previous+(\1)',q,flags=re.I);q=re.sub(r'^subtract\s+(.+)$',r'previous-(\1)',q,flags=re.I)
    for pattern,replacement in [(r'^multiply (.+) by (.+)$',r'(\1)*(\2)'),(r'^divide (.+) by (.+)$',r'(\1)/(\2)'),(r'^add (.+) to (.+)$',r'(\1)+(\2)'),(r'^subtract (.+) from (.+)$',r'(\2)-(\1)'),(r'^sum of (.+) and (.+)$',r'(\1)+(\2)')]:q=re.sub(pattern,replacement,q,flags=re.I)
    for pattern,replacement in OPERATORS:q=re.sub(pattern,replacement,q,flags=re.I)
    q=re.sub(r'(?<=\d)\s+\bx\b\s+(?=[\d.(+-])','*',q,flags=re.I)
    if '%' in q:
        # A modulo-looking or compound postfix form is ambiguous; never turn
        # e.g. '20 % 3' into the unrelated numeric expression '20 / 1003'.
        percent=re.fullmatch(r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*%',q)
        if not percent:raise ValueError('Use an explicit percent-of request, or a single percentage; modulo and compound postfix percentages are not supported.')
        q='('+percent[1]+'/100)'
    # Group separators may only occur inside well-formed numeric tokens.
    if ',' in q:
        q=re.sub(r'(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w.,])',lambda m:m[0].replace(',',''),q)
        if ',' in q:raise ValueError('Ambiguous comma notation; use explicit decimal points and parentheses.')
    q=q.strip()
    if '#' in q:raise ValueError('Comments are not arithmetic; the entire request must be explicit and supported.')
    if not 1<=len(q)<=256:raise ValueError('Arithmetic expression exceeds the existing tool budget.')
    try:tree=ast.parse(q,mode='eval')
    except (SyntaxError,RecursionError) as error:raise ValueError('Use explicit operators and parentheses; this arithmetic notation is incomplete or unsupported.') from error
    nodes=list(ast.walk(tree))
    if len(nodes)>80:raise ValueError('Arithmetic exceeds the existing expression-node budget.')
    allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.UAdd,ast.USub,ast.Load)
    for node in nodes:
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):number(ast.get_source_segment(q,node));continue
        if isinstance(node,ast.Name) and node.id=='previous':continue
        if not isinstance(node,allowed):raise ValueError('Only explicit numeric arithmetic, integer powers and unit conversion are supported here; functions, implicit multiplication and prose need clarification or another method.')
    return {'operation':'arithmetic','parameters':{'expression':q},'previous':any(isinstance(n,ast.Name) for n in nodes)}


def request(question):
    """Bounded capability eligibility; no topic catalog or model-issued actions."""
    plan(question)  # Reuse the established question/type/size boundary.
    q=question.strip();base={'format':ROUTING,'objective':question,'interpretation':'Proposed operation from a fully consumed bounded language grammar, not general entailment.'}
    summary=re.match(r'^(?:please\s+)?(?:summari[sz]e|sum\s+up|give\s+(?:me\s+)?a\s+summary\s+of)\s+(.+?)[?.!]*$',q,re.I)
    if summary:return {**base,'kind':'summarize','query':re.sub(r'^(?:the|a|an)\s+','',summary[1].rstrip('?.!'),flags=re.I)}
    if re.fullmatch(r'what\s+about\s+(?:it|that|them|those)[?.!]*',q,re.I):return {**base,'kind':'retrieve','query':q.rstrip('?.!'),'implicit':True,'continuation':True}
    retrieval=re.match(r'^(?:please\s+)?(?:find|search(?:\s+for)?|look\s+up|show(?:\s+me)?)\s+(?:(?:information|sources?|documents?|passages?)\s+(?:about|on|for)\s+|(?:about|on)\s+)?(.+?)[?.!]*$',q,re.I)
    if retrieval:return {**base,'kind':'retrieve','query':retrieval[1].rstrip('?.!')}
    clauses=[s.strip() for s in re.split(r';|,\s*then\b|\band\s+then\b',q,flags=re.I)]
    if any(not s.rstrip('?.!').strip() for s in clauses):return {**base,'kind':'clarify','reason':'A calculation step is missing. Complete every operation before execution.'}
    if len(clauses)>16:return {**base,'kind':'clarify','reason':'This calculation slice supports sixteen explicit operations; split the request without discarding the remaining objective.'}
    calculations=[];failure=None if clauses else 'Enter a complete request.'
    for index,clause in enumerate(clauses):
        try:calculations.append(literal_math(clause,previous=index>0 or bool(re.search(r'\b(?:result|that)\b',clause,re.I))))
        except ValueError as error:failure=str(error);break
    if failure is None:return {**base,'kind':'calculate','calculations':calculations}
    math_intent=bool(re.search(r'\d',q) and (re.search(r'[+*/×÷^%=]|\b(?:times|multiplied|divided|plus|minus|percent|calculate|compute|evaluate|multiply|divide|subtract|add|sum|sqrt|sin|cos|convert)\b',q,re.I) or re.match(r'^[\s\d.,eE()+−-]+$',q)))
    if math_intent:return {**base,'kind':'clarify','reason':failure}
    # Bare entity/property searches preserve the established evidence-only path.
    words=re.findall(r'[^\W_]+',q)
    if 1<len(words)<=6 and not re.match(r'^(?:why|how|what|which|who|explain|describe|write|invent|investigate|brainstorm|hello|hi)\b',q,re.I):return {**base,'kind':'retrieve','query':q.rstrip('?.!'),'implicit':True}
    return {**base,'kind':'interpret','reason':'No independently verified operation has been established for the whole request. Neural interpretation or an explicitly approved investigation may help.'}
