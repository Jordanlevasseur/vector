"""Qualified offline Poppler/Cairo reader. No commands, sockets or original mounts."""
import ctypes as C
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from vector_core.storage import safe_path,input_file

class PDF:
    def __init__(self):
        self.p=C.CDLL('libpoppler-glib.so.8');self.c=C.CDLL('libcairo.so.2');self.g=C.CDLL('libgobject-2.0.so.0');self.glib=C.CDLL('libglib-2.0.so.0')
        def signature(lib,name,result,args):f=getattr(lib,name);f.restype=result;f.argtypes=args;return f
        ptr=C.c_void_p;integer=C.c_int;double=C.c_double
        signature(self.p,'poppler_get_version',C.c_char_p,[])
        signature(self.p,'poppler_document_new_from_file',ptr,[C.c_char_p,C.c_char_p,C.POINTER(ptr)])
        signature(self.p,'poppler_document_get_n_pages',integer,[ptr]);signature(self.p,'poppler_document_get_page',ptr,[ptr,integer])
        signature(self.p,'poppler_page_get_size',None,[ptr,C.POINTER(double),C.POINTER(double)])
        signature(self.p,'poppler_page_render',None,[ptr,ptr]);signature(self.p,'poppler_page_get_text',ptr,[ptr])
        signature(self.p,'poppler_index_iter_new',ptr,[ptr]);signature(self.p,'poppler_index_iter_get_action',ptr,[ptr]);signature(self.p,'poppler_index_iter_get_child',ptr,[ptr]);signature(self.p,'poppler_index_iter_next',integer,[ptr]);signature(self.p,'poppler_index_iter_free',None,[ptr]);signature(self.p,'poppler_action_free',None,[ptr]);signature(self.p,'poppler_document_find_dest',ptr,[ptr,C.c_char_p]);signature(self.p,'poppler_dest_free',None,[ptr])
        signature(self.g,'g_object_unref',None,[ptr]);signature(self.glib,'g_free',None,[ptr]);signature(self.glib,'g_error_free',None,[ptr])
        signature(self.c,'cairo_image_surface_create',ptr,[integer,integer,integer]);signature(self.c,'cairo_surface_status',integer,[ptr])
        signature(self.c,'cairo_create',ptr,[ptr]);signature(self.c,'cairo_set_source_rgb',None,[ptr,double,double,double]);signature(self.c,'cairo_paint',None,[ptr]);signature(self.c,'cairo_scale',None,[ptr,double,double]);signature(self.c,'cairo_destroy',None,[ptr]);signature(self.c,'cairo_surface_destroy',None,[ptr]);signature(self.c,'cairo_surface_write_to_png',integer,[ptr,C.c_char_p])
        self.image=C.CDLL('libgdk_pixbuf-2.0.so.0')
        signature(self.image,'gdk_pixbuf_new_from_file_at_scale',ptr,[C.c_char_p,integer,integer,integer,C.POINTER(ptr)])
        signature(self.image,'gdk_pixbuf_apply_embedded_orientation',ptr,[ptr])
        signature(self.image,'gdk_pixbuf_savev',integer,[ptr,C.c_char_p,C.c_char_p,ptr,ptr,C.POINTER(ptr)])
        signature(self.image,'gdk_pixbuf_get_width',integer,[ptr]);signature(self.image,'gdk_pixbuf_get_height',integer,[ptr])
        self.doc=None;self.token=None;self.count=0
    def open(self,token):
        if not isinstance(token,str) or not re.fullmatch('[0-9a-f]{64}',token):raise ValueError('Invalid verified reader handle.')
        if token==self.token:return {'pages':self.count,'runtime':self.p.poppler_get_version().decode()}
        path=Path('/inputs')/token
        if path.is_symlink() or not path.is_file() or path.stat().st_size>128*1024*1024:raise ValueError('Reader input missing or exceeds 128 MiB working-file limit.')
        with input_file(path) as handle:
            if handle.read(5)!=b'%PDF-':raise ValueError('Selected source is not a PDF.')
        if self.doc:self.g.g_object_unref(self.doc);self.doc=None;self.token=None
        error=C.c_void_p();doc=self.p.poppler_document_new_from_file(path.as_uri().encode(),None,C.byref(error))
        if not doc:
            class Error(C.Structure):_fields_=[('domain',C.c_uint),('code',C.c_int),('message',C.c_char_p)]
            message=C.cast(error,C.POINTER(Error)).contents.message.decode('utf-8','replace')[:1000] if error else 'Unknown Poppler error'
            if error:self.glib.g_error_free(error)
            raise ValueError('PDF could not be opened: '+message)
        self.doc=doc;self.token=token;self.count=self.p.poppler_document_get_n_pages(doc)
        if not 1<=self.count<=1000000:raise ValueError('PDF contains no supported pages.')
        return {'pages':self.count,'runtime':self.p.poppler_get_version().decode()}
    def page(self,token,page):
        self.open(token)
        if type(page) is not int or not 1<=page<=self.count:raise ValueError('PDF page outside document.')
        p=self.p.poppler_document_get_page(self.doc,page-1)
        if not p:raise ValueError('PDF page unavailable.')
        return p
    def text(self,token,page):
        p=self.page(token,page)
        try:
            pointer=self.p.poppler_page_get_text(p)
            if not pointer:return ''
            try:return C.string_at(pointer).decode('utf-8','replace')
            finally:self.glib.g_free(pointer)
        finally:self.g.g_object_unref(p)
    def outline(self,token):
        self.open(token);items=[]
        class Destination(C.Structure):
            _fields_=[('type',C.c_int),('page_num',C.c_int),('left',C.c_double),('bottom',C.c_double),('right',C.c_double),('top',C.c_double),('zoom',C.c_double),('named_dest',C.c_char_p)]
        class Action(C.Structure):_fields_=[('type',C.c_int),('title',C.c_char_p),('dest',C.POINTER(Destination))]
        def walk(iterator,level):
            if not iterator:return
            try:
                while len(items)<1000:
                    pointer=self.p.poppler_index_iter_get_action(iterator)
                    if pointer:
                        try:
                            action=C.cast(pointer,C.POINTER(Action)).contents;page=None
                            if action.type==2 and action.dest:
                                dest=action.dest.contents;candidate=dest.page_num
                                if not 1<=candidate<=self.count and dest.named_dest:
                                    resolved=self.p.poppler_document_find_dest(self.doc,dest.named_dest)
                                    if resolved:
                                        try:candidate=C.cast(resolved,C.POINTER(Destination)).contents.page_num
                                        finally:self.p.poppler_dest_free(resolved)
                                if 1<=candidate<=self.count:page=candidate
                            items.append({'title':(action.title or b'Untitled section').decode('utf-8','replace')[:200],'page':page,'level':level,'reason':'' if page else 'Nonlocal or unresolved destination; no action is executed.'})
                        finally:self.p.poppler_action_free(pointer)
                    child=self.p.poppler_index_iter_get_child(iterator)
                    if child:
                        if level<12:walk(child,level+1)
                        else:self.p.poppler_index_iter_free(child)
                    if not self.p.poppler_index_iter_next(iterator):break
            finally:self.p.poppler_index_iter_free(iterator)
        walk(self.p.poppler_index_iter_new(self.doc),1)
        return {'items':items,'truncated':len(items)>=1000,'method':'Original PDF bookmarks; only internal verified page destinations are navigable.'}
    def render(self,token,page,width):
        if type(width) is not int or not 400<=width<=1600:raise ValueError('PDF width must be 400–1600 pixels.')
        p=self.page(token,page);surface=None;context=None
        try:
            w=C.c_double();h=C.c_double();self.p.poppler_page_get_size(p,C.byref(w),C.byref(h))
            if not 0<w.value<100000 or not 0<h.value<100000:raise ValueError('Invalid PDF dimensions.')
            height=max(1,round(width*h.value/w.value))
            if height>5000 or width*height>8000000:raise ValueError('Page aspect ratio exceeds the bounded renderer; reduce zoom or export the original.')
            surface=self.c.cairo_image_surface_create(1,width,height)
            if self.c.cairo_surface_status(surface):raise ValueError('Cairo page allocation failed.')
            context=self.c.cairo_create(surface);self.c.cairo_set_source_rgb(context,1,1,1);self.c.cairo_paint(context);self.c.cairo_scale(context,width/w.value,width/w.value);self.p.poppler_page_render(p,context)
            # Three raster pages maximum; never render a whole book eagerly.
            outputs=Path('/outputs')
            for old in sorted(outputs.glob('*.png'),key=lambda p:p.stat().st_mtime_ns)[:-2]:old.unlink()
            name=token+'-'+str(page)+'-'+str(width)+'.png';path=outputs/name
            if self.c.cairo_surface_write_to_png(surface,str(path).encode()):raise ValueError('Page image could not be written.')
            path.chmod(0o600)
            if path.stat().st_size>16*1024*1024:path.unlink();raise ValueError('Rendered page exceeds bounded image size.')
            with path.open('rb') as handle:digest=hashlib.file_digest(handle,'sha256').hexdigest()
            return {'kind':'pdf','page':page,'pages':self.count,'width':width,'height':height,'image':name,'sha256':digest,'bytes':path.stat().st_size}
        finally:
            if context:self.c.cairo_destroy(context)
            if surface:self.c.cairo_surface_destroy(surface)
            self.g.g_object_unref(p)
    def render_image(self,token,width):
        if not isinstance(token,str) or not re.fullmatch('[0-9a-f]{64}',token) or type(width) is not int or not 400<=width<=1600:raise ValueError('Invalid image handle/width.')
        path=Path('/inputs')/token
        if path.is_symlink() or path.stat().st_size>128*1024*1024:raise ValueError('Image exceeds the reader working-file budget.')
        error=C.c_void_p();pix=self.image.gdk_pixbuf_new_from_file_at_scale(str(path).encode(),width,4000,1,C.byref(error))
        if not pix:
            if error:self.glib.g_error_free(error)
            raise ValueError('Image format is unsupported or damaged.')
        try:
            # Apply camera orientation to the already bounded display bitmap,
            # never to the preserved image and never at original resolution.
            oriented=self.image.gdk_pixbuf_apply_embedded_orientation(pix)
            if not oriented:raise ValueError('Embedded image orientation could not be applied.')
            self.g.g_object_unref(pix);pix=oriented
            output=Path('/outputs')/(token+'-1-'+str(width)+'.png')
            if not self.image.gdk_pixbuf_savev(pix,str(output).encode(),b'png',None,None,C.byref(error)):
                if error:self.glib.g_error_free(error)
                raise ValueError('Image could not be rendered.')
            output.chmod(0o600)
            if output.stat().st_size>16*1024*1024:output.unlink();raise ValueError('Image exceeds output budget.')
            for old in sorted(Path('/outputs').glob('*.png'),key=lambda p:p.stat().st_mtime_ns)[:-3]:old.unlink()
            with output.open('rb') as h:digest=hashlib.file_digest(h,'sha256').hexdigest()
            return {'kind':'image','display_orientation':'embedded-orientation-applied','page':1,'pages':1,'width':self.image.gdk_pixbuf_get_width(pix),'height':self.image.gdk_pixbuf_get_height(pix),'image':output.name,'sha256':digest,'bytes':output.stat().st_size}
        finally:self.g.g_object_unref(pix)

def worker():
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
    pdf=PDF()
    from vector_core.security import activate
    policy=activate()
    for raw in iter(lambda:sys.stdin.buffer.readline(65537),b''):
        try:
            if len(raw)>65536 or not raw.endswith(b'\n'):raise ValueError('Reader frame exceeds limit.')
            from vector_core.portable import unique
            p=json.loads(raw,object_pairs_hook=unique);operation=p.get('operation')
            if operation=='qualify':
                readonly=False
                try:Path('/inputs/forbidden-write').write_bytes(b'no')
                except OSError:readonly=True
                fork_denied=False
                try:
                    child=os.fork()
                    if child==0:os._exit(0)
                    os.waitpid(child,0)
                except PermissionError:fork_denied=True
                result={**policy,'runtime_version':'Poppler '+pdf.p.poppler_get_version().decode(),'network_namespace':str(Path('/proc/self/ns/net').readlink()),'routes':len(Path('/proc/net/route').read_text().splitlines())>1,'host_home_absent':not Path('/home/mint').exists(),'inputs_readonly':readonly,'no_subprocesses':fork_denied,'file_size_max':resource.getrlimit(resource.RLIMIT_FSIZE)[0],'fd_max':resource.getrlimit(resource.RLIMIT_NOFILE)[0]}
            elif operation=='open' and set(p)=={'operation','token'}:result=pdf.open(p['token'])
            elif operation=='render' and set(p)=={'operation','token','page','width'}:result=pdf.render(p['token'],p['page'],p['width'])
            elif operation=='outline' and set(p)=={'operation','token'}:result=pdf.outline(p['token'])
            elif operation=='text' and set(p)=={'operation','token','page','offset'}:
                if type(p['offset']) is not int or not 0<=p['offset']<=2**32:raise ValueError('Invalid page text offset.')
                text=pdf.text(p['token'],p['page']);start=p['offset'];result={'text':text[start:start+16000],'page':p['page'],'start':start,'end':min(len(text),start+16000),'next_offset':start+16000 if start+16000<len(text) else None,'qualification':'Poppler page text derived from the verified original PDF; layout and meaning are not certified.'}
            elif operation=='image' and set(p)=={'operation','token','width'}:result=pdf.render_image(p['token'],p['width'])
            elif operation=='image_chunk' and set(p)=={'operation','name','offset'}:
                if not isinstance(p['name'],str) or not re.fullmatch(r'[0-9a-f]{64}-\d+-\d+\.png',p['name']) or type(p['offset']) is not int or not 0<=p['offset']<=16*1024*1024:raise ValueError('Invalid bounded image chunk.')
                with input_file(Path('/outputs')/p['name']) as stream:stream.seek(p['offset']);result={'data':base64.b64encode(stream.read(65536)).decode('ascii')}
            elif operation=='find' and set(p)=={'operation','token','page','query'}:
                if not isinstance(p['query'],str) or not 1<=len(p['query'])<=200:raise ValueError('Invalid PDF query.')
                pdf.open(p['token']);first=p['page']
                if type(first) is not int or not 1<=first<=pdf.count:raise ValueError('Invalid PDF search page.')
                result={'found':False,'incomplete':first+20<=pdf.count,'next_page':min(pdf.count,first+20)}
                for page in range(first,min(pdf.count+1,first+20)):
                    text=pdf.text(p['token'],page);match=re.search(re.escape(p['query']),text,re.I)
                    if match:result={'found':True,'page':page,'excerpt':text[max(0,match.start()-80):match.end()+160]};break
            else:raise ValueError('Unknown reader operation or fields; no commands are accepted.')
            response={'ok':True,'result':result}
        except (ValueError,OSError,RuntimeError) as error:response={'ok':True,'result':{'reader_error':str(error)[:2000]}}
        sys.stdout.buffer.write(json.dumps(response,allow_nan=False).encode()+b'\n');sys.stdout.buffer.flush()

def launch_reader():
    """Trusted startup only, before the core's no-exec policy; no original mounts."""
    from vector_core.worker_launcher import WorkerTransport
    class ReaderTransport(WorkerTransport):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.reader_resources={};self.next_monitor=0
        def _check(self,end,cancellation):
            super()._check(end,cancellation)
            if self.report.get('cgroup') and time.monotonic()>=self.next_monitor:
                self.next_monitor=time.monotonic()+.25
                from vector_core.inference import InferenceError
                try:
                    group=Path(self.report['cgroup']);available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
                    events={k:int(v) for k,v in (l.split() for l in (group/'memory.events').read_text().splitlines())}
                    self.reader_resources={'memory_peak':int((group/'memory.peak').read_text()),'memory_current':int((group/'memory.current').read_text()),'swap_current':int((group/'memory.swap.current').read_text()),'host_available':available,'memory_events':events}
                    if available<384*1024*1024 or self.reader_resources['swap_current'] or events.get('oom_kill'):raise InferenceError('Reader resource protection: '+json.dumps(self.reader_resources),code='READER_RESOURCE_LIMIT',stage='library-renderer')
                except (OSError,ValueError,StopIteration) as error:raise InferenceError('Reader memory monitor failed closed: '+str(error),code='READER_MONITOR_FAILED',stage='library-renderer') from error
        def request(self,*args,**kwargs):
            try:result=super().request(*args,**kwargs)
            except BaseException:
                self.close();raise
            if isinstance(result,dict) and 'reader_error' in result:raise ValueError(result['reader_error'])
            if isinstance(result,dict) and self.reader_resources:result['reader_resources']=dict(self.reader_resources)
            return result
    binary={}
    for name in ('bwrap','systemd-run','systemctl'):
        found=shutil.which(name)
        if not found:raise RuntimeError('Offline PDF reader requires installed '+name)
        path=Path(found).resolve()
        if not str(path).startswith('/usr/bin/') or path.stat().st_uid!=0 or path.stat().st_mode&0o022:raise RuntimeError('Untrusted reader launcher: '+name)
        binary[name]=str(path)
    tmp=tempfile.TemporaryDirectory(prefix='vector_reader_');cache=Path(tmp.name)
    for name in ('inputs','outputs'):(cache/name).mkdir(mode=0o700)
    unit='vector-reader-'+uuid4().hex;memory=512*1024*1024;tasks=32
    environment={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid()),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus','LC_ALL':'C.UTF-8'}
    command=[binary['systemd-run'],'--user','--scope','--quiet','--unit='+unit,'--property=MemoryMax='+str(memory),'--property=MemorySwapMax=0','--property=TasksMax='+str(tasks),'--property=CPUQuota=100%',binary['bwrap'],'--unshare-all','--unshare-user','--disable-userns','--assert-userns-disabled','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--size','67108864','--tmpfs','/tmp','--dir','/tmp/home','--ro-bind',str(cache/'inputs'),'/inputs','--size','67108864','--tmpfs','/outputs','--ro-bind',str(Path(__file__).parent),'/application/vector_core','--setenv','HOME','/tmp/home','--setenv','PATH','/usr/bin:/bin','--setenv','PYTHONPATH','/application','--setenv','PYTHONDONTWRITEBYTECODE','1','--chdir','/tmp','/usr/bin/python3','-B','-m','vector_core.reader_runtime','--worker']
    for source in ('/etc/fonts','/var/cache/fontconfig'):
        if Path(source).is_dir():at=command.index('--proc');command[at:at]=['--ro-bind',source,source]
    if Path('/usr/share/ollama').exists():at=command.index('--proc');command[at:at]=['--size','4096','--tmpfs','/usr/share/ollama']
    diagnostic=tempfile.TemporaryFile();transport=None
    try:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=diagnostic,bufsize=0,env=environment,start_new_session=True)
        transport=ReaderTransport(process,{'runtime_version':'unqualified reader'});report=transport.request({'operation':'qualify'},30)
        if report['network_namespace']==str(Path('/proc/self/ns/net').readlink()) or report['routes'] or not all(report['network_denied'].values()) or not report['host_home_absent'] or not report['inputs_readonly'] or not report['no_subprocesses']:raise RuntimeError('Reader namespace, offline or filesystem qualification failed.')
        shown=subprocess.run([binary['systemctl'],'--user','show',unit+'.scope','--property=ControlGroup'],capture_output=True,text=True,timeout=5,check=True,env=environment)
        group=Path('/sys/fs/cgroup')/shown.stdout.strip().split('=',1)[1].lstrip('/')
        if int((group/'memory.max').read_text())!=memory or int((group/'memory.swap.max').read_text())!=0 or int((group/'pids.max').read_text())!=tasks:raise RuntimeError('Reader resource limits not enforced.')
        quota,period=(group/'cpu.max').read_text().split()
        if quota=='max' or int(quota)>int(period):raise RuntimeError('Reader CPU limit not enforced.')
        report.update(cgroup=str(group),unit=unit,memory_max=memory,pids_max=tasks,memory_swap_max=0,cpu_max=(group/'cpu.max').read_text().strip())
        transport.report=report;transport.runtime_version=report['runtime_version'];transport.cache=cache;transport.temporary=tmp
        return transport
    except Exception as error:
        diagnostic.seek(0);detail=diagnostic.read(4096).decode('utf-8','replace')
        if transport:transport.close()
        tmp.cleanup();raise RuntimeError('Local PDF reader unavailable: '+str(error)+' '+detail) from error
    finally:diagnostic.close()

if __name__=='__main__':
    if sys.argv[1:]!=['--worker']:raise SystemExit('Reader is started only by qualified local desktop startup.')
    worker()
