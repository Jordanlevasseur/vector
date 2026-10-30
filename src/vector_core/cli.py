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
    from vector_core.config import Config
    from vector_core.database import connect
    parser=argparse.ArgumentParser(description='VECTOR independent offline foundation')
    parser.add_argument('--data-dir')
    parser.add_argument('--config')
    parser.add_argument('command',choices=('health','backup'),nargs='?',default='health')
    args=parser.parse_args(argv)
    try:
        config=Config.load(args.config,args.data_dir)
        db=connect(config)
        from vector_core.maintenance import logger,backup
        log=logger(config.data_dir)
        log.info("Operation started: %s",args.command)
        try:
            if args.command=="backup":
                print(json.dumps(backup(db,config.data_dir),indent=2))
                return 0
            print(json.dumps({'policy':policy,'database_integrity':db.execute('PRAGMA quick_check').fetchone()[0],
                'schema_version':db.execute('PRAGMA user_version').fetchone()[0],
                'data_directory':str(config.data_dir),'model_available':False,'release_ready':False},indent=2))
        finally: db.close()
        return 0
    except (ValueError,OSError,RuntimeError) as error:
        print('VECTOR operation blocked: '+str(error),file=sys.stderr)
        return 1

if __name__=='__main__': raise SystemExit(main())
