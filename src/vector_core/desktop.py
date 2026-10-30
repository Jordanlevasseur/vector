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
        self.process=process;self.pending=None;self.output=b'';self.input=b''
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
            if response.get('initialization_error'):raise RuntimeError('VECTOR startup blocked: '+str(response['result']))
            if not self.pending or response.get('id')!=self.pending[0]:raise RuntimeError('Application response identity mismatch.')
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
        style=ttk.Style();style.theme_use('clam');style.configure('TButton',padding=6);style.configure('TNotebook.Tab',padding=(16,8))
        top=ttk.Frame(root,padding=10);top.pack(fill='x')
        ttk.Label(top,text='VECTOR',font=('Sans',20,'bold')).pack(side='left')
        self.status=tk.StringVar(value='Starting protected application…');ttk.Label(top,textvariable=self.status).pack(side='left',padx=20)
        ttk.Button(top,text='Cancel operation',command=self.client.cancel).pack(side='right')
        notebook=ttk.Notebook(root);notebook.pack(fill='both',expand=True,padx=10,pady=(0,10))
        self.tabs={}
        for name in ('Assistant','Knowledge','Learning','Projects','Tools','Settings'):
            tab=ttk.Frame(notebook,padding=12);notebook.add(tab,text=name);self.tabs[name]=tab
        self.chat=ScrolledText(self.tabs['Assistant'],wrap='word',font=('Sans',11),state='disabled');self.chat.pack(fill='both',expand=True)
        line=ttk.Frame(self.tabs['Assistant']);line.pack(fill='x',pady=8)
        self.question=ttk.Entry(line);self.question.pack(side='left',fill='x',expand=True);self.question.bind('<Return>',lambda event:self.send_chat())
        ttk.Button(line,text='Ask VECTOR',command=self.send_chat).pack(side='left',padx=6)
        ttk.Button(line,text='New conversation',command=lambda:self.call('new_conversation',{},lambda r:self.reset_history('New conversation.'))).pack(side='left')
        ttk.Button(self.tabs['Assistant'],text='Load saved conversation',command=self.load_history).pack(anchor='w')
        ttk.Button(self.tabs['Assistant'],text='Find / resume older conversations',command=self.conversations).pack(anchor='w')
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
        self.knowledge=ttk.Treeview(tab,columns=('title','detail','identity'),show='headings',height=12)
        for name,width in [('title',240),('detail',420),('identity',220)]:self.knowledge.heading(name,text=name.title());self.knowledge.column(name,width=width)
        self.knowledge.pack(fill='both',expand=True,pady=8);self.knowledge.bind('<<TreeviewSelect>>',self.select_source);self.knowledge.bind('<Double-1>',lambda event:self.view_source())
        ttk.Button(tab,text='View selected original / evidence',command=self.view_source).pack(anchor='w')
        ttk.Button(tab,text='Export selected original',command=self.export_original).pack(anchor='w',pady=4)
        more=ttk.Frame(tab);more.pack(fill='x')
        for label,command in [('Compare / versions',lambda:self.source_operation('memory_compare')),('Relationships',lambda:self.source_operation('memory_links')),('Link evidence',self.link_evidence),('Assessments',self.assessment_history),('Dispute claim',self.assess_claim),('Entity',self.entity_lookup)]:ttk.Button(more,text=label,command=command).pack(side='left',padx=2)
        tab=self.tabs['Learning'];ttk.Label(tab,text='Import originals or learn explicit subject | predicate | value statements. Sources remain unverified.').pack(anchor='w')
        self.learning=ScrolledText(tab,wrap='word',height=12);self.learning.pack(fill='both',expand=True,pady=8)
        controls=ttk.Frame(tab);controls.pack(fill='x');self.scope=ttk.Entry(controls,width=20);self.scope.insert(0,'personal');self.scope.grid(row=0,column=0,sticky='w')
        self.exclusive=tk.BooleanVar();ttk.Checkbutton(controls,text='Comparable exclusive claims',variable=self.exclusive).grid(row=0,column=1,columnspan=2,sticky='w')
        for index,(label,command) in enumerate([('Archive text',self.archive_text),('Import file',self.import_file),('Learn statements',self.learn_text),('AI proposal from selected source',self.extract_proposal),('Review proposals',self.proposals)]):ttk.Button(controls,text=label,command=command).grid(row=1+index//3,column=index%3,sticky='w',padx=3,pady=4)
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
        tab=self.tabs['Settings'];self.model_status=tk.StringVar(value='No model availability assumed');ttk.Label(tab,textvariable=self.model_status,wraplength=950).pack(anchor='w')
        bar=ttk.Frame(tab);bar.pack(fill='x',pady=8);self.model=tk.StringVar();self.model_box=ttk.Combobox(bar,textvariable=self.model,width=30,state='readonly');self.model_box.pack(side='left')
        self.model_limits={}
        for key,default in [('context',2048),('output',256),('timeout',30)]:
            ttk.Label(bar,text=key.title()).pack(side='left',padx=4);entry=ttk.Entry(bar,width=7);entry.insert(0,str(default));entry.pack(side='left');self.model_limits[key]=entry
        self.select_button=ttk.Button(bar,text='Select model',command=self.select_model,state='disabled');self.select_button.pack(side='left',padx=5)
        ttk.Button(tab,text='Import selected local model into portable storage',command=self.import_model).pack(anchor='w')
        ttk.Label(tab,text='To configure inference, launch “VECTOR — Local Models” or “VECTOR — Managed Models” from the application menu.\nModel output is unverified inference; exact citations do not certify its conclusions.',wraplength=950).pack(anchor='w',pady=8)
        actions=ttk.Frame(tab);actions.pack(fill='x',pady=4)
        for index,(label,command) in enumerate([('Storage usage / available space',lambda:self.call('storage',{},self.show_result)),('Verify originals',lambda:self.call('verify',{},self.show_result)),('Create separate recovery key',self.create_key),('Export VECTOR',self.backup),('Verify backup (actual restore)',self.verify_backup),('Restore to a new folder',self.restore),('Move data location',self.move),('Rebuild search indexes',lambda:self.call('rebuild',{},self.show_result)),('Recover interrupted storage',lambda:self.call('recover_storage',{},self.show_result)),('System / offline diagnostics',lambda:self.call('health',{},self.show_result))]):ttk.Button(actions,text=label,command=command).grid(row=index//2,column=index%2,sticky='ew',padx=4,pady=3)
        self.root.protocol('WM_DELETE_WINDOW',self.close);root.deiconify();root.after(30,self.poll);self.call('health',{},self.health)
    def call(self,operation,parameters,callback=None):
        try:
            self.status.set('Working: '+operation)
            def done(response):
                self.last_response=response;self.status.set('Offline • '+('Ready' if response['ok'] else 'Operation failed'))
                if response['ok']:
                    if callback:callback(response['result'])
                else:self.dialog.showerror('VECTOR operation blocked',response['result'],parent=self.root)
            self.client.start(operation,parameters,done)
        except (ValueError,RuntimeError,OSError) as error:self.dialog.showerror('VECTOR',str(error),parent=self.root)
    def poll(self):
        try:self.client.poll()
        except (RuntimeError,OSError,ValueError) as error:self.status.set(str(error));return
        self.root.after(30,self.poll)
    def show_chat(self,text):self.chat.configure(state='normal');self.chat.insert('end',text+'\n\n');self.chat.see('end');self.chat.configure(state='disabled')
    def send_chat(self):
        question=self.question.get()
        if not question.strip():return
        if self.client.pending:
            self.dialog.showinfo('Operation running','Wait for the current operation or cancel it. Your question remains in the input field.');return
        self.question.delete(0,'end');self.show_chat('You: '+question);self.call('ask',{'question':question},self.answer)
    def answer(self,record):
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
    def reset_history(self,message):
        self.history_cursor=0;self.show_chat(message)
    def source_link(self,identity):
        tag='source:'+identity;self.chat.configure(state='normal');self.chat.insert('end','View original source '+identity+'\n\n',tag)
        self.chat.tag_configure(tag,foreground='#1e4f8f',underline=True)
        self.chat.tag_bind(tag,'<Button-1>',lambda event:self.call('show',{'event_id':identity},self.show_result));self.chat.configure(state='disabled')
    def load_history(self):self.call('history',{'after':self.history_cursor},lambda r:self.history(r))
    def history(self,result):
        self.history_cursor=result['next_cursor']
        for record in result['items']:self.show_chat('Saved question: '+record['question']);self.answer(record)
    def health(self,result):
        inference=result['inference']
        self.model_status.set('Isolated local runtime qualified. Select a model; generated answers remain unverified.' if inference.get('runtime_version') else 'Local AI unavailable: '+str(inference.get('reason','No worker selected.'))[:350])
        self.active_project=result['session']['project_id']
        self.project_status.set('Active project: '+str(self.active_project) if self.active_project else 'No active project. Global memory remains available.')
        configuration=result['generation'];self.model.set(configuration['model'])
        for key,field in [('context','context_tokens'),('output','output_tokens'),('timeout','timeout_seconds')]:self.model_limits[key].delete(0,'end');self.model_limits[key].insert(0,str(configuration[field]))
        self.call('managed_models' if self.managed else 'models',{},self.model_list)
    def model_list(self,result):
        names=[row['name'] for row in result] if isinstance(result,list) else [row['name'] for row in result.get('models',[])]
        self.model_box['values']=names
        self.select_button.configure(state='normal' if names else 'disabled')
        if not names:self.model_status.set('No available model. Archive search, evidence-only answers, tools and backups remain usable.')
    def select_model(self):
        try:config={'model':self.model.get(),'context_tokens':int(self.model_limits['context'].get()),'output_tokens':int(self.model_limits['output'].get()),'timeout_seconds':float(self.model_limits['timeout'].get()),'temperature':0,'seed':0}
        except ValueError:self.dialog.showerror('Invalid limits','Enter numeric generation limits.');return
        if not self.managed and not self.dialog.askyesno('External model dependency','Use these external local weights? Complete exports will fail until the required weights are imported into managed storage.'):return
        self.call('select_model',{'configuration':config,'authorize_external':True},self.show_result)
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
        if self.client.pending and not self.dialog.askyesno('Operation running','Cancel the current operation and close?'):return
        if self.client.pending:self.client.cancel()
        self.client.close();self.root.destroy()


def main(argv=None):
    parser=argparse.ArgumentParser(description='VECTOR offline desktop');parser.add_argument('--data-dir');parser.add_argument('--models-directory');parser.add_argument('--choose-models',action='store_true');parser.add_argument('--choose-data',action='store_true');parser.add_argument('--managed',action='store_true')
    args=parser.parse_args(argv)
    try:
        root,client=bootstrap(args)
        if root is None:return 0
        Desktop(root,client,managed=args.managed);root.mainloop();return 0
    except Exception as error:
        print('VECTOR desktop startup blocked: '+str(error),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
