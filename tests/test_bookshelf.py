"""Bookshelf views use existing sources; synthetic fixtures are not installed content."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.resources import Resources
class BookshelfTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.m=Memory(Config.load(data_dir=str(Path(self.tmp.name)/'data')));self.addCleanup(self.m.close);self.r=Resources(self.m);self.addCleanup(self.r.close)
 def ingest(self,title,metadata=None,parent=None):return self.m.ingest(Submission(title.encode(),title,'text/plain',metadata or {},parent_id=parent))['event_id']
 def test_primary_view_preserves_audit_records_and_opens_complete_original(self):
  a=self.ingest('A whole original.txt');b=self.ingest('Extracted page',{'resource_type':'scientific-extracted-text','original_event_id':a},a);c=self.ingest('Rights metadata: fixture');d=self.ingest('Botanical complete body',{'resource_type':'botanical-original','botanical_role':'original'})
  page=self.r.list(view='bookshelf');self.assertEqual({p['id'] for p in page['items']},{a,d});self.assertEqual(page['total'],2);self.assertEqual(set(page['category_counts']),{'Other documents','Botanical sources'})
  self.assertEqual(self.r.read(a)['source_text'],'A whole original.txt');self.assertEqual(self.r.detail(b)['original_event_id'],a)
  self.assertEqual({p['id'] for p in self.r.list()['items']},{a,b,c,d})
 def test_empty_query_pagination_sorting_and_recent_opened(self):
  ids=[self.ingest(name) for name in ('Charlie','Alpha','Bravo')]
  self.assertEqual([r['title'] for r in self.r.list(view='bookshelf')['items']],['Alpha','Bravo','Charlie'])
  first=self.r.list(view='bookshelf',limit=2,sort='title_desc');second=self.r.list(view='bookshelf',after=first['next_cursor'],limit=2,sort='title_desc');self.assertEqual([p['title'] for p in first['items']+second['items']],['Charlie','Bravo','Alpha']);self.assertIsNone(second['next_cursor'])
  self.r.position(ids[1],offset=1);self.r.position(ids[0],offset=2);self.assertEqual(self.r.list(view='bookshelf',sort='recent')['items'][0]['id'],ids[0]);self.assertIsNotNone(self.r.list(view='bookshelf',sort='recent')['items'][0]['reading'])
  self.assertEqual(self.r.list('Bravo',view='bookshelf')['total'],1);self.assertEqual(self.r.list('',view='bookshelf')['total'],3)
 def test_original_checks_are_not_bypassed_by_lazy_browsing(self):
  key=self.ingest('Preserved original');self.r.list(view='bookshelf');descriptor=self.m.db.execute('SELECT object_digest FROM external_originals WHERE digest=?',(self.m.event(key)['sha256'],)).fetchone()
  if descriptor:
   path=Path(self.m.config.data_dir)/'objects'/descriptor[0][:2]/descriptor[0][2:];path.write_bytes(b'Corrupt fixture bytes')
   self.assertFalse(self.r.detail(key)['available'])
   with self.assertRaises(ValueError):self.r.open(key)
  else:self.assertEqual(self.r.read(key)['source_text'],'Preserved original')
 def test_original_root_lookup_has_an_additive_index(self):
  key=self.ingest('Root fixture');plan=self.m.db.execute('EXPLAIN QUERY PLAN SELECT id FROM events WHERE parent_id IS NULL OR id IN (?)',(key,)).fetchall()
  self.assertTrue(any('events_parent' in row[3] for row in plan),plan)
 def test_recent_order_stays_stable_across_reading_and_next_page(self):
  ids=[self.ingest(name) for name in ('One','Two','Three')]
  for key in ids:self.r.position(key,offset=1)
  first=self.r.list(view='bookshelf',sort='recent',limit=1);self.r.position(ids[0],offset=2)
  second=self.r.list(view='bookshelf',sort='recent',limit=1,after=first['next_cursor']);third=self.r.list(view='bookshelf',sort='recent',limit=1,after=second['next_cursor'])
  self.assertEqual({p['id'] for page in (first,second,third) for p in page['items']},set(ids))
 def test_native_autoload_scrolling_search_clear_return_and_error_retry(self):
  if not os.environ.get('DISPLAY'):self.skipTest('Local X11 display unavailable; actual bookshelf controls unverified.')
  script=r'''
import argparse,socket,tempfile,time
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as folder:
 data=str(Path(folder)/'data')
 with Memory(Config.load(data_dir=data)) as m:
  for i in range(125):m.ingest(Submission(('Complete original '+str(i)).encode(),'Book %03d.txt'%i,'text/plain'))
 args=argparse.Namespace(data_dir=data,choose_data=False,choose_models=False,models_directory=None,managed=False,no_inference=True,runtime_profile=None)
 root,client=bootstrap(args);app=Desktop(root,client);lib=app.library;errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  deadline=time.monotonic()+90
  while time.monotonic()<deadline:
   root.update();time.sleep(.02)
   if not client.pending and not lib.queue and lib.timer is None and lib.save_timer is None and lib.search_timer is None and not lib.loading:break
  assert not client.pending and not lib.queue and not lib.loading,'Bookshelf operation deadline';assert not errors,errors
 wait();app.shell.nav['Library'].invoke();wait();assert len(lib.rows)==40 and lib.loaded and lib.total==125 and lib.filters['category'][0].get()=='All Books'
 seen={r['id'] for r in lib.rows.values()}
 while lib.next_cursor is not None:
  before=lib.next_cursor;lib.listing.yview_moveto(1);root.update();time.sleep(.1);wait();assert lib.next_cursor!=before;seen.update(r['id'] for r in lib.rows.values());assert len(lib.rows)<=200
 assert len(seen)==125
 lib.query.insert(0,'Book 012');wait();assert len(lib.rows)==1;lib.query.delete(0,'end');wait();assert lib.total==125 and len(lib.rows)==40
 lib.listing.yview_moveto(.25);root.update();before=lib.listing.yview()[0];lib.listing.selection_set('5');lib.open_button.invoke();wait();assert lib.kind=='text' and lib.text.get('1.0','end-1c').startswith('Complete original');lib.back_button.invoke();wait();assert abs(lib.listing.yview()[0]-before)<.03
 lib.filters['sort'][0].set('Title Z–A');lib.filters['sort'][1].event_generate('<<ComboboxSelected>>');wait();assert lib.rows['0']['title']=='Book 124.txt'
 lib.catalog_failed('Explicit fixture load error');assert not lib.loaded and 'Explicit fixture' in lib.notice.get();lib.retry_button.invoke();wait();assert lib.loaded and lib.rows
 for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
  try:s=socket.socket(family,socket.SOCK_STREAM)
  except PermissionError:pass
  else:s.close();raise AssertionError('Network enabled')
 app.close()
print('bookshelf-native-passed')
'''
  root=Path(__file__).resolve().parents[1];env={**os.environ,'PYTHONPATH':os.pathsep.join((str(root/'src'),str(root/'tests'))),'PYTHONDONTWRITEBYTECODE':'1'};result=subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True,env=env,timeout=240);self.assertEqual(result.returncode,0,result.stderr+'\n'+result.stdout);self.assertIn('bookshelf-native-passed',result.stdout)
