"""Original-based library, durable state and actual qualified rendering controls."""
import hashlib,io,json,os,tarfile,tempfile,unittest,zipfile
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.resources import Resources,read_tool
from vector_core.service import Application

def pdf_bytes(pages=3,outline=False):
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',('<< /Type /Pages /Count '+str(pages)+' /Kids ['+' '.join(str(4+i*2)+' 0 R' for i in range(pages))+'] >>').encode(),b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    for i in range(pages):
        content=('BT /F1 18 Tf 30 160 Td (Library page '+str(i+1)+') Tj ET').encode()
        objects.extend([('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 3 0 R >> >> /Contents '+str(5+i*2)+' 0 R >>').encode(),b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream'])
    if outline:
        parent=len(objects)+1;item=parent+1;objects[0]=('<< /Type /Catalog /Pages 2 0 R /Outlines '+str(parent)+' 0 R >>').encode()
        objects.extend([('<< /Type /Outlines /First '+str(item)+' 0 R /Last '+str(item)+' 0 R /Count 1 >>').encode(),('<< /Title (Last chapter) /Parent '+str(parent)+' 0 R /Dest ['+str(4+(pages-1)*2)+' 0 R /Fit] >>').encode()])
    data=bytearray(b'%PDF-1.4\n');offsets=[0]
    for i,obj in enumerate(objects):offsets.append(len(data));data.extend(str(i+1).encode()+b' 0 obj\n'+obj+b'\nendobj\n')
    xref=len(data);data.extend(b'xref\n0 '+str(len(offsets)).encode()+b'\n0000000000 65535 f \n')
    for offset in offsets[1:]:data.extend(('%010d 00000 n \n'%offset).encode())
    data.extend(('trailer\n<< /Size '+str(len(offsets))+' /Root 1 0 R >>\nstartxref\n'+str(xref)+'\n%%EOF\n').encode());return bytes(data)

class ResourceLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.memory=Memory(Config.load(data_dir=str(self.root/'data')));self.addCleanup(self.memory.close);self.r=Resources(self.memory);self.addCleanup(self.r.close)
    def ingest(self,raw=b'Original text',name='Sample.txt',media='text/plain'):
        return self.memory.ingest(Submission(raw,name,media))['event_id']
    def test_all_events_duplicates_and_distinct_originals_are_separate_counts(self):
        a=self.ingest();b=self.ingest();c=self.ingest(b'other','Other.txt')
        inventory=self.r.inventory();self.assertEqual(inventory['catalogue_entries'],3);self.assertEqual(inventory['unique_original_contents'],2);self.assertEqual(inventory['duplicate_records'],1)
        self.assertEqual({p['id'] for p in self.r.list()['items']},{a,b,c});self.assertEqual(self.r.detail(a)['duplicate_count'],1)
    def test_complete_original_beyond_preview_has_stable_character_navigation(self):
        raw=('CHAPTER I\n'+'First chapter text\n'*1200+'\nCHAPTER II\nSecond chapter Ω and café\n').encode();key=self.ingest(raw)
        first=self.r.read(key);second=self.r.read(key,offset=first['next_offset']);self.assertEqual(first['source_text']+second['source_text'],raw.decode())
        self.assertFalse(first['whole_original_supplied']);self.assertTrue(first['range_is_excerpt'])
        self.assertTrue(self.r.find(key,'Second chapter')['found']);self.assertEqual(len(self.r.outline(key)['items']),2);self.assertEqual(self.memory.original(key),raw)
    def test_metadata_search_filters_and_pagination_do_not_read_originals(self):
        for i in range(7):self.ingest(str(i).encode(),'Manual '+str(i)+'.md','text/markdown')
        self.memory.original_chunks=lambda key:(_ for _ in ()).throw(AssertionError('Catalogue must not read original content'))
        page=self.r.list('manual markdown',limit=3);self.assertEqual(page['total'],7);self.assertEqual(len(page['items']),3);self.assertEqual(self.r.list(after=3,limit=3)['next_cursor'],6)
    def test_catalogue_does_not_need_large_extracted_text_payload_or_tail_columns(self):
        import sqlite3
        key=self.ingest(('large text\n'*10000).encode())
        def authorize(action,table,column,*rest):
            return sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_READ and (table=='texts' and column in {'text','status'} or table=='blobs' and column=='body') else sqlite3.SQLITE_OK
        self.memory.db.set_authorizer(authorize)
        try:self.assertEqual(self.r.list()['items'][0]['id'],key)
        finally:self.memory.db.set_authorizer(None)
    def test_html_xml_are_inert_and_raw_source_stays_available(self):
        key=self.ingest(b'<h1>Chapter</h1><script>do_bad()</script><p>Readable</p>','a.html','text/html')
        self.assertNotIn('do_bad',self.r.read(key)['text']);self.assertIn('<script>',self.r.read(key,raw=True)['text']);self.assertEqual(self.memory.original(key),b'<h1>Chapter</h1><script>do_bad()</script><p>Readable</p>')
    def test_zip_members_are_not_extracted_to_the_host_and_unsafe_names_are_visible(self):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:z.writestr('chapters/one.txt','Chapter one');z.writestr('../escape.txt','unsafe');z.writestr('animation.swf','inert')
        key=self.ingest(data.getvalue(),'book.zip','application/zip');opened=self.r.open(key);self.assertEqual(len(opened['members']),3);self.assertFalse(opened['members'][1]['readable']);self.assertEqual(self.r.read(key,member='chapters/one.txt')['text'],'Chapter one')
        with self.assertRaises(ValueError):self.r.member(key,'../escape.txt')
        self.assertFalse((self.root/'escape.txt').exists())
    def test_tar_links_and_duplicate_members_are_not_followed(self):
        raw=io.BytesIO()
        with tarfile.open(fileobj=raw,mode='w:gz') as archive:
            info=tarfile.TarInfo('link.txt');info.type=tarfile.SYMTYPE;info.linkname='/etc/passwd';archive.addfile(info)
            for _ in range(2):info=tarfile.TarInfo('same.txt');info.size=1;archive.addfile(info,io.BytesIO(b'x'))
        key=self.ingest(raw.getvalue(),'book.tar.gz','application/x-gzip');members=self.r.open(key)['members'];self.assertFalse(members[0]['safe'])
        for name in ('link.txt','same.txt'):
            with self.assertRaises(ValueError):self.r.member(key,name)
    def test_ncbi_molecular_source_requires_real_header_and_is_inert_complete_text(self):
        source='Ncbi-mime-asn1 ::= strucseqs {\n'+'  description "Original molecular data"\n'*600+'}\n';data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as archive:
            archive.writestr('molecule.prt',source);archive.writestr('unknown-cad.prt',b'\xff\x00 binary CAD')
        key=self.ingest(data.getvalue(),'Sources.zip','application/zip');members=self.r.open(key)['members']
        self.assertEqual(members[0]['format'],'NCBI ASN.1');self.assertIn('no 3D',members[0]['note']);self.assertTrue(members[0]['readable']);self.assertFalse(members[1]['readable'])
        first=self.r.read(key,member='molecule.prt');last=self.r.read(key,member='molecule.prt',offset=first['next_offset']);self.assertEqual(first['source_text']+last['source_text'],source)
        with self.assertRaises(ValueError):self.r.member(key,'unknown-cad.prt')
    def test_epub_spine_order_and_complete_inert_chapter_source(self):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:
            z.writestr('META-INF/container.xml','<container><rootfiles><rootfile full-path="book/content.opf"/></rootfiles></container>')
            z.writestr('book/content.opf','<package><manifest><item id="second" href="two.xhtml"/><item id="first" href="one.xhtml"/></manifest><spine><itemref idref="first"/><itemref idref="second"/></spine></package>')
            z.writestr('book/two.xhtml','<h1>Chapter two</h1><p>Last chapter text.</p>');z.writestr('book/one.xhtml','<h1>Chapter one</h1><p>First chapter text.</p>')
        key=self.ingest(data.getvalue(),'Book.epub','application/epub+zip');opened=self.r.open(key)
        self.assertEqual([p['name'] for p in opened['members'][:2]],['book/one.xhtml','book/two.xhtml']);chapter=self.r.read(key,member='book/two.xhtml');self.assertIn('Last chapter text.',chapter['text']);self.assertTrue(chapter['whole_original_supplied'])
    def test_position_bookmark_collection_persist_across_reopen(self):
        key=self.ingest();collection=self.r.collection('Reference',approved=True);self.r.membership(collection['id'],key,approved=True)
        self.r.position(key,offset=3,font_size=16,scroll=.25);self.r.position(key,offset=3,bookmark='Important')
        fresh=Resources(self.memory);self.addCleanup(fresh.close);self.assertEqual(fresh.state(key)['offset'],3);self.assertEqual(fresh.state(key)['scroll'],.25);self.assertEqual(len(fresh.bookmarks(key)),1);self.assertEqual(fresh.list(collection=collection['id'])['total'],1)
        self.r.membership(collection['id'],key,included=False,approved=True);self.assertEqual(self.r.list(collection=collection['id'])['total'],0)
    def test_manual_revision_retains_complete_source_and_custom_sections(self):
        first=self.r.manual('My manual',[{'title':'Unusual topic','body':'Original instructions','level':1}],approved=True)
        second=self.r.manual('My manual',[{'title':'New heading','body':'Revised instructions','level':2}],manual_id=first['manual']['id'],revision=first['manual']['revision'],approved=True)
        self.assertIn(b'Original instructions',self.memory.original(first['resource_id']));self.assertIn(b'Revised instructions',self.memory.original(second['resource_id']));self.assertEqual(self.memory.event(second['resource_id'])['parent_id'],first['resource_id'])
        with self.assertRaises(ValueError):self.r.manual('Bad',[{'title':'a','body':'b','level':1}],manual_id=first['manual']['id'],revision=first['manual']['revision'],approved=True)
    def test_future_model_boundary_cannot_write_or_dispatch_arbitrary_operations(self):
        key=self.ingest();app=Application(self.memory);app.resources=self.r
        for op in ('resource_position','resource_manual_save','ingest','library_reset_index'):
            with self.assertRaises(PermissionError):read_tool(app,{'operation':op,'parameters':{'id':key}})
        self.assertEqual(read_tool(app,{'operation':'resource_list','parameters':{}})['total'],1)
    def test_unsupported_source_is_accounted_for_and_does_not_block_other_reading(self):
        bad=self.ingest(b'not executable','unknown.bin','application/octet-stream');good=self.ingest()
        self.assertEqual(self.r.open(bad)['kind'],'unsupported');self.assertEqual(len(self.r.inventory()['unsupported']),1);self.assertEqual(self.r.read(good)['text'],'Original text')
    def test_original_corruption_is_never_replaced_by_cached_or_indexed_text(self):
        file=self.root/'source.txt';file.write_text('exact content');key=self.memory.ingest_file(file,media_type='text/plain')['event_id'];self.r.read(key)
        row=self.memory.db.execute('SELECT * FROM managed_objects').fetchone()
        from vector_core.storage import object_path
        path=object_path(self.memory.config.data_dir,row['digest']);path.write_bytes(b'damaged')
        with self.assertRaises((ValueError,OSError)):self.r.read(key)
    def test_portable_restore_preserves_library_state_and_old_originals(self):
        from vector_core.portable import export_vector,restore_vector
        key=self.ingest();self.r.position(key,offset=4);self.r.position(key,bookmark='Bookmark');c=self.r.collection('Books',approved=True);self.r.membership(c['id'],key,approved=True)
        export_vector(self.memory,self.root/'backup');config=Config.load(data_dir=str(self.root/'restored'));restore_vector(config,self.root/'backup')
        with Memory(config) as memory:
            r=Resources(memory)
            try:self.assertEqual(r.state(key)['offset'],4);self.assertEqual(len(r.bookmarks(key)),1);self.assertEqual(r.list(collection=c['id'])['total'],1);self.assertEqual(memory.original(key),b'Original text')
            finally:r.close()

class ReaderIsolationTests(unittest.TestCase):
    def test_original_pdf_bookmark_destinations_and_text_are_read_not_executed(self):
        from vector_core.reader_runtime import launch_reader
        transport=launch_reader()
        with tempfile.TemporaryDirectory() as temp,Memory(Config.load(data_dir=str(Path(temp)/'data'))) as memory:
            key=memory.ingest(Submission(pdf_bytes(4,outline=True),'Original PDF outline.pdf','application/pdf'))['event_id'];r=Resources(memory,transport)
            try:
                outline=r.outline(key);self.assertEqual(outline['items'][0]['title'],'Last chapter');self.assertEqual(outline['items'][0]['page'],4)
                path=r.stage(key);text=transport.request({'operation':'text','token':path.name,'page':4,'offset':0},10);self.assertIn('Library page 4',text['text'])
                bad=memory.ingest(Submission(b'%PDF-1.4 not a valid document','Damaged.pdf','application/pdf'))['event_id']
                with self.assertRaises(ValueError):r.open(bad)
                self.assertTrue(transport.qualified);self.assertEqual(r.read(key,page=4,width=600)['page'],4)
            finally:r.close()
    def test_actual_isolated_pdf_page_1000_network_denial_and_cleanup(self):
        from vector_core.reader_runtime import launch_reader
        transport=launch_reader();group=Path(transport.report['cgroup']);self.addCleanup(transport.close)
        self.assertTrue(all(transport.report['network_denied'].values()));self.assertTrue(transport.report['inputs_readonly']);self.assertTrue(transport.report['no_subprocesses']);self.assertEqual(transport.report['memory_swap_max'],0)
        with tempfile.TemporaryDirectory() as temp,Memory(Config.load(data_dir=str(Path(temp)/'data'))) as memory:
            source=memory.ingest(Submission(pdf_bytes(1000),'Thousand pages.pdf','application/pdf'));r=Resources(memory,transport)
            try:
                self.assertEqual(r.open(source['event_id'])['pages'],1000);image=r.read(source['event_id'],page=1000,width=600);self.assertEqual(image['page'],1000);self.assertTrue(Path(image['image_path']).is_file());self.assertLess(image['bytes'],16*1024*1024)
                with self.assertRaises(ValueError):transport.request({'operation':'open','token':'../etc/passwd'},5)
                self.assertTrue(transport.qualified);self.assertEqual(r.read(source['event_id'],page=1,width=600)['page'],1)
            finally:r.close()
        self.assertTrue(not group.exists() or (group/'pids.current').read_text().strip()=='0')

if __name__=='__main__':unittest.main()
