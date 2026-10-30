"""Supported runtime: kernel policy precedes data or logging operations."""
import json
import sys


def main(argv=None):
    from vector_core.security import activate,SecurityError
    try: policy=activate()
    except SecurityError as error:
        print('VECTOR startup blocked: '+str(error),file=sys.stderr)
        return 2
    import argparse
    import sqlite3
    from pathlib import Path
    from vector_core.config import Config
    from vector_core.database import connect
    from vector_core.intake import read_file
    from vector_core.memory import Memory,Submission
    from vector_core.maintenance import logger,backup,restore
    parser=argparse.ArgumentParser(description='VECTOR independent offline permanent memory')
    parser.add_argument('--data-dir')
    parser.add_argument('--config')
    commands=parser.add_subparsers(dest='command')
    for command in ('health','backup','verify','list','rebuild','conflicts'): commands.add_parser(command)
    add=commands.add_parser('add')
    content=add.add_mutually_exclusive_group(required=True)
    content.add_argument('--file');content.add_argument('--text')
    add.add_argument('--name');add.add_argument('--type',default='text/plain')
    add.add_argument('--parent');add.add_argument('--source')
    show=commands.add_parser('show');show.add_argument('event_id');show.add_argument('--text',action='store_true')
    export=commands.add_parser('export');export.add_argument('event_id');export.add_argument('output')
    recovery=commands.add_parser('restore');recovery.add_argument('backup_directory')
    find=commands.add_parser('search');find.add_argument('query');find.add_argument('--source')
    find.add_argument('--since');find.add_argument('--until');find.add_argument('--limit',type=int,default=20)
    learning=commands.add_parser('learn')
    learning.add_argument('--file',required=True);learning.add_argument('--scope',required=True)
    learning.add_argument('--exclusive',action='store_true')
    claim=commands.add_parser('claim');claim.add_argument('claim_id')
    override=commands.add_parser('override');override.add_argument('claim_id')
    override.add_argument('--value',required=True);override.add_argument('--scope',required=True)
    override.add_argument('--reason',required=True);override.add_argument('--approve',action='store_true')
    args=parser.parse_args(argv)
    command=args.command or 'health'
    try:
        config=Config.load(args.config,args.data_dir)
        if command=='restore':
            print(json.dumps(restore(config,args.backup_directory),indent=2));return 0
        with Memory(config) as memory:
            log=logger(config.data_dir)
            log.info('Operation started: %s',command)
            if command=='health':
                result={'policy':policy,'database_integrity':memory.db.execute('PRAGMA quick_check').fetchone()[0],
                    'schema_version':memory.db.execute('PRAGMA user_version').fetchone()[0],
                    'data_directory':str(config.data_dir),'model_available':False,'release_ready':False,
                    'original_integrity':'not run; use verify'}
            elif command=='backup':result=backup(memory.db,config.data_dir)
            elif command=='verify':result=memory.verify()
            elif command=='list':result=memory.recent()
            elif command in ('learn','claim','conflicts','override'):
                from vector_core.knowledge import Knowledge,learn
                knowledge=Knowledge(memory)
                if command=='learn':
                    raw=read_file(args.file,config.max_source_bytes)
                    result=learn(memory,Submission(raw,Path(args.file).name),args.scope,args.exclusive)
                elif command=='claim':result=knowledge.claim(args.claim_id)
                elif command=='conflicts':result=knowledge.contradictions()
                else:result=knowledge.override(args.claim_id,args.value,args.scope,args.reason,approved=args.approve)
            elif command=='search':
                from vector_core.retrieval import search
                result=search(memory,args.query,limit=args.limit,source_id=args.source,since=args.since,until=args.until)
            elif command=='rebuild':
                from vector_core.retrieval import rebuild
                result=rebuild(memory)
            elif command=='add':
                raw=read_file(args.file,config.max_source_bytes) if args.file else args.text.encode('utf-8')
                result=memory.ingest(Submission(raw,args.name or (Path(args.file).name if args.file else 'User submission'),
                    args.type,{'input_path':str(Path(args.file).absolute())} if args.file else {},args.source,args.parent))
            elif command=='show':
                result=memory.event(args.event_id)
                if args.text:result['original_text']=memory.original(args.event_id).decode('utf-8')
            elif command=='export':
                from vector_core.intake import write_new_file
                write_new_file(args.output,memory.original(args.event_id))
                result={'exported':str(Path(args.output).absolute()),'event_id':args.event_id}
            print(json.dumps(result,indent=2,ensure_ascii=False))
            return 1 if isinstance(result,dict) and result.get('passed') is False else 0
    except (ValueError,OSError,RuntimeError,KeyError,sqlite3.Error) as error:
        print('VECTOR operation blocked: '+str(error),file=sys.stderr)
        return 1

if __name__=='__main__': raise SystemExit(main())
