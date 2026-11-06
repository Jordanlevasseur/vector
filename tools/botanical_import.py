"""Owner/developer-reviewed LOCAL pack intake; no download or model dispatch."""
import argparse,json
from vector_core.security import activate
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.botany import import_pack
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--data-dir',required=True);p.add_argument('--pack',required=True)
p.add_argument('--review-sha256',required=True,help='SHA-256 of the exact independently reviewed manifest.json')
a=p.parse_args();policy=activate()
with Memory(Config.load(data_dir=a.data_dir)) as memory:
 print(json.dumps({'result':import_pack(memory,a.pack,a.review_sha256),'policy':policy},ensure_ascii=False))
