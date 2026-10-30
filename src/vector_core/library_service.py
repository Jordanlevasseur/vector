"""Fixed, offline application operations. Never a model tool or arbitrary dispatcher."""
import json
import re
from vector_core.literature import Library,PG_NOTICE,pg_license_span
from vector_core.projects import latest,identity
from vector_core.persistence import records

def dispatch(app,operation,p):
    memory=app.memory;library=Library(memory)
    if operation=='library_languages':
        from vector_core.languages import seed
        seed(memory);return records(memory,'languages',after=p.get('after',0),limit=100)
    if operation=='library_reset_index':return library.reset_index(approved=p.get('approved',False))
    if operation=='library_stats':return library.stats()
    if operation=='library_editions':return library.editions(p.get('query',''),language=p.get('language'),author=p.get('author'),subject=p.get('subject'),since=p.get('since'),until=p.get('until'),after=p.get('after',0))
    if operation=='library_edition':
        record=library.edition(p['id']);record['rights_notice']=PG_NOTICE if record['metadata']['rights']['status']=='provider-unrestricted-us' else record['metadata']['rights']['basis']
        return record
    if operation=='library_related':
        edition=library.edition(p['id']);rows=memory.db.execute("SELECT payload FROM persistent_records WHERE contract='linguistic_links' AND (json_extract(payload,'$.left')=? OR json_extract(payload,'$.right')=?) AND json_extract(payload,'$.relation') IN ('edition-of','translation-of','volume-of') ORDER BY rowid LIMIT 30",(edition['id'],edition['id'])).fetchall()
        items=[]
        for row in rows:
            link=json.loads(row[0]);target=link['right'] if link['left']==edition['id'] else link['left'];items.append({'relationship':link,'edition':library.edition(target)})
        return {'items':items}
    if operation=='library_license':
        edition=library.edition(p['id'])
        if edition['metadata']['rights']['status']=='provider-unrestricted-us':
            original=memory.original(edition['event_id']).decode('utf-8');start,end=pg_license_span(original)
            if len(original)-start>65536:raise ValueError('License exceeds viewer budget; export the complete original.')
            return {'event_id':edition['event_id'],'start':start,'end':len(original),'quote':original[start:]}
        evidence=memory.original(edition['rights_event_id']).decode('utf-8')
        if len(evidence)>65536:raise ValueError('Rights evidence exceeds viewer budget; export original evidence.')
        return {'event_id':edition['rights_event_id'],'start':0,'end':len(evidence),'quote':evidence}
    if operation=='library_import':
        result=library.import_pack(p['directory'],offset=p.get('offset',0),limit=p.get('limit',2),approved=p.get('approved',False),fingerprint=p.get('fingerprint'))
        if app.session['project_id'] and result['items']:
            from vector_core.projects import Projects
            Projects(memory).link_many(app.session['project_id'],[item['event_id'] for item in result['items']],approved=True)
        return result
    if operation=='library_process':return library.process(p['event_id'],limit=p.get('limit',500),rebuild=p.get('rebuild',False))
    if operation=='library_processing':return library.processing(p.get('after',0))
    if operation=='library_search':return {'items':library.search(p['query'],language=p.get('language'),event_id=p.get('event_id'))}
    if operation=='library_units':
        event=memory.event(p['event_id']);after=p.get('after',-1)
        if type(after) is not int or after< -1:raise ValueError('Invalid unit cursor.')
        rows=memory.db.execute('SELECT id,ordinal,kind,start_char,end_char FROM literary_units WHERE event_id=? AND ordinal>? ORDER BY ordinal LIMIT 50',(event['id'],after)).fetchall()
        return {'items':[dict(r) for r in rows],'next_cursor':rows[-1]['ordinal'] if rows else after}
    if operation=='library_observations':
        result=latest(memory,'literary_analyses',p['event_id'])
        for form in result['word_form_candidates']:
            if memory.read_text_span(result['event_id'],form['start'],form['end'])!=form['quote']:raise ValueError('Invalid lexical observation source.')
        return result
    if operation=='library_passage':return library.passage(p['id'])
    if operation=='library_observe':
        from vector_core.literary_analysis import observe
        return observe(memory,p['event_id'],p['start'],p['end'])
    if operation=='library_vocabulary':
        from vector_core.literary_analysis import propose_vocabulary
        return propose_vocabulary(memory,p['event_id'],p['start'],p['end'],p['language'],approved=p.get('approved',False))
    if operation=='library_annotate':return library.annotate(p['language'],p['kind'],p['label'],p['features'],p['attestations'],uncertainty=p['uncertainty'],record_id=p.get('id'),revision=p.get('revision'),approved=p.get('approved',False))
    if operation=='library_review':return library.review(p['id'],p['revision'],accept=p['accept'],approved=p.get('approved',False))
    if operation=='library_relate':return library.relate(p['left'],p['right'],p['relation'],p['reason'],p['uncertainty'],approved=p.get('approved',False))
    if operation=='library_concepts':return library.concepts(p['query'],p.get('language'),p.get('after',0))
    if operation=='library_record':
        result=latest(memory,'linguistic_records',identity(p['id']))
        for a in result['attestations']:
            if memory.read_text_span(a['event_id'],a['start'],a['end'])!=a['quote']:raise ValueError('Invalid attestation.')
        return result
    if operation=='library_historical':
        from vector_core.literary_analysis import historical_frame
        return historical_frame(p['language'])
    if operation=='library_dictionary_import':
        from vector_core.literary_analysis import import_dictionary
        return import_dictionary(memory,p['file'],p['license_file'],approved=p.get('approved',False))
    if operation=='library_pronunciation':
        from vector_core.literary_analysis import pronunciation
        return pronunciation(memory,p['word'])
    raise ValueError('Unknown literary operation; no commands or external acquisition are available.')
