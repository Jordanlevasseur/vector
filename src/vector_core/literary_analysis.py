"""Mechanical observations and optional source-verified CMU pronunciation lookup."""
import hashlib
import json
import re
from collections import Counter
from vector_core.coordination import write_operation
from vector_core.memory import now,canonical
from vector_core.persistence import put
from vector_core.projects import _insert
from vector_core.languages import identify

VERSION='literary-observations-v1'
HISTORICAL_LAYERS=('original','transliteration','morphology','literal_gloss','readable_translation','commentary','textual_variants','scholarly_disagreement')

def historical_frame(language):
    if language not in {'la-x-classic','grc','hbo'}:raise ValueError('Choose an initial historical-language module.')
    return {'language':language,'layers':list(HISTORICAL_LAYERS),'morphology_fields':['lemma','form','case','number','gender','person','tense','aspect','mood','voice','stem','alternatives'],
            'qualified':False,'policy':'All readings, glosses and analyses need exact source attestations and explicit review; unknown layers remain absent, not invented.'}

def dictionary_state(memory):
    row=memory.db.execute("SELECT payload FROM persistent_records WHERE contract='capabilities' AND record_key='english-pronunciation' ORDER BY rowid DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else None

@write_operation
def import_dictionary(memory,path,license_path,*,approved=False,limit=20000):
    if approved is not True:raise PermissionError('Explicit local dictionary/license import approval required.')
    if type(limit) is not int or not 1<=limit<=20000:raise ValueError('Dictionary batch must contain 1–20000 lines.')
    from vector_core.intake import read_file
    license_bytes=read_file(license_path,32768)
    if not all(t in license_bytes for t in (b'Carnegie Mellon',b'Redistribution and use',b'DISCLAIM')):raise ValueError('Expected complete CMU redistribution/license evidence; unknown terms rejected.')
    raw=read_file(path,memory.config.max_source_bytes);digest=hashlib.sha256(raw).hexdigest();state=dictionary_state(memory)
    if state and state['sha256']!=digest:raise ValueError('A different dictionary requires an explicit new capability namespace; previous data retained.')
    if state and state['complete']:return {**state,'unchanged_skipped':True}
    if not state:
        license_event=memory.ingest_file(license_path,name='CMUdict license',media_type='text/plain')
        source=memory.ingest_file(path,name='CMU US English pronunciation dictionary',media_type='text/plain')
        state={'event_id':source['event_id'],'license_event_id':license_event['event_id'],'sha256':digest,'offset':0,'entries':0,'complete':False,'source_url':'https://github.com/cmusphinx/cmudict','method':'CMU ARPABET source lookup; not poetry scansion or universal English pronunciation'}
        put(memory,'capabilities','english-pronunciation',state)
    text=raw.decode('utf-8');offset=state['offset'];count=0;entries=state['entries'];db=memory.db;db.execute('BEGIN IMMEDIATE')
    try:
        while offset<len(text) and count<limit:
            end=text.find('\n',offset);end=len(text) if end<0 else end+1;line=text[offset:end].strip();match=re.fullmatch(r"([a-z'][a-z0-9_'.-]*)(?:\((\d+)\))? ([A-Z0-9 ]+)(?: #.*)?",line)
            if match:
                word,variant,phones=match.groups();tokens=phones.split();phones=' '.join(tokens)
                if not 1<=len(tokens)<=64 or any(not re.fullmatch('[A-Z]{1,3}[012]?',t) for t in tokens):raise ValueError('Invalid pronunciation field.')
                db.execute('INSERT INTO literary_pronunciations VALUES (?,?,?,?,?,?)',(word,variant or '1',phones,state['event_id'],offset,end));entries+=1
            elif line and not line.startswith(';;;'):raise ValueError('Unsupported dictionary line; original retained.')
            offset=end;count+=1
        state.update(offset=offset,entries=entries,complete=offset>=len(text));_insert(memory,'capabilities','english-pronunciation',state);db.commit()
    except BaseException:db.rollback();raise
    return state

def pronunciation(memory,word,*,verified_source=None):
    state=dictionary_state(memory)
    if not state:return {'word':word,'available':False,'alternatives':[],'reason':'No locally imported licensed pronunciation resource.'}
    if not isinstance(word,str) or len(word)>100:raise ValueError('Invalid word lookup.')
    rows=memory.db.execute('SELECT * FROM literary_pronunciations WHERE event_id=? AND word=? ORDER BY variant',(state['event_id'],word.casefold())).fetchall();alternatives=[]
    for row in rows:
        original=verified_source[1][row['start_char']:row['end_char']] if verified_source and verified_source[0]==row['event_id'] else memory.read_text_span(row['event_id'],row['start_char'],row['end_char'])
        body=original.split(' #',1)[0].strip()
        if ' '.join(body.split()[1:])!=row['phones'] or body.split(' ',1)[0].split('(',1)[0]!=row['word']:raise ValueError('Corrupt pronunciation index; source mismatch.')
        phones=row['phones'].split();vowels=[i for i,p in enumerate(phones) if p[-1:].isdigit()];stress=[phones[i][-1] for i in vowels]
        stressed=[i for i in vowels if phones[i][-1] in '12'];rhyme=phones[(stressed[-1] if stressed else vowels[-1]):] if vowels else []
        alternatives.append({'variant':row['variant'],'phones':phones,'syllables':len(vowels),'stress':''.join(stress),'rhyme_tail':rhyme,'event_id':row['event_id'],'start':row['start_char'],'end':row['end_char'],'quote':original})
    return {'word':word,'available':bool(alternatives),'alternatives':alternatives,'license_event_id':state['license_event_id'],'limits':'American-English dictionary alternatives, not guaranteed literary performance, dialect equivalence or calibrated meter.'}

def observe(memory,event_id,start,end):
    if type(start) is not int or type(end) is not int or not 0<=start<end or end-start>4000:raise ValueError('Select an exact passage of at most 4000 characters.')
    original=memory.read_text_span(event_id,start,end);event=memory.event(event_id)
    dictionary=dictionary_state(memory);verified_source=(dictionary['event_id'],memory.original(dictionary['event_id']).decode('utf-8')) if dictionary else None
    lines=[];cursor=start;stanzas=0;in_stanza=False
    for raw in original.splitlines(keepends=True):
        body=raw.rstrip('\r\n')
        if body.strip():
            if not in_stanza:stanzas+=1
            in_stanza=True
            words=re.findall(r"[^\W_]+(?:['’][^\W_]+)*",body);last=words[-1] if words else None
            pron=pronunciation(memory,last,verified_source=verified_source) if last else {'alternatives':[]}
            lines.append({'start':cursor,'end':cursor+len(body),'text':body,'last_word':last,'last_word_pronunciations':pron})
        else:in_stanza=False
        cursor+=len(raw)
    words=re.findall(r"[^\W_]+(?:['’][^\W_]+)*",original);frequency=Counter(w.casefold() for w in words)
    repetitions=[{'form':w,'count':count} for w,count in frequency.most_common(32) if count>1]
    candidates=[]
    for match in re.finditer(r'\b(like|as|because|therefore|however)\b',original,re.I):
        if len(candidates)>=32:break
        candidates.append({'marker':match.group(),'start':start+match.start(),'end':start+match.end(),'interpretation':'Lexical comparison/argument cue only; figurative use or valid inference not established.'})
    return {'version':VERSION,'event_id':event_id,'sha256':event['sha256'],'start':start,'end':end,'quote':original,
            'script_evidence':identify(original),'nonblank_lines':len(lines),'stanzas':stanzas,'stanza_count_interpretation':'Blank-line grouping only; prose paragraphs and wrapped editions may not encode poetic stanzas.','lines':lines,'tokens':len(words),'repeated_forms':repetitions,'lexical_cues':candidates,
            'sentence_boundary_candidates':[start+m.end() for m in re.finditer(r'[.!?]+(?=\s|$)',original)][:100],
            'interpretive_status':'Themes, symbolism, narrative, metaphor, irony, grammar and meter require source-linked reviewed interpretations. No automatic literary certainty or model competence claim.'}

def propose_vocabulary(memory,event_id,start,end,language,*,approved=False):
    if approved is not True:raise PermissionError('Explicit vocabulary-candidate action required.')
    from vector_core.literature import Library
    raw=memory.read_text_span(event_id,start,end)
    if len(raw)>4000:raise ValueError('Passage too large.')
    event=memory.event(event_id);words=list(dict.fromkeys(re.findall(r'[^\W_]+',raw)))[:32];results=[]
    for word in words:
        at=raw.find(word);a={'event_id':event_id,'sha256':event['sha256'],'start':start+at,'end':start+at+len(word),'quote':word}
        results.append(Library(memory).annotate(language,'word_form',word,{'observation':'Literal written form, not an inferred lemma, sense or grammar rule.'},[a],uncertainty='Candidate vocabulary; requires review. Token boundaries are not a universal tokenizer.',approved=True))
    return {'proposals':results,'truncated':len(set(re.findall(r'[^\W_]+',raw)))>len(words),'facts_created':0}

def summarize_body(original,event_id,sha256,start,end):
    """Literal book-body observations; bounded previews never replace the source."""
    body=original[start:end];frequency=Counter();first={};total=0
    for match in re.finditer(r"[^\W_]+(?:['’][^\W_]+)*",body):
        quote=match.group();key=quote.casefold();frequency[key]+=1;total+=1
        if len(quote)<=100 and key not in first:first[key]={'quote':quote,'start':start+match.start(),'end':start+match.end()}
    candidates=[{'form':word,'count':count,**first[word]} for word,count in frequency.most_common(64) if word in first][:32]
    return {'event_id':event_id,'sha256':sha256,'method':'literal-body-observations-v1','start':start,'end':end,'characters':len(body),
            'nonblank_lines':sum(bool(line.strip()) for line in body.splitlines()),'blank_line_blocks':len([part for part in re.split(r'\r?\n[ \t]*\r?\n',body) if part.strip()]),
            'word_form_tokens':total,'word_form_candidates':candidates,'script_sample':identify(body),'status':'mechanical source observations; no inferred lemmas/senses/themes/grammar facts',
            'limits':'Casefolded lexical-form counts and bounded previews, not universal word segmentation, language identification, semantics or neural learning.'}
