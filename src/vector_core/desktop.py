"""Lightweight Tk desktop over a separately kernel-guarded application backend."""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import time
from uuid import uuid4

class Client:
    def __init__(self,process):
        self.process=process;self.pending=None;self.output=b'';self.input=b'';self.on_progress=None
        os.set_blocking(process.stdin.fileno(),False);os.set_blocking(process.stdout.fileno(),False)
    def start(self,operation,parameters,callback):
        if self.pending:raise RuntimeError('An operation is already running; wait or cancel it.')
        identifier=uuid4().hex
        frame=json.dumps({'id':identifier,'operation':operation,'parameters':parameters},allow_nan=False).encode()+b'\n'
        if len(frame)>65536:raise ValueError('Desktop request too large; import a file instead.')
        self.pending=(identifier,callback);self.output=frame
    def poll(self):
        if self.output and select.select([],[self.process.stdin],[],0)[1]:
            try:self.output=self.output[os.write(self.process.stdin.fileno(),self.output):]
            except BlockingIOError:pass
        if select.select([self.process.stdout],[],[],0)[0]:
            chunk=os.read(self.process.stdout.fileno(),65536)
            if not chunk:raise RuntimeError('Application channel closed. Restart VECTOR.')
            self.input+=chunk
            if len(self.input)>1024*1024:raise RuntimeError('Application response exceeds limit.')
        if b'\n' not in self.input and self.process.poll() is not None:raise RuntimeError('Application backend stopped. Restart VECTOR; committed data remains recoverable.')
        if b'\n' in self.input:
            raw,self.input=self.input.split(b'\n',1);response=json.loads(raw)
            if isinstance(response,dict) and set(response)=={'startup_progress'}:
                label=response['startup_progress']
                if not isinstance(label,str) or len(label)>500:raise RuntimeError('Invalid startup progress frame.')
                if self.on_progress:self.on_progress({'phase':'startup','label':label})
                return
            if response.get('initialization_error'):raise RuntimeError('VECTOR startup blocked: '+str(response['result']))
            if not self.pending or response.get('id')!=self.pending[0]:raise RuntimeError('Application response identity mismatch.')
            if 'progress' in response:
                if self.on_progress:self.on_progress(response['progress'])
                return
            callback=self.pending[1];self.pending=None;callback(response)
    def cancel(self):
        if self.pending:
            try:os.kill(self.process.pid,signal.SIGUSR1)
            except ProcessLookupError:pass
    def close(self):
        self.process.stdin.close()
        try:self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:self.process.terminate()
        self.process.stdout.close()


def bootstrap(args):
    import tkinter as tk
    from tkinter import filedialog
    import re
    if not re.fullmatch(r':\d+(?:\.\d+)?',os.environ.get('DISPLAY','')):raise RuntimeError('A local X11 display is required; remote displays are refused before connection.')
    before=set(os.listdir('/proc/self/fd'))
    root=tk.Tk();root.withdraw();root.update()
    if args.choose_data:
        selected=filedialog.askdirectory(parent=root,title='Open a private VECTOR data folder')
        if not selected:root.destroy();return None,None
        args.data_dir=selected
    if args.choose_models:
        selected=filedialog.askdirectory(parent=root,title='Select local Ollama models folder (contains blobs and manifests)')
        if not selected:root.destroy();return None,None
        args.models_directory=selected
    display=[];new_pipes=[]
    for name in os.listdir('/proc/self/fd'):
        fd=int(name)
        try:
            mode=os.fstat(fd).st_mode
            if stat.S_ISFIFO(mode) and name not in before and fd>2:new_pipes.append(fd)
            if stat.S_ISSOCK(mode):
                handle=socket.fromfd(fd,socket.AF_UNIX,socket.SOCK_STREAM)
                try:
                    peer=handle.getpeername()
                    if isinstance(peer,bytes):peer=os.fsdecode(peer)
                    if isinstance(peer,str) and peer.lstrip('\0').startswith('/tmp/.X11-unix/X'):display.append(fd)
                finally:handle.close()
        except OSError:continue
    if len(display)!=1:root.destroy();raise RuntimeError('Exactly one local X11 connection required; remote or ambiguous displays are refused.')
    command=[sys.executable,'-m','vector_core.desktop_worker']
    if args.data_dir:command+=['--data-dir',args.data_dir]
    if args.models_directory:command+=['--models-directory',args.models_directory]
    if args.managed:command+=['--managed']
    if getattr(args,'no_inference',False):command+=['--no-inference']
    if getattr(args,'runtime_profile',None):command+=['--runtime-profile',args.runtime_profile]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
    from vector_core.security import activate
    try:activate(pipe_fds=(*new_pipes,process.stdin.fileno(),process.stdout.fileno()),display_fd=display[0])
    except Exception:process.terminate();root.destroy();raise
    return root,Client(process)

class Desktop:
    def __init__(self,root,client,*,managed=False):
        import tkinter as tk
        from tkinter import ttk,messagebox,filedialog,simpledialog
        from tkinter.scrolledtext import ScrolledText
        self.tk=tk;self.ttk=ttk;self.dialog=messagebox;self.files=filedialog;self.simple=simpledialog
        self.root=root;self.client=client;self.managed=managed;self.last_response=None;self.selected_event=None;self.selected_claim=None;self.selected_source_id=None;self.claim_cursor=''
        self.rows={};self.event_cursor='';self.project_cursor=0;self.project_rows={};self.history_cursor=0;self.active_project=None;self.item_rows={};self.editing_item=None
        root.title('VECTOR — Offline Evidence Assistant');root.geometry(str(min(1060,root.winfo_screenwidth()-80))+'x'+str(min(760,root.winfo_screenheight()-100)));root.minsize(820,600)
        from vector_core.desktop_shell import Interface
        self.shell=Interface(self)
        self.client.on_progress=lambda value:self.status.set(value['label'])
        tab=self.tabs['Knowledge'];bar=ttk.Frame(tab);bar.pack(fill='x')
        self.search=ttk.Entry(bar);self.search.pack(side='left',fill='x',expand=True);self.search.bind('<Return>',lambda event:self.search_sources())
        for label,command in [('Search',self.search_sources),('Browse next sources',self.browse),('Claims',self.claims),('Conflicts',lambda:self.call('conflicts',{},self.show_result)),('Override claim',self.override)]:ttk.Button(bar,text=label,command=command).pack(side='left',padx=2)
        filters=ttk.Frame(tab);filters.pack(fill='x',pady=4)
        self.memory_view=tk.StringVar(value='episodic');ttk.Combobox(filters,textvariable=self.memory_view,values=('episodic','semantic','procedural','project','working'),state='readonly',width=12).pack(side='left')
        self.project_only=tk.BooleanVar();ttk.Checkbutton(filters,text='Active project only',variable=self.project_only).pack(side='left')
        self.source_only=tk.BooleanVar();ttk.Checkbutton(filters,text='Selected source only',variable=self.source_only).pack(side='left')
        self.memory_since=ttk.Entry(filters,width=20);self.memory_until=ttk.Entry(filters,width=20)
        for label,entry in [('Since (ISO + zone)',self.memory_since),('Until',self.memory_until)]:ttk.Label(filters,text=label).pack(side='left');entry.pack(side='left')
        ttk.Button(filters,text='Recall memories',command=self.recall_memories).pack(side='left')
        self.knowledge_rights=tk.StringVar(value='');ttk.Label(tab,textvariable=self.knowledge_rights,wraplength=950).pack(fill='x')
        self.knowledge=ttk.Treeview(tab,columns=('title','detail','identity'),show='headings',height=12)
        for name,width in [('title',240),('detail',420),('identity',220)]:self.knowledge.heading(name,text=name.title());self.knowledge.column(name,width=width)
        self.knowledge.pack(fill='both',expand=True,pady=8);self.knowledge.bind('<<TreeviewSelect>>',self.select_source);self.knowledge.bind('<Double-1>',lambda event:self.view_source())
        ttk.Button(tab,text='View selected original / evidence',command=self.view_source).pack(anchor='w')
        ttk.Button(tab,text='Export selected original',command=self.export_original).pack(anchor='w',pady=4)
        ttk.Button(tab,text='Open selected original in Library',command=lambda:self.open_resource_reference(self.selected_event) if self.selected_event else None).pack(anchor='w')
        more=ttk.Frame(tab);more.pack(fill='x')
        for label,command in [('Compare / versions',lambda:self.source_operation('memory_compare')),('Relationships',lambda:self.source_operation('memory_links')),('Link evidence',self.link_evidence),('Assessments',self.assessment_history),('Dispute claim',self.assess_claim),('Entity',self.entity_lookup)]:ttk.Button(more,text=label,command=command).pack(side='left',padx=2)
        tab=self.tabs['Learning'];ttk.Label(tab,text='Import originals or learn explicit subject | predicate | value statements. Sources remain unverified.').pack(anchor='w')
        self.learning=ScrolledText(tab,wrap='word',height=12);self.learning.pack(fill='both',expand=True,pady=8)
        controls=ttk.Frame(tab);controls.pack(fill='x');self.scope=ttk.Entry(controls,width=20);self.scope.insert(0,'personal');self.scope.grid(row=0,column=0,sticky='w')
        self.exclusive=tk.BooleanVar();ttk.Checkbutton(controls,text='Comparable exclusive claims',variable=self.exclusive).grid(row=0,column=1,columnspan=2,sticky='w')
        for index,(label,command) in enumerate([('Archive text',self.archive_text),('Import file',self.import_file),('Learn statements',self.learn_text),('AI proposal from selected source',self.extract_proposal),('Review proposals',self.proposals)]):ttk.Button(controls,text=label,command=command).grid(row=1+index//3,column=index%3,sticky='w',padx=3,pady=4)
        ttk.Button(tab,text='Literary library / linguistics',command=self.open_library).pack(anchor='w')
        ttk.Button(tab,text='Deferred extraction queue',command=lambda:self.paged_records('Deferred learning','learning_queue',lambda r:r['status']+' — '+r['event_id'],lambda r:self.call('show',{'event_id':r['event_id']},self.show_result))).pack(anchor='w')
        ttk.Button(tab,text='Reconcile selected evidence',command=lambda:self.source_operation('reconcile')).pack(anchor='w')
        ttk.Button(tab,text='Selected source learning history',command=lambda:self.source_operation('learning_history')).pack(anchor='w')
        tab=self.tabs['Projects'];bar=ttk.Frame(tab);bar.pack(fill='x');self.project_name=ttk.Entry(bar);self.project_name.pack(side='left',fill='x',expand=True)
        ttk.Button(bar,text='Create project',command=self.create_project).pack(side='left');ttk.Button(bar,text='Load next projects',command=self.projects).pack(side='left');ttk.Button(bar,text='Resume selected',command=self.load_project).pack(side='left')
        self.project_list=tk.Listbox(tab,font=('Sans',12),height=4);self.project_list.pack(fill='x',pady=8)
        self.project_status=tk.StringVar(value='No active project. Global memory remains available.');ttk.Label(tab,textvariable=self.project_status).pack(anchor='w')
        controls=ttk.Frame(tab);controls.pack(fill='x')
        for label,command in [('Link selected source',self.link_selected_project),('Sources',self.project_sources),('History',self.project_history),('Archive / restore',self.archive_project),('Leave project',self.leave_project),('Items',self.project_items)]:ttk.Button(controls,text=label,command=command).pack(side='left',padx=2)
        self.project_item_list=tk.Listbox(tab,height=5);self.project_item_list.pack(fill='both',expand=True,pady=5);self.project_item_list.bind('<<ListboxSelect>>',self.select_project_item)
        form=ttk.Frame(tab);form.pack(fill='x');self.item_kind=tk.StringVar(value='note');self.item_status=tk.StringVar(value='open')
        ttk.Combobox(form,textvariable=self.item_kind,values=('goal','requirement','note','decision','task','milestone','question','hypothesis'),state='readonly',width=13).pack(side='left')
        ttk.Combobox(form,textvariable=self.item_status,values=('open','done','blocked','deferred'),state='readonly',width=10).pack(side='left')
        self.item_title=ttk.Entry(form);self.item_title.pack(side='left',fill='x',expand=True)
        ttk.Button(form,text='New item',command=self.clear_item).pack(side='left');ttk.Button(form,text='Save revision',command=self.save_item).pack(side='left')
        self.item_body=ScrolledText(tab,height=4,wrap='word');self.item_body.pack(fill='x',pady=5)
        ttk.Label(tab,text='Selected Knowledge source is attached as evidence on save. Goals/decisions/hypotheses are user records, not verified facts.').pack(anchor='w')
        tab=self.tabs['Tools'];ttk.Label(tab,text='Deterministic calculations. Clicking Run authorizes this calculation only. No model tool execution.').pack(anchor='w')
        self.tool_name=tk.StringVar(value='arithmetic');combo=ttk.Combobox(tab,textvariable=self.tool_name,values=('arithmetic','convert','solve_linear','geometry','statistics','constant'),state='readonly');combo.pack(anchor='w',pady=8);combo.bind('<<ComboboxSelected>>',lambda e:self.tool_fields())
        self.tool_form=ttk.Frame(tab);self.tool_form.pack(fill='x');self.tool_inputs={};self.tool_fields()
        ttk.Button(tab,text='Run calculation',command=self.run_tool).pack(anchor='w',pady=8)
        self.tool_result=ScrolledText(tab,height=12,wrap='word');self.tool_result.pack(fill='both',expand=True)
        tab=self.tabs['Settings'];ttk.Label(tab,text='Development Mode — manual operation does not depend on accuracy or release readiness.').pack(anchor='w')
        runtime=ttk.LabelFrame(tab,text='Local AI startup / memory',padding=6);runtime.pack(fill='x')
        self.experimental_memory=tk.BooleanVar(value=False);ttk.Checkbutton(runtime,text='Experimental memory estimates (user controlled)',variable=self.experimental_memory).pack(anchor='w')
        line=ttk.Frame(runtime);line.pack(fill='x');ttk.Label(line,text='Manual memory cap (MiB; host checked)').pack(side='left');self.runtime_memory=ttk.Entry(line,width=8);self.runtime_memory.insert(0,'1536');self.runtime_memory.pack(side='left',padx=5)
        self.runtime_apply=ttk.Button(line,text='Save startup options',command=self.save_runtime_options);self.runtime_apply.pack(side='left')
        ttk.Label(runtime,text='Experimental estimates can cause crashes or resource exhaustion. Kernel limits and offline isolation remain enforced. Close and reopen VECTOR after saving.',wraplength=900).pack(anchor='w')
        self.runtime_notice=tk.StringVar();ttk.Label(runtime,textvariable=self.runtime_notice,wraplength=900).pack(anchor='w')
        self.model_status=tk.StringVar(value='No model availability assumed');ttk.Label(tab,textvariable=self.model_status,wraplength=950).pack(anchor='w')
        bar=ttk.Frame(tab);bar.pack(fill='x',pady=8);self.model=tk.StringVar();self.model_box=ttk.Combobox(bar,textvariable=self.model,width=30,state='readonly');self.model_box.pack(side='left')
        self.model_limits={}
        for key,default in [('context',2048),('output',256),('timeout',30)]:
            ttk.Label(bar,text=key.title()).pack(side='left',padx=4);entry=ttk.Entry(bar,width=7);entry.insert(0,str(default));entry.pack(side='left');self.model_limits[key]=entry
        self.select_button=ttk.Button(bar,text='Select model',command=self.select_model,state='disabled');self.select_button.pack(side='left',padx=5)
        ttk.Button(tab,text='Import selected local model into portable storage',command=self.import_model).pack(anchor='w')
        ttk.Label(tab,text='AUTO discovers approved local models and starts protected inference when used. Manual selection is optional.\nModel output is unverified inference; exact citations do not certify its conclusions.',wraplength=950).pack(anchor='w',pady=8)
        from vector_core.model_routing import MODES
        modes=ttk.LabelFrame(tab,text='Conversation models',padding=8);modes.pack(fill='x',pady=8)
        self.default_mode=tk.StringVar(value='Choose model mode');self.default_mode_box=ttk.Combobox(modes,textvariable=self.default_mode,values=tuple(MODES.values()),state='readonly',width=28);self.default_mode_box.grid(row=0,column=0,sticky='w')
        ttk.Button(modes,text='Save default mode',command=self.save_default_mode).grid(row=0,column=1,padx=8)
        self.synthesis_role=tk.StringVar(value='b');ttk.Label(modes,text='Synthesis role').grid(row=1,column=0,sticky='w')
        ttk.Combobox(modes,textvariable=self.synthesis_role,values=('a','b'),state='readonly',width=5).grid(row=1,column=1,sticky='w')
        self.extra_reviews=tk.IntVar(value=0);ttk.Label(modes,text='Additional review rounds (0–2, only unresolved issues)').grid(row=2,column=0,sticky='w')
        ttk.Spinbox(modes,from_=0,to=2,textvariable=self.extra_reviews,width=5).grid(row=2,column=1,sticky='w')
        self.role_names={};self.role_boxes={}
        for i,role in enumerate(('a','b')):
            self.role_names[role]=tk.StringVar();ttk.Label(modes,text='Exact local model for role '+role.upper()).grid(row=3+i,column=0,sticky='w')
            box=ttk.Combobox(modes,textvariable=self.role_names[role],state='readonly',width=36);box.grid(row=3+i,column=1,sticky='w');self.role_boxes[role]=box
        ttk.Button(modes,text='Save model roles and limits',command=self.save_model_settings).grid(row=5,column=0,sticky='w',pady=6)
        ttk.Label(modes,text='The context, output and timeout fields above also configure these modes.\nCalls run sequentially and unload between stages. Both requires five complete calls.\nA model review or agreement does not verify factual correctness.',wraplength=700).grid(row=6,column=0,columnspan=2,sticky='w')
        self.mode_catalog=None;self.model_work_open=False
        actions=ttk.Frame(self.tabs['Tools']);actions.pack(fill='x',pady=4);self.advanced_actions=actions
        for index,(label,command) in enumerate([('Storage usage / available space',lambda:self.call('storage',{},self.show_result)),('Verify originals',lambda:self.call('verify',{},self.show_result)),('Create separate recovery key',self.create_key),('Export VECTOR',self.backup),('Verify backup (actual restore)',self.verify_backup),('Restore to a new folder',self.restore),('Move data location',self.move),('Rebuild search indexes',lambda:self.call('rebuild',{},self.show_result)),('Recover interrupted storage',lambda:self.call('recover_storage',{},self.show_result)),('System / offline diagnostics',lambda:self.call('health',{},self.show_result))]):ttk.Button(actions,text=label,command=command).grid(row=index//2,column=index%2,sticky='ew',padx=4,pady=3)
        self.shell.finish()
        from vector_core.resource_desktop import ResourceDesktop
        self.library=ResourceDesktop(self,self.shell.library_parent)
        self.root.protocol('WM_DELETE_WINDOW',self.close);root.deiconify();root.after(30,self.poll);self.call('health',{},self.health)
    def call(self,operation,parameters,callback=None,on_error=None):
        try:
            self.status.set('Working locally…')
            def done(response):
                self.last_response=response;self.shell.pending();self.status.set('Offline • '+('Ready' if response['ok'] else 'Operation failed'))
                if response['ok']:
                    if operation in {'new_conversation','conversation_resume','project_load','project_leave'} and 'model_mode' in response['result']:
                        from vector_core.model_routing import MODES
                        mode=response['result']['model_mode'];self.model_mode.set(MODES.get(mode,'Choose model mode'))
                        if self.mode_catalog is not None:self.mode_catalog['mode']=mode
                        self.shell.model_state.set(MODES.get(mode,'Model not selected'))
                    if callback:callback(response['result'])
                elif on_error:on_error(response['result'])
                else:self.dialog.showerror('VECTOR operation blocked',response['result'],parent=self.root)
            self.client.start(operation,parameters,done);self.shell.pending()
        except (ValueError,RuntimeError,OSError) as error:
            if on_error:on_error(str(error))
            else:self.dialog.showerror('VECTOR',str(error),parent=self.root)
    def poll(self):
        try:self.client.poll()
        except (RuntimeError,OSError,ValueError) as error:
            self.backend_error=str(error)
            if getattr(self,'library',None) and self.library.loading:self.library.catalog_failed(str(error))
            self.status.set('Backend unavailable — restart VECTOR');self.shell.model_state.set('Backend unavailable');self.shell.core.state(busy=False,motion=False);self.shell.send.configure(state='disabled');self.shell.cancel.configure(state='disabled');return
        self.root.after(30 if self.client.pending else 100,self.poll)
    def show_chat(self,text):self.shell.append(text,'user' if text.startswith('You:') else 'system' if text.startswith(('Saved question:','Uncertainty:','Limitations:')) else None)
    def send_chat(self):
        question=self.question.get()
        if not question.strip():return
        if self.client.pending:
            self.dialog.showinfo('Operation running','Wait for the current operation or cancel it. Your question remains in the input field.');return
        self.shell.history_rows=[];self.shell.history_cursor=0
        self.question.delete(0,'end');self.show_chat('You: '+question);self.call('ask',{'question':question,'semantic':self.semantic_enabled.get(),'planning':self.planning_enabled.get(),'manual':self.manual_enabled.get(),'request_id':uuid4().hex},self.answer)
    def answer(self,record):
        if record.get('model_run'):
            self.active_response=record;self.active_planning=None;outcome=record['outcome'];self.show_chat('VECTOR: '+outcome['message'])
            if outcome.get('model_text'):self.show_chat(outcome['model_text'])
            for part in outcome.get('partial_responses',[]):self.show_chat('Completed '+part['phase']+' from '+part['model']+' (overall run incomplete):\n'+part['text'])
            if outcome.get('partial_text'):self.show_chat('Partial actual model response (incomplete):\n'+outcome['partial_text'])
            for note in outcome.get('quality_observations',[]):self.show_chat('Quality note: '+note)
            warnings=(outcome.get('generation') or {}).get('resources',{}).get('experimental_advisories',[])
            if warnings:self.show_chat('Experimental memory warning: '+'; '.join(warnings))
            if record.get('checked'):self.show_chat('Independent calculation check:\n'+self.shell.document_text(record['checked']))
            failure=outcome.get('failure') or {}
            if failure.get('restart_required') and failure.get('code')=='SUPERVISOR_CLOSED':self.show_chat('The protected controller exited. Reopen VECTOR to create a fresh controller; the technical diagnostic and saved work remain available.')
            elif failure.get('restart_required'):self.show_chat('The protected worker stopped. The next request will qualify a fresh worker; saved work is preserved.' if getattr(self,'mode_catalog',{}).get('adaptive') else 'The isolated worker stopped. Restart VECTOR before another model request; saved work is preserved.')
            selection=(record.get('context') or {}).get('context',{}).get('history_selection',{})
            if selection.get('omitted_for_context'):self.show_chat('This reply used a bounded selection of earlier messages; the full conversation remains saved.')
            if outcome.get('uncertainty'):self.show_chat('Uncertainty: '+outcome['uncertainty'])
            for issue in outcome.get('issues',[]):self.show_chat('Unresolved: '+issue)
            for cite in outcome.get('citations',[]):self.source_link(cite['event_id'])
            for error in outcome['errors']:self.show_chat('Limitations: '+error)
            context=(record.get('context') or {}).get('context',{})
            for conflict in context.get('conflicts',[]):self.show_chat('Unresolved source disagreement: '+conflict['subject']+' / '+conflict['predicate'])
            for claim in context.get('claims',[]):
                if claim['override']:self.show_chat('Scoped user assumption: '+claim['subject']+' '+claim['predicate']+' '+claim['operating_conclusion']+' ['+claim['scope']+']; source says '+claim['value'])
            if (record.get('context') or {}).get('display_notices'):self.show_chat('Source rights and provenance remain available under Inspect response / evidence and original-source links.')
            if record['model_run']['can_continue']:self.show_chat('Completed work is saved. Open Model work to resume this run or explicitly continue with one model.')
            if (record.get('context') or {}).get('context',{}).get('truncated'):self.show_chat('Limitations: retrieval was bounded; some candidate evidence was omitted. The selected evidence package was identical for both models.')
            if self.model_work_open:self.load_model_work()
            if getattr(self,'mode_catalog',{}).get('adaptive'):self.call('model_modes',{},self.mode_status)
            return
        if record.get('planning') is not None:
            self.active_response=None
            self.active_planning=record
            self.planned_answer(record['planning']);return
        if record.get('routing'):
            self.active_response=record
            outcome=record['outcome'];self.show_chat('VECTOR: '+outcome.get('message',outcome['status']))
            if record.get('checked'):self.show_chat(self.shell.document_text(record['checked']))
            elif outcome.get('answer'):
                for statement in outcome['answer']['statements']:
                    self.show_chat(statement['text']+'\n['+statement['kind']+'; model interpretation is unverified]')
                    for cite in statement['citations']:self.source_link(cite['event_id'])
                self.show_chat('Uncertainty: '+outcome['answer']['uncertainty'])
            elif record.get('context'):
                sources=record['context']['context']['sources']
                self.show_chat('Retrieved source material — not a completed explanation or summary.' if sources else 'No matching relevant source material was established.')
                for source in sources:self.show_chat(source['quote']);self.source_link(source['event_id'])
            for conflict in (record.get('context') or {}).get('context',{}).get('conflicts',[]):self.show_chat('Conflicting sources: '+conflict['subject']+' / '+conflict['predicate']+'; no single conclusion is established.')
            for claim in (record.get('context') or {}).get('context',{}).get('claims',[]):
                if claim['override']:self.show_chat('Scoped user assumption: '+claim['subject']+' '+claim['predicate']+' '+claim['operating_conclusion']+' ['+claim['scope']+']; source says '+claim['value'])
            if outcome['errors']:self.show_chat('Limitations: '+'; '.join(outcome['errors']))
            if (record.get('context') or {}).get('display_notices'):self.show_chat('Source rights and provenance notices are available under Inspect response / evidence and View original source.')
            return
        for notice in (record.get('context') or {}).get('display_notices',[]):self.show_chat(notice['notice'])
        outcome=record['outcome'];self.show_chat('VECTOR: '+outcome['status'])
        if record.get('context') is None:
            self.show_chat('This saved request was interrupted or failed before evidence construction. No model answer was accepted.');return
        if outcome['answer']:
            for statement in outcome['answer']['statements']:
                self.show_chat(statement['text']+'\n['+statement['kind']+']')
                for cite in statement['citations']:self.source_link(cite['event_id'])
            self.show_chat('Uncertainty: '+outcome['answer']['uncertainty'])
        else:
            for source in record['context']['context']['sources']:
                self.show_chat(source['quote']);self.source_link(source['event_id'])
        if outcome['errors']:self.show_chat('Limitations: '+'; '.join(outcome['errors']))
        for claim in record['context']['context']['claims']:
            if claim['override']:self.show_chat('Scoped user assumption: '+claim['subject']+' '+claim['predicate']+' '+claim['operating_conclusion']+' ['+claim['scope']+']; source says '+claim['value'])
        for conflict in record['context']['context']['conflicts']:self.show_chat('Conflicting sources: '+conflict['subject']+' / '+conflict['predicate'])
        connected=record['context']['context'].get('semantic')
        if connected:
            self.show_chat('Connected evidence contains source interpretations; relationships alone do not establish a conclusion.')
            for conflict in connected['conflicts']:self.show_chat('Disputed evidence: '+conflict['subject']+' / '+conflict['predicate'])
            for note in connected['qualifications']:self.show_chat('Evidence qualification: '+note)
    def planned_answer(self,view):
        message=view['message']
        if view.get('answer'):message=message.replace(view['answer']['text'],self.shell.document_text(view['answer']),1)
        self.show_chat('VECTOR — investigation\n'+message)
        if self.active_planning:self.active_planning['planning']=view
        if view.get('answer') or view.get('intermediate_answer'):
            for source in (view.get('answer') or view['intermediate_answer'])['sources']:self.source_link(source['event_id'])
        for source in view.get('evidence_sources',[]):
            self.show_chat('Retrieved passage (relevance unverified): '+source['quote']);self.source_link(source['event_id'])
        if view.get('analysis'):
            for gap in view['analysis']['unresolved']:
                for option in gap['choices']:
                    if 'request' in option:
                        selector=option['request']['selector'];self.show_chat('Possible interpretation: '+selector['subject']+' — '+selector['predicate']+' ('+selector['sense']+'; scope '+selector['scope']+')')
        for notice in view.get('notices',[]):self.show_chat(notice)
    def clarify_investigation(self):
        if not self.active_planning or not self.active_planning['planning'].get('state'):self.dialog.showinfo('Investigation','Ask a planned question first, or load its saved conversation.');return
        question=self.question.get().strip()
        if not question:return
        view=self.active_planning['planning'];self.question.delete(0,'end');self.show_chat('Clarification: '+question)
        self.call('ask',{'question':question,'planning':True,'request_id':uuid4().hex,'investigation_id':view['id'],'revision':view['state']['revision']},self.answer)
    def resume_investigation(self):
        if not self.active_planning:return
        view=self.active_planning['planning']
        if not view.get('state'):
            record=self.active_planning;self.call('ask',{'question':record['question'],'planning':True,'request_id':record['id'],'constraints':record['planning_ref']['constraints']},self.answer);return
        self.call('question_run',{'id':view['id'],'revision':view['state']['revision'],'resume':view['state']['status'] in {'paused','cancelled','running'},'approved':True},self.planned_answer)
    def explore_investigation(self):
        if not self.active_planning or not self.active_planning['planning'].get('state'):return
        view=self.active_planning['planning'];self.call('question_explore',{'id':view['id'],'revision':view['state']['revision'],'approved':True},self.planned_answer)
    def reset_history(self,message):
        self.history_cursor=0;self.shell.reset();self.active_response=None;self.show_chat(message)
    def source_link(self,identity,start=0):
        tag='source:'+identity+':'+str(start);self.shell.append('Read original source '+identity,tag)
        self.chat.tag_configure(tag,foreground='#42dfe8',underline=True)
        self.chat.tag_bind(tag,'<Button-1>',lambda event:self.open_resource_reference(identity,start));self.chat.configure(state='disabled')
    def open_resource_reference(self,event_id,start=0):
        self.shell.navigate('Library');self.selected_event=event_id
        self.library.call('resource_reference',{'event_id':event_id,'start':start},lambda r:self.library.open(r['resource_id'],location=r))
    def load_history(self):self.call('history',{'after':self.history_cursor},lambda r:self.history(r))
    def history(self,result):
        self.history_cursor=result['next_cursor']
        for record in result['items']:self.show_chat('Saved question: '+record['question']);self.answer(record)
    def health(self,result):
        appearance=result.get('appearance') or {}
        self.shell.reduced.set(appearance.get('reduced_motion',False) or os.environ.get('VECTOR_REDUCED_MOTION')=='1');self.shell.core.state(motion=not self.shell.reduced.get())
        inference=result['inference']
        self.model_status.set('Development Mode: isolated runtime started. Select any installed model for manual inference.' if inference.get('runtime_version') else 'Local runtime not started: '+str(inference.get('reason','No worker selected.'))[:1200])
        self.active_project=result['session']['project_id']
        self.project_status.set('Active project: '+str(self.active_project) if self.active_project else 'No active project. Global memory remains available.')
        configuration=result['generation'];self.model.set(configuration['model'])
        for key,field in [('context','context_tokens'),('output','output_tokens'),('timeout','timeout_seconds')]:self.model_limits[key].delete(0,'end');self.model_limits[key].insert(0,str(configuration[field]))
        self.call('managed_models' if self.managed else 'models',{},self.model_list)
    def model_list(self,result):
        names=[row['name'] for row in result] if isinstance(result,list) else [row['name'] for row in result.get('models',[])]
        self.model_box['values']=names
        self.select_button.configure(state='normal' if names else 'disabled')
        self.shell.model_state.set('Model unavailable' if not names else 'Model selected' if self.model.get() in names else 'Model not selected')
        if not names:self.model_status.set('No available model. Archive search, evidence-only answers, tools and backups remain usable.')
        self.call('model_modes',{},self.mode_status)
    def mode_status(self,result):
        from vector_core.model_routing import MODES
        self.mode_catalog=result;adaptive=result.get('adaptive')
        self.mode_choices={label:key for key,label in MODES.items()}
        if adaptive:
            from vector_core.adaptive_runtime import AUTO_LABEL
            self.mode_choices={AUTO_LABEL:'auto'}
            for role,label in MODES.items():
                name=(result.get('manual_settings') or result['settings'])['bindings'].get(role)
                self.mode_choices[(role.upper()+' — '+name) if name and role!='both' else label]=role
            for row in result['models']:self.mode_choices['Model — '+row['name']]='model:'+row['name']
            labels={value:key for key,value in self.mode_choices.items()}
            selected=adaptive['selection'];value='model:'+selected['model'] if selected['mode']=='model' else selected['mode']
            self.model_mode.set(labels.get(value,AUTO_LABEL))
            default=adaptive.get('default_selection') or {'mode':'auto'};key='model:'+default['model'] if default['mode']=='model' else default['mode']
            self.default_mode.set(labels.get(key,AUTO_LABEL));self.mode_box['values']=tuple(self.mode_choices);self.default_mode_box['values']=tuple(self.mode_choices)
        else:self.model_mode.set(MODES.get(result['mode'],'Choose model mode'));self.default_mode.set(MODES.get(result['default_mode'],'Choose model mode'))
        self.shell.model_state.set(MODES.get(result['mode'],'Select a model')+(' • Development • runtime ready' if result.get('available') else ' • runtime stopped; see Local AI / memory'))
        if not result.get('available'):self.model_status.set('Runtime diagnostic: '+str(result.get('reason','No qualified local runtime.'))[:1800])
        current=next((m for m in result['modes'] if m['id']==result['mode']),None)
        if current and current.get('resource_blocked'):self.shell.model_state.set(MODES[result['mode']]+' • resource blocked')
        if adaptive:
            active=', '.join(adaptive.get('active_models',{}).values())
            self.shell.model_state.set(adaptive['label']+' • '+active+(' • protected runtime ready' if adaptive.get('runtime_qualified') else ' • starts when used'))
            notice=(adaptive.get('plan') or {}).get('reason') if adaptive['selection']['mode']=='auto' else None
            if adaptive.get('controller_alive') is False:self.shell.model_state.set(adaptive['label']+' • controller stopped; reopen VECTOR')
            self.model_status.set(adaptive.get('reason') or notice or 'Local model stores already approved. No internet permission. Protected inference qualifies on demand; model accuracy never blocks manual use.')
        if result.get('resources',{}).get('resource_notice'):self.model_status.set(result['resources']['resource_notice'])
        settings=result['settings'];self.synthesis_role.set(settings['synthesis']);self.extra_reviews.set(settings['extra_reviews'])
        names=[row['name'] for row in result['models']]
        for role,box in self.role_boxes.items():box['values']=names;self.role_names[role].set((result.get('manual_settings') or settings)['bindings'].get(role,''))
        if result['mode']:
            for key,field in [('context','context_tokens'),('output','output_tokens'),('timeout','timeout_seconds')]:self.model_limits[key].delete(0,'end');self.model_limits[key].insert(0,str(settings['generation'][field]))
    def selected_mode_id(self,value):
        from vector_core.model_routing import MODES
        return getattr(self,'mode_choices',{}).get(value) or next((key for key,label in MODES.items() if label==value),None)
    def open_runtime_options(self):
        self.shell.internal('Settings')
        def shown(result):
            settings=result.get('settings')
            if settings:
                self.experimental_memory.set(settings.get('experimental_memory',False));self.runtime_memory.delete(0,'end');self.runtime_memory.insert(0,str(settings['memory_bytes']//1048576))
            self.runtime_notice.set(result.get('startup_error') or 'Manual memory ceiling and scoped consent apply after reopen. AUTO adapts memory to hardware; the process ceiling and all mandatory protections remain enforced.')
        self.call('runtime_options_get',{},shown)
    def save_runtime_options(self):
        try:memory=int(self.runtime_memory.get())
        except ValueError:self.dialog.showerror('Memory cap','Enter a whole number of MiB; the maximum is checked against this computer.');return
        experimental=self.experimental_memory.get()
        if experimental and not self.dialog.askyesno('Experimental memory','Allow attempts despite conservative memory estimates and pressure warnings? Crashes and resource exhaustion are possible. Kernel memory/pids/CPU limits, zero worker swap and offline isolation remain enforced. Close and reopen VECTOR to apply.'):return
        self.call('runtime_options_set',{'memory_mib':memory,'experimental':experimental,'acknowledged':experimental},lambda result:self.runtime_notice.set(result['message']))
    def change_mode(self,event=None):
        mode=self.selected_mode_id(self.model_mode.get())
        if mode:
            adaptive=bool(getattr(self,'mode_catalog',{}).get('adaptive'))
            parameters={'mode':'model','model':mode[6:]} if mode.startswith('model:') else {'mode':mode}
            self.call('runtime_selection_set' if adaptive else 'model_mode_set',parameters,lambda result:self.call('model_modes',{},self.mode_status))
    def save_default_mode(self):
        mode=self.selected_mode_id(self.default_mode.get())
        if mode:
            adaptive=bool(getattr(self,'mode_catalog',{}).get('adaptive'))
            parameters={'mode':'model','model':mode[6:],'scope':'default'} if mode.startswith('model:') else {'mode':mode,'scope':'default'}
            self.call('runtime_selection_set' if adaptive else 'model_mode_set',parameters,lambda result:self.call('model_modes',{},self.mode_status))
    def save_model_settings(self):
        mode=self.selected_mode_id(self.model_mode.get()) or self.selected_mode_id(self.default_mode.get())
        if mode=='auto':self.dialog.showinfo('AUTO resource settings','AUTO adapts its own budgets. Select a manual model or Both to save custom generation settings.');return
        exact=mode[6:] if mode and mode.startswith('model:') else None
        if exact:mode='a'
        if not mode:self.dialog.showinfo('Choose a model mode','Choose a conversation model mode first.');return
        try:
            settings={'bindings':{k:v.get() for k,v in self.role_names.items() if v.get()},'synthesis':self.synthesis_role.get(),'extra_reviews':self.extra_reviews.get(),'generation':{'model':'','context_tokens':int(self.model_limits['context'].get()),'output_tokens':int(self.model_limits['output'].get()),'timeout_seconds':float(self.model_limits['timeout'].get()),'temperature':0,'seed':0}}
        except ValueError:self.dialog.showerror('Invalid model settings','Enter numeric context, output, timeout and review limits.');return
        if exact:settings['bindings']={'a':exact}
        self.call('model_mode_set',{'mode':mode,'settings':settings},lambda result:self.call('model_modes',{},self.mode_status))
    def toggle_model_work(self):
        self.model_work_open=not self.model_work_open
        if self.model_work_open:self.shell.model_work.grid();self.shell.model_work_button.configure(text='Model work ▾');self.load_model_work()
        else:self.shell.model_work.grid_remove();self.shell.model_work_button.configure(text='Model work ▸')
    def load_model_work(self):
        record=getattr(self,'active_response',None)
        if not record or not record.get('model_run_ref'):return
        def loaded(run):
            lines=[run['status']+' — '+run['mode'],'All generated material below is unverified. Agreement is not factual verification.']
            for stage in run['steps']:
                lines.append('\n'+stage['phase']+' — '+stage['model']+' — '+stage['status'])
                if stage.get('generation'):
                    try:
                        p=json.loads(stage['generation']['text']);lines.append(p.get('text',stage['generation']['text']));lines.extend(p.get('issues',[]));lines.append(p.get('uncertainty',''))
                    except ValueError:lines.append(stage['generation']['text'])
                if stage.get('error'):lines.append(stage['error'])
            text=self.shell.model_work_text;text.configure(state='normal');text.delete('1.0','end');text.insert('end','\n'.join(lines));text.configure(state='disabled')
        self.call('model_run',{'id':record['model_run_ref']},loaded)
    def resume_model_run(self):
        record=getattr(self,'active_response',None)
        if record and record.get('model_run_ref'):self.call('model_resume',{'id':record['model_run_ref'],'approved':True},self.answer)
    def continue_model_run(self):
        record=getattr(self,'active_response',None)
        if not record or not record.get('model_run_ref'):return
        role=self.simple.askstring('Continue with one model','Enter A or B. This starts an explicitly single-model answer using the saved task and evidence. The failed Both run remains recorded.',parent=self.root)
        if role and role.lower() in {'a','b'}:self.call('model_continue',{'id':record['model_run_ref'],'mode':role.lower(),'approved':True},self.answer)
    def select_model(self):
        try:config={'model':self.model.get(),'context_tokens':int(self.model_limits['context'].get()),'output_tokens':int(self.model_limits['output'].get()),'timeout_seconds':float(self.model_limits['timeout'].get()),'temperature':0,'seed':0}
        except ValueError:self.dialog.showerror('Invalid limits','Enter numeric generation limits.');return
        if getattr(self,'mode_catalog',{}).get('adaptive'):
            self.call('runtime_selection_set',{'mode':'model','model':config['model']},lambda result:self.call('model_modes',{},self.mode_status));return
        if not self.managed and not self.dialog.askyesno('External model dependency','Use these external local weights? Complete exports will fail until the required weights are imported into managed storage.'):return
        self.call('select_model',{'configuration':config,'authorize_external':True},lambda result:(self.shell.model_state.set('Model selected'),self.show_result(result)))
    def import_model(self):
        directory=self.files.askdirectory(title='Select the source Ollama models directory')
        name=self.model.get() or self.simple.askstring('Model','Exact local model:tag name')
        if directory and name and self.dialog.askyesno('Import managed model','Copy and hash all required local model assets into portable storage? This uses disk and CPU, never downloads.'):
            self.call('import_model',{'directory':directory,'model':name,'approved':True},self.show_result)
    def show_result(self,result):
        from tkinter.scrolledtext import ScrolledText
        window=self.tk.Toplevel(self.root);window.title('VECTOR result');window.geometry('800x550')
        text=ScrolledText(window,wrap='word');text.pack(fill='both',expand=True);text.insert('1.0',json.dumps(result,ensure_ascii=False,indent=2));text.configure(state='disabled')
    def fill(self,rows,kind):
        self.knowledge_rights.set(next((r['rights_notice'] for r in rows if r.get('rights_notice')),''))
        self.knowledge.delete(*self.knowledge.get_children());self.rows={}
        for row in rows:
            identity=row.get('event_id') or row.get('id');item=self.knowledge.insert('', 'end',values=(row.get('name') or row.get('submission_name') or row.get('subject'),row.get('excerpt') or (str(row.get('predicate',''))+' '+str(row.get('value',''))),identity))
            self.rows[item]=(kind,row)
    def search_sources(self):self.call('search',{'query':self.search.get()},lambda r:self.fill(r,'event'))
    def browse(self):self.call('events',{'after':self.event_cursor},self.source_page)
    def source_page(self,result):self.event_cursor=result['next_cursor'];self.fill(result['items'],'event')
    def claims(self):
        def loaded(result):self.claim_cursor=result['next_cursor'] if result['items'] else '';self.fill(result['items'],'claim')
        self.call('claims',{'event_id':self.selected_event,'after':self.claim_cursor},loaded)
    def select_source(self,event=None):
        selection=self.knowledge.selection()
        if not selection:return
        kind,row=self.rows[selection[0]]
        event_id=row.get('event_id') if kind=='claim' else row.get('event_id',row.get('id'))
        if event_id!=self.selected_event:self.claim_cursor=''
        self.selected_source_id=row.get('source_id');self.selected_event=event_id;self.selected_claim=row if kind=='claim' else None
    def view_source(self):
        if self.selected_event:self.call('show',{'event_id':self.selected_event},self.show_result)
    def export_original(self):
        if not self.selected_event:return
        path=self.files.asksaveasfilename(title='Export exact original to a new file')
        if path:self.call('export_original',{'event_id':self.selected_event,'output':path},self.show_result)
    def override(self):
        claim=self.selected_claim
        if not claim:self.dialog.showinfo('Select a claim','Click Claims, then select the claim to override.');return
        value=self.simple.askstring('Operating assumption','New value (source evidence remains unchanged):')
        if value is None:return
        reason=self.simple.askstring('Override reason','Reason for this scoped user assumption:')
        if reason and self.dialog.askyesno('Confirm override','Record an explicit user assumption for scope '+claim['scope']+'?'):
            self.call('override',{'claim_id':claim['id'],'value':value,'scope':claim['scope'],'reason':reason,'approved':True},self.show_result)
    def archive_text(self):self.call('ingest',{'text':self.learning.get('1.0','end-1c')},self.show_result)
    def import_file(self):
        path=self.files.askopenfilename(title='Archive a source file')
        if path:
            import mimetypes
            self.call('ingest',{'file':path,'media_type':mimetypes.guess_type(path)[0] or 'application/octet-stream'},self.show_result)
    def learn_text(self):self.call('learn',{'text':self.learning.get('1.0','end-1c'),'scope':self.scope.get(),'exclusive':self.exclusive.get()},self.show_result)
    def extract_proposal(self):
        if not self.selected_event:self.dialog.showinfo('Select a source','Select an archived source in Knowledge first.');return
        self.call('extract_proposal',{'event_id':self.selected_event,'scope':self.scope.get()},self.show_result)
    def proposals(self):
        window=self.tk.Toplevel(self.root);window.title('Review source-linked proposals');window.geometry('760x430')
        self.ttk.Label(window,text='Inspect the original quotes and proposed fields before approving. Claims remain unverified.').pack(anchor='w',padx=10,pady=10)
        listing=self.tk.Listbox(window);listing.pack(fill='both',expand=True,padx=10)
        state={'rows':[],'after':0,'reviewed':None}
        controls=self.ttk.Frame(window);controls.pack(fill='x',padx=10,pady=10)
        def load():
            def loaded(result):
                state.update(rows=[r for r in result['items'] if r['status']=='pending'],after=result['next_cursor'],reviewed=None)
                listing.delete(0,'end')
                for record in state['rows']:listing.insert('end',record['origin']+' — '+record['id'])
                approve.configure(state='disabled')
                if not result['items']:state['after']=0
            self.call('proposals',{'after':state['after']},loaded)
        def selected():
            indices=listing.curselection()
            return state['rows'][indices[0]]['id'] if indices else None
        def inspect():
            identity=selected()
            if not identity:return
            def inspected(detail):
                self.show_result(detail);state['reviewed']=identity
                if selected()==identity:approve.configure(state='normal')
            self.call('proposal_detail',{'id':identity},inspected)
        def apply():
            identity=selected()
            if identity!=state['reviewed']:return
            if self.dialog.askyesno('Approve reviewed claims','Apply all reviewed claims atomically as unverified source-linked interpretations?'):
                self.call('approve_proposal',{'id':identity,'approved':True},self.show_result);approve.configure(state='disabled')
        self.ttk.Button(controls,text='Inspect exact original evidence',command=inspect).pack(side='left')
        approve=self.ttk.Button(controls,text='Approve reviewed proposal',command=apply,state='disabled');approve.pack(side='left',padx=6)
        self.ttk.Button(controls,text='Next page / restart',command=load).pack(side='right')
        listing.bind('<<ListboxSelect>>',lambda event:approve.configure(state='normal' if selected()==state['reviewed'] and selected() else 'disabled'))
        load()
    def open_library(self):
        from vector_core.library_desktop import LiteraryDesktop
        self.library_window=LiteraryDesktop(self)
    def create_project(self):self.call('project_create',{'name':self.project_name.get()},lambda r:self.open_project(r['id']))
    def projects(self):
        def loaded(result):
            self.project_cursor=result['next_cursor'];self.project_list.delete(0,'end');self.project_rows={}
            for row in result['items']:
                if row['payload'].get('kind')=='project':
                    index=self.project_list.size();self.project_list.insert('end',row['payload']['name']);self.project_rows[index]=row['payload']['id']
                    if row['payload'].get('archived'):self.project_list.delete(index);self.project_list.insert(index,row['payload']['name']+' [archived]')
            if not result['items']:self.project_cursor=0
        self.call('projects',{'after':self.project_cursor},loaded)
    def load_project(self):
        selected=self.project_list.curselection()
        if selected:self.open_project(self.project_rows[selected[0]])
    def open_project(self,identity):
        def loaded(result):
            self.active_project=result['project_id'];self.project_status.set('Active project: '+result['project']['name']+(' [archived]' if result['project'].get('archived') else ''))
            self.reset_history('Project resumed. Load saved conversation to read its history.');self.clear_item();self.item_after=0;self.project_item_list.delete(0,'end')
        self.call('project_load',{'id':identity},loaded)
    def leave_project(self):
        def left(result):self.active_project=None;self.project_status.set('Global workspace. Originals remain searchable.');self.reset_history('Global conversation.');self.clear_item();self.item_after=0;self.project_item_list.delete(0,'end')
        self.call('project_leave',{},left)
    def link_selected_project(self):
        selected=self.knowledge.selection()
        events=list(dict.fromkeys(self.rows[item][1].get('event_id',self.rows[item][1].get('id')) for item in selected))
        if not events and self.selected_event:events=[self.selected_event]
        if self.active_project and events:
            if len(events)>64:self.dialog.showinfo('Bounded batch','Select at most 64 sources per atomic operation. Projects may contain any number of sources.');return
            self.call('project_links',{'event_ids':events,'approved':True},self.show_result)
        else:self.dialog.showinfo('Select project and sources','Open a project and select sources in Knowledge first.')
    def project_sources(self):
        if not self.active_project:return
        self.paged_records('Project sources','project_sources',lambda r:r['event_id'],lambda r:self.call('show',{'event_id':r['event_id']},self.show_result),{'project_id':self.active_project})
    def project_history(self):
        if not self.active_project:return
        self.paged_records('Project history','project_history',lambda r:r['created']+' — '+r['contract'],self.show_result,{'project_id':self.active_project})
    def archive_project(self):
        if not self.active_project:return
        def selected(record):
            archived=not record.get('archived',False)
            if self.dialog.askyesno('Project status','Archive this project?' if archived else 'Restore this project to active status?'):
                self.call('project_archive',{'archived':archived,'revision':record['revision'],'approved':True},lambda r:self.project_status.set(r['name']+(' [archived]' if r['archived'] else ' [active]')))
        self.call('project_get',{},selected)
    def clear_item(self):
        self.editing_item=None;self.item_title.delete(0,'end');self.item_body.delete('1.0','end');self.item_status.set('open')
    def project_items(self):
        if not self.active_project:return
        def loaded(result):
            self.project_item_list.delete(0,'end');self.item_rows={}
            for index,row in enumerate(result['items']):self.project_item_list.insert('end',row['kind']+' / '+row['status']+' — '+row['title']);self.item_rows[index]=row
            self.item_after=result['next_cursor'] if result['items'] else 0
        self.call('project_items',{'after':getattr(self,'item_after',0)},loaded)
    def select_project_item(self,event=None):
        selected=self.project_item_list.curselection()
        if not selected:return
        row=self.item_rows[selected[0]];self.clear_item();self.editing_item=row
        self.item_kind.set(row['kind']);self.item_status.set(row['status']);self.item_title.insert(0,row['title']);self.item_body.insert('1.0',row['body'])
    def save_item(self):
        if not self.active_project:self.dialog.showinfo('Open project','Create or open a project first.');return
        previous=self.editing_item
        evidence=list(previous['evidence']) if previous else []
        if self.selected_event and self.selected_event not in evidence:evidence.append(self.selected_event)
        parameters={'kind':self.item_kind.get(),'title':self.item_title.get(),'body':self.item_body.get('1.0','end-1c'),'status':self.item_status.get(),'evidence':evidence,'approved':True}
        if previous:parameters.update(item_id=previous['id'],revision=previous['revision'],confidence=previous['confidence'],uncertainty=previous['uncertainty'])
        def saved(record):self.editing_item=record;self.status.set('Saved project revision. Evidence remains unverified.')
        self.call('project_item',parameters,saved)
    def paged_records(self,title,operation,label,inspect,parameters=None):
        window=self.tk.Toplevel(self.root);window.title(title);window.geometry('760x420')
        listing=self.tk.Listbox(window);listing.pack(fill='both',expand=True);state={'after':0,'rows':[]}
        def load():
            def loaded(result):
                state.update(rows=result['items'],after=result['next_cursor'] if result['items'] else 0);listing.delete(0,'end')
                for row in state['rows']:listing.insert('end',label(row))
            self.call(operation,{**(parameters or {}),'after':state['after']},loaded)
        def selected():
            indices=listing.curselection()
            if indices:inspect(state['rows'][indices[0]])
        self.ttk.Button(window,text='Next page / restart',command=load).pack(side='left');self.ttk.Button(window,text='Inspect / open selected',command=selected).pack(side='right');load()
    def checked_results(self):
        self.paged_records('Checked investigation results','investigation_list',lambda r:r['status']+' — '+r['goal'],lambda r:self.call('investigation_answer',{'id':r['id']},self.checked_answer))
    def checked_answer(self,result):
        self.show_chat('VECTOR — checked findings\n'+self.shell.document_text(result['answer']))
        for notice in result.get('notices',[]):self.show_chat(notice)
        if result.get('commentary'):
            self.show_chat('Optional model commentary — unverified; checked findings above remain authoritative.')
            for note in result['commentary']['notes']:self.show_chat(note['kind']+': '+note['text'])
        for source in result['answer']['sources']:self.source_link(source['event_id'])
    def conversations(self):
        def resume(row):
            def resumed(result):
                self.active_project=result['project_id'];self.project_status.set('Resumed project '+str(self.active_project) if self.active_project else 'Global conversation');self.reset_history('Saved session resumed. Load saved conversation to view turns.')
            self.call('conversation_resume',{'conversation_id':row['conversation_id']},resumed)
        self.paged_records('Saved conversations','conversation_browse',lambda r:r['question'],resume)
    def recall_memories(self):
        parameters={'query':self.search.get(),'view':self.memory_view.get(),'project_only':self.project_only.get() or self.memory_view.get()=='project'}
        for key,entry in [('since',self.memory_since),('until',self.memory_until)]:
            if entry.get():parameters[key]=entry.get()
        if self.source_only.get():
            if not self.selected_source_id:self.dialog.showinfo('Select source','Select an original source first.');return
            parameters['source_id']=self.selected_source_id
        def recalled(result):
            if result['view']=='working':self.show_result(result)
            else:self.fill(result['items'],'event')
        self.call('memory_recall',parameters,recalled)
    def source_operation(self,operation):
        if self.selected_event:self.call(operation,{'event_id':self.selected_event},self.show_result)
    def link_evidence(self):
        if not self.selected_event:return
        first=self.selected_event
        # Events use string cursors, unlike registered-record pages.
        window=self.tk.Toplevel(self.root);window.title('Link selected evidence');window.geometry('650x360');listing=self.tk.Listbox(window);listing.pack(fill='both',expand=True);state={'after':'','rows':[]}
        def load():
            def loaded(result):
                state.update(after=result['next_cursor'],rows=result['items']);listing.delete(0,'end')
                for row in result['items']:listing.insert('end',row['submission_name'])
                if not result['items']:state['after']=''
            self.call('events',{'after':state['after']},loaded)
        def apply():
            chosen=listing.curselection()
            if not chosen:return
            reason=self.simple.askstring('Relationship reason','Why are these originals related?')
            if reason:self.call('memory_link',{'event_id':first,'target_id':state['rows'][chosen[0]]['id'],'kind':'related','reason':reason,'approved':True},self.show_result)
        self.ttk.Button(window,text='Next sources / restart',command=load).pack(side='left');self.ttk.Button(window,text='Save user relationship',command=apply).pack(side='right');load()
    def assessment_history(self):
        if self.selected_claim:self.call('assessment_history',{'claim_id':self.selected_claim['id']},self.show_result)
    def assess_claim(self):
        if not self.selected_claim:return
        reason=self.simple.askstring('Reassessment','Reason to mark this interpretation disputed (source stays intact):')
        if reason:self.call('assess',{'claim_id':self.selected_claim['id'],'state':'disputed','confidence':0,'reason':reason,'approved':True},self.show_result)
    def entity_lookup(self):
        name=self.simple.askstring('Entity','Exact entity or concept label:')
        if name:self.call('entity',{'name':name},self.show_result)
    def tool_fields(self):
        for child in self.tool_form.winfo_children():child.destroy()
        fields={'arithmetic':[('expression','2+2')],'convert':[('value','1'),('from','ft'),('to','m')],
                'solve_linear':[('a','2'),('b','3'),('c','11')],'geometry':[('shape','circle'),('dimensions','1'),('unit','m')],
                'statistics':[('values','1,2,3,4')],'constant':[('name','c')]}[self.tool_name.get()]
        self.tool_inputs={}
        for row,(name,default) in enumerate(fields):
            self.ttk.Label(self.tool_form,text=name.title()).grid(row=row,column=0,sticky='w',padx=6,pady=4)
            entry=self.ttk.Entry(self.tool_form,width=60);entry.insert(0,default);entry.grid(row=row,column=1,sticky='ew');self.tool_inputs[name]=entry
    def run_tool(self):
        parameters={k:v.get() for k,v in self.tool_inputs.items()}
        if self.tool_name.get()=='statistics':parameters['values']=[v.strip() for v in parameters['values'].split(',')]
        if self.tool_name.get()=='geometry':parameters['dimensions']=[v.strip() for v in parameters['dimensions'].split(',')]
        def result(record):self.tool_result.delete('1.0','end');self.tool_result.insert('1.0',json.dumps(record,indent=2,ensure_ascii=False))
        self.call('tool',{'name':self.tool_name.get(),'parameters':parameters,'approved':True},result)
    def key_file(self):
        if self.dialog.askyesno('Encrypted backup','Use an existing separate recovery-key file for this operation?'):
            key=self.files.askopenfilename(title='Select separate private recovery key')
            if not key:raise ValueError('Recovery key selection cancelled; no plaintext fallback.')
            return key
        return None
    def create_key(self):
        path=self.files.asksaveasfilename(title='Save NEW recovery key separately from data/backups')
        if path:self.call('create_recovery_key',{'output':path,'approved':True},self.show_result)
    def backup(self):
        parent=self.files.askdirectory(title='Select backup parent folder')
        if parent:
            try:key=self.key_file()
            except ValueError:return
            self.call('backup',{'directory':str(Path(parent)/('vector-backup-'+time.strftime('%Y%m%d-%H%M%S'))),'key_file':key},self.show_result)
    def verify_backup(self):
        directory=self.files.askdirectory(title='Select VECTOR backup repository')
        if directory:
            try:key=self.key_file()
            except ValueError:return
            self.call('verify_backup',{'directory':directory,'key_file':key},self.show_result)
    def restore(self):
        directory=self.files.askdirectory(title='Select backup repository')
        destination=self.files.asksaveasfilename(title='Choose NEW data folder name (must not exist)') if directory else None
        if destination:
            try:key=self.key_file()
            except ValueError:return
            self.call('restore',{'directory':directory,'destination':destination,'key_file':key},self.show_result)
    def move(self):
        destination=self.files.asksaveasfilename(title='Choose NEW location on larger storage')
        if destination and self.dialog.askyesno('Move data','Verify the new copy and redirect VECTOR? Old originals will be retained.'):
            self.call('move',{'destination':destination,'approved':True},self.show_result)
    def close(self):
        if getattr(self,'library',None) and not self.client.pending:
            self.library.save_position();end=time.monotonic()+2
            while (self.client.pending or self.library.queue) and time.monotonic()<end:self.root.update();time.sleep(.01)
        if self.client.pending and not self.dialog.askyesno('Operation running','Cancel the current operation and close?'):return
        if self.client.pending:self.client.cancel()
        if getattr(self,'library',None):self.library.close()
        self.shell.close();self.client.close();self.root.destroy()


def configure_startup(args):
    if getattr(args,'library',False):args.no_inference=True
    if args.no_inference:
        if args.models_directory or args.managed or args.runtime_profile:raise ValueError('Storage-only startup cannot also request a model runtime.')
    elif not args.models_directory and not args.managed and not args.runtime_profile:
        profile=Path.home()/'.config/vector/local-inference.json'
        if profile.exists():args.runtime_profile=str(profile)
    return args


def main(argv=None):
    parser=argparse.ArgumentParser(description='VECTOR offline development desktop');parser.add_argument('--data-dir');parser.add_argument('--models-directory');parser.add_argument('--choose-models',action='store_true');parser.add_argument('--choose-data',action='store_true');parser.add_argument('--managed',action='store_true');parser.add_argument('--runtime-profile');parser.add_argument('--no-inference',action='store_true',help='Explicit storage-only session.')
    parser.add_argument('--library',action='store_true',help='Open the Library without starting local AI; default model settings remain unchanged.')
    args=parser.parse_args(argv)
    try:
        configure_startup(args);root,client=bootstrap(args)
        if root is None:return 0
        app=Desktop(root,client,managed=args.managed)
        if args.library:app.shell.navigate('Library')
        root.mainloop();return 0
    except Exception as error:
        print('VECTOR desktop startup blocked: '+str(error),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
