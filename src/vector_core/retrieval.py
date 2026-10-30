"""Bounded literal FTS5 retrieval with original event/source provenance."""
from datetime import datetime,timezone
import json
import re


def timestamp(value):
    moment=datetime.fromisoformat(value)
    if moment.tzinfo is None: raise ValueError('Time filters require an explicit time zone.')
    return moment.astimezone(timezone.utc).isoformat(timespec='microseconds')


def search(memory,query,*,limit=20,source_id=None,since=None,until=None,metadata=None):
    if not isinstance(query,str) or len(query)>512:
        raise ValueError('Query must be text up to 512 characters.')
    if type(limit) is not int or not 1<=limit<=100: raise ValueError('Result limit must be 1-100.')
    tokens=re.findall(r'[^\W_]+',query,flags=re.UNICODE)
    if len(tokens)>16: raise ValueError('Query exceeds 16 lexical terms.')
    conditions=[];parameters=[]
    ranked=bool(tokens)
    if ranked:
        conditions.append('text_search MATCH ?')
        parameters.append(' AND '.join('"'+token+'"' for token in tokens))
    elif not any((source_id,since,until,metadata)):
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
         'substr(t.text,1,500) AS excerpt,'+score+' AS rank '
         'FROM texts t JOIN events e ON e.id=t.event_id '+join+
         'WHERE '+' AND '.join(conditions)+
         (' ORDER BY rank,e.occurred DESC,e.id' if ranked else ' ORDER BY e.occurred DESC,e.id')+' LIMIT ?')
    results=[]
    for row in memory.db.execute(sql,parameters+[limit]):
        result=dict(row)
        original=memory.original(result['event_id']).decode('utf-8')
        derived=memory.db.execute('SELECT text FROM texts WHERE event_id=?',(result['event_id'],)).fetchone()[0]
        if derived!=original:
            raise ValueError('Derived text differs from original; rebuild the index before trusting results.')
        result['excerpt']=original[:500]
        results.append(result)
    return results


def index_event(db,event_id,text,status):
    if status=='utf8-extracted':
        rowid=db.execute('SELECT rowid FROM texts WHERE event_id=?',(event_id,)).fetchone()[0]
        db.execute('INSERT INTO text_search(rowid,text) VALUES (?,?)',(rowid,text))


def rebuild(memory):
    """One atomic derived-data rebuild; originals/hashes remain authoritative."""
    from vector_core.memory import extract,now
    db=memory.db
    count=0
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute("INSERT INTO text_search(text_search) VALUES ('delete-all')")
        db.execute('DELETE FROM texts')
        for event_id,digest,media_type,content in db.execute(
                'SELECT e.id,e.sha256,e.media_type,b.body FROM events e JOIN blobs b ON b.sha256=e.sha256'):
            import hashlib
            if hashlib.sha256(content).hexdigest()!=digest: raise ValueError('Original hash failure; rebuild aborted.')
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
