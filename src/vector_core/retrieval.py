"""Bounded literal FTS5 retrieval with original event/source provenance."""
from datetime import datetime,timezone
from vector_core.coordination import write_operation

import json
import re


def timestamp(value):
    moment=datetime.fromisoformat(value)
    if moment.tzinfo is None: raise ValueError('Time filters require an explicit time zone.')
    return moment.astimezone(timezone.utc).isoformat(timespec='microseconds')


def search(memory,query,*,limit=20,source_id=None,since=None,until=None,metadata=None,project_id=None,category=None,omit_literary=False):
    if not isinstance(query,str) or len(query)>512:
        raise ValueError('Query must be text up to 512 characters.')
    if type(limit) is not int or not 1<=limit<=100: raise ValueError('Result limit must be 1-100.')
    tokens=re.findall(r'[^\W_]+',query,flags=re.UNICODE)
    if len(tokens)>16: raise ValueError('Query exceeds 16 lexical terms.')
    if category not in (None,'episodic','semantic','procedural','project'):raise ValueError('Unsupported source memory category.')
    if project_id is not None:
        from vector_core.projects import Projects
        Projects(memory).get(project_id)
    if category=='project' and project_id is None:raise ValueError('Select a project for project memory.')
    conditions=["t.status='utf8-extracted'"];parameters=[]
    if project_id:
        conditions.append("EXISTS (SELECT 1 FROM persistent_records a WHERE a.contract='project_sources' AND json_extract(a.payload,'$.project_id')=? AND json_extract(a.payload,'$.event_id')=e.id)")
        parameters.append(project_id)
    if category in ('semantic','procedural'):
        conditions.append("EXISTS (SELECT 1 FROM claims c WHERE c.event_id=e.id"+(" AND (c.kind='procedure' OR c.predicate='procedure')" if category=='procedural' else '')+")")
    if type(omit_literary) is not bool:raise ValueError('Invalid literary retrieval flag.')
    if omit_literary:conditions.append('NOT EXISTS (SELECT 1 FROM literary_units u WHERE u.event_id=e.id)')
    ranked=bool(tokens)
    if ranked:
        conditions.append('text_search MATCH ?')
        parameters.append(' AND '.join('"'+token+'"' for token in tokens))
    elif not any((source_id,since,until,metadata,project_id,category)):
        raise ValueError('Provide search terms or an explicit filter.')
    if source_id:
        conditions.append('e.source_id=?');parameters.append(source_id)
    for value,operator in ((since,'>='),(until,'<=')):
        if value:
            conditions.append('e.occurred'+operator+'?');parameters.append(timestamp(value))
    if since and until and timestamp(since)>timestamp(until): raise ValueError('Time range is reversed.')
    if metadata:
        if not isinstance(metadata,dict) or len(metadata)>4: raise ValueError('At most four metadata filters.')
        for key,value in metadata.items():
            if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',key):
                raise ValueError('Metadata filters use simple top-level text keys.')
            if value is None: kind='null'
            elif type(value) is bool: kind='true' if value else 'false'
            elif type(value) is int: kind='integer'
            elif type(value) is float: kind='real'
            elif type(value) is str: kind='text'
            else: raise ValueError('Metadata filter values must be JSON scalars.')
            json.dumps(value,allow_nan=False)
            path='$.'+key
            conditions.extend(['json_type(e.metadata,?)=?','json_extract(e.metadata,?) IS ?'])
            parameters.extend([path,kind,path,value])
    score='bm25(text_search)' if ranked else '0.0'
    join='JOIN text_search ON text_search.rowid=t.rowid ' if ranked else ''
    sql=('SELECT e.id AS event_id,e.source_id,e.sha256,e.occurred,e.submission_name AS name,'
         "json_extract(e.metadata,'$.resource_type') AS resource_type,substr(t.text,1,500) AS excerpt,"+score+' AS rank '
         'FROM texts t JOIN events e ON e.id=t.event_id '+join+
         'WHERE '+' AND '.join(conditions)+
         (' ORDER BY rank,e.occurred DESC,e.id' if ranked else ' ORDER BY e.occurred DESC,e.id')+' LIMIT ?')
    results=[]
    for row in memory.db.execute(sql,parameters+[limit]):
        result=dict(row)
        if str(result.get('resource_type','')).startswith('botanical-'):
            from vector_core.botany import provenance
            qualified=provenance(memory,result['event_id'])
            if qualified is None:continue  # staged/rolled-back sources are retained, not AI evidence
            result['botanical_provenance']=qualified
        original=memory.original(result['event_id']).decode('utf-8')
        derived=memory.db.execute('SELECT text FROM texts WHERE event_id=?',(result['event_id'],)).fetchone()[0]
        if derived!=original:
            raise ValueError('Derived text differs from original; rebuild the index before trusting results.')
        # A late-file hit must not be represented by an unrelated prefix.
        match=re.search('|'.join(re.escape(t) for t in tokens),original,re.IGNORECASE) if tokens else None
        start=max(0,match.start()-120) if match else 0
        result['start']=start;result['end']=min(len(original),start+500)
        result['excerpt']=original[start:result['end']]
        if result.get('resource_type')=='literary-work':
            row=memory.db.execute("SELECT json_extract(payload,'$.metadata.rights.status') FROM persistent_records WHERE contract='literary_editions' AND json_extract(payload,'$.event_id')=? LIMIT 1",(result['event_id'],)).fetchone()
            if row and row[0]=='provider-unrestricted-us':
                from vector_core.literature import PG_NOTICE
                result['rights_notice']=PG_NOTICE
        if result.get('resource_type')=='scientific-extracted-text':
            from vector_core.science import provenance
            result['scientific_provenance']=provenance(memory,result['event_id'])
        results.append(result)
    return results


def index_event(db,event_id,text,status):
    if status=='utf8-extracted':
        rowid=db.execute('SELECT rowid FROM texts WHERE event_id=?',(event_id,)).fetchone()[0]
        db.execute('INSERT INTO text_search(rowid,text) VALUES (?,?)',(rowid,text))


@write_operation
def rebuild(memory):
    """One atomic derived-data rebuild; originals/hashes remain authoritative."""
    from vector_core.memory import extract,now
    db=memory.db
    count=0
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute("INSERT INTO text_search(text_search) VALUES ('delete-all')")
        db.execute('DELETE FROM texts')
        for event_id,media_type in db.execute('SELECT id,media_type FROM events'):
            event=memory.event(event_id)
            if event['byte_count']>memory.config.max_source_bytes:
                for _ in memory.original_chunks(event_id):pass
                text,status=None,'streamed-original-preserved-index-deferred'
            else:
                content=memory.original(event_id)
                text,status=extract(content,media_type)
            db.execute('INSERT INTO texts VALUES (?,?,?)',(event_id,text,status))
            index_event(db,event_id,text,status)
            count+=1
        db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                   (now(),'index-rebuild',json.dumps({'events':count})))
        db.commit()
    except Exception:
        db.rollback();raise
    return {'rebuilt_events':count,'originals_modified':False}
