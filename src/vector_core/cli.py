"""Supported runtime: kernel policy precedes data or logging operations."""
import json
import sys


def main(argv=None):
    from vector_core.security import activate,SecurityError
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
    for name in ('export-vector','restore-vector','import-vector','verify-export'):
        action=commands.add_parser(name)
        action.add_argument('directory');action.add_argument('--key-file')
        action.add_argument('--deadline',type=float,default=900)
        if name=='export-vector':action.add_argument('--resume')
        elif name in ('restore-vector','import-vector'):
            action.add_argument('--resume',action='store_true');action.add_argument('--snapshot')
        else:action.add_argument('--snapshot')
    move=commands.add_parser('move-data');move.add_argument('destination');move.add_argument('--deadline',type=float,default=900)
    commands.add_parser('storage');commands.add_parser('storage-recover')
    action=commands.add_parser('create-recovery-key');action.add_argument('output')
    action=commands.add_parser('events');action.add_argument('--after',default='');action.add_argument('--limit',type=int,default=100)
    action=commands.add_parser('import-asset');action.add_argument('contract');action.add_argument('name');action.add_argument('file')
    action.add_argument('--purpose',default='portable-data')
    action=commands.add_parser('register-model');action.add_argument('name');action.add_argument('version');action.add_argument('runtime');action.add_argument('assets',nargs='+')
    action=commands.add_parser('register-contract');action.add_argument('name');action.add_argument('description')
    action=commands.add_parser('state-put');action.add_argument('contract');action.add_argument('key');action.add_argument('json_file')
    action=commands.add_parser('state-list');action.add_argument('contract');action.add_argument('--after',type=int,default=0);action.add_argument('--limit',type=int,default=100)
    for name in ('ask','models'):
        action=commands.add_parser(name);action.add_argument('--models-directory');action.add_argument('--managed',action='store_true')
        if name=='ask':
            action.add_argument('question');action.add_argument('--model');action.add_argument('--context',type=int,default=2048)
            action.add_argument('--output-tokens',type=int,default=256);action.add_argument('--timeout',type=float,default=30)
    action=commands.add_parser('calculate');action.add_argument('operation');action.add_argument('parameters');action.add_argument('--approve',action='store_true')
    args=parser.parse_args(argv)
    transport=None;startup_error=None
    if args.command in ('ask','models') and (args.models_directory or args.managed):
        try:
            from vector_core.worker_launcher import launch,launch_managed
            transport=launch_managed() if args.managed else launch(args.models_directory)
        except (RuntimeError,ValueError,OSError) as error:startup_error=str(error)
    try:policy=activate(pipe_fds=transport.retained_fds if transport else ())
    except SecurityError as error:
        if transport:transport.close()
        print('VECTOR startup blocked: '+str(error),file=sys.stderr);return 2
    command=args.command or 'health'
    try:
        config=Config.load(args.config,args.data_dir)
        if command=='create-recovery-key':
            from vector_core.portable_crypto import create_key
            create_key(args.output)
            print(json.dumps({'created':str(Path(args.output).absolute()),'keep_separate':True}));return 0
        if command in ('restore-vector','import-vector','verify-export'):
            from vector_core.portable import restore_vector,verify_export
            if command=='verify-export':result=verify_export(args.directory,snapshot=args.snapshot,key_file=args.key_file,deadline_seconds=args.deadline)
            else:result=restore_vector(config,args.directory,snapshot=args.snapshot,key_file=args.key_file,resume=args.resume,deadline_seconds=args.deadline)
            print(json.dumps(result,indent=2));return 0
        if command=='restore':
            print(json.dumps(restore(config,args.backup_directory),indent=2));return 0
        with Memory(config) as memory:
            log=logger(config.data_dir)
            log.info('Operation started: %s',command)
            if command in ('ask','models','calculate'):
                from vector_core.service import Application
                application=Application(memory,transport,startup_error);application.policy=policy
                if command=='models':result=application.handle('models',{})
                elif command=='calculate':result=application.handle('tool',{'name':args.operation,'parameters':json.loads(args.parameters),'approved':args.approve})
                else:
                    if args.model and transport:
                        from dataclasses import asdict
                        from vector_core.inference import GenerationConfig
                        application.handle('select_model',{'configuration':asdict(GenerationConfig(args.model,args.context,args.output_tokens,args.timeout)),'authorize_external':True})
                    result=application.handle('ask',{'question':args.question})
            elif command=='health':
                result={'policy':policy,'database_integrity':memory.db.execute('PRAGMA quick_check').fetchone()[0],
                    'schema_version':memory.db.execute('PRAGMA user_version').fetchone()[0],
                    'data_directory':str(config.data_dir),'model_available':False,'release_ready':False,
                    'original_integrity':'not run; use verify'}
            elif command=='export-vector':
                from vector_core.portable import export_vector
                result=export_vector(memory,args.directory,key_file=args.key_file,resume=args.resume,deadline_seconds=args.deadline)
            elif command=='move-data':
                from vector_core.coordination import move_data
                result=move_data(memory,args.destination,deadline_seconds=args.deadline)
            elif command=='storage':
                from vector_core.storage import usage
                result=usage(memory)
            elif command=='storage-recover':
                from vector_core.storage import recover_objects
                result=recover_objects(memory)
            elif command=='events':result=memory.event_page(args.after,args.limit)
            elif command in ('import-asset','register-model','register-contract','state-put','state-list'):
                from vector_core import persistence
                if command=='import-asset':result=persistence.import_asset(memory,args.contract,args.name,args.file,args.purpose)
                elif command=='register-model':result={'record_id':persistence.model_manifest(memory,args.name,args.version,args.runtime,args.assets)}
                elif command=='register-contract':
                    persistence.register(memory,args.name,args.description);result={'registered':args.name}
                elif command=='state-list':result=persistence.records(memory,args.contract,after=args.after,limit=args.limit)
                else:
                    from vector_core.portable import unique
                    payload=json.loads(read_file(args.json_file,1024*1024),object_pairs_hook=unique)
                    result={'record_id':persistence.put(memory,args.contract,args.key,payload)}
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
                if args.file and Path(args.file).stat().st_size>memory.config.max_source_bytes:
                    result=memory.ingest_file(args.file,name=args.name,media_type=args.type,source_id=args.source,parent_id=args.parent)
                else:
                    raw=read_file(args.file,memory.config.max_source_bytes) if args.file else args.text.encode('utf-8')
                    result=memory.ingest(Submission(raw,args.name or (Path(args.file).name if args.file else 'User submission'),args.type,{'input_path':str(Path(args.file).absolute())} if args.file else {},args.source,args.parent))
            elif command=='show':
                result=memory.event(args.event_id)
                if args.text:result['original_text']=memory.original(args.event_id).decode('utf-8')
            elif command=='export':
                memory.export_original(args.event_id,args.output)
                result={'exported':str(Path(args.output).absolute()),'event_id':args.event_id}
            print(json.dumps(result,indent=2,ensure_ascii=False))
            return 1 if isinstance(result,dict) and result.get('passed') is False else 0
    except (ValueError,OSError,RuntimeError,KeyError,sqlite3.Error) as error:
        print('VECTOR operation blocked: '+str(error),file=sys.stderr)
        return 1
    finally:
        if transport:transport.close()

if __name__=='__main__': raise SystemExit(main())
