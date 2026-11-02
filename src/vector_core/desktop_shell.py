"""Progressive native presentation; every action uses the existing Desktop client."""
import os
import tkinter as tk
from tkinter import ttk
from vector_core.desktop_theme import COLORS as C,FONT,Core,CommandInput,Workspace,apply

PRIMARY=('Home / Chat','Projects','History')
SECONDARY=('Knowledge','Memory','Investigations','Settings','Advanced')


class Interface:
    def __init__(self,app):
        self.app=app;root=app.root;self.style=apply(root);self.current='Home / Chat';self.menu_open=False;self.history_cursor=0;self.history_rows=[];self.follow=True;self.has_text=False
        root.title('VECTOR — Personal Intelligence');root.minsize(820,580)
        self.header=ttk.Frame(root,padding=(16,8));self.header.pack(fill='x')
        self.hamburger=ttk.Button(self.header,text='☰',width=3,style='Accent.TButton',command=self.toggle_menu);self.hamburger.pack(side='left')
        ttk.Label(self.header,text='V E C T O R',style='Brand.TLabel').pack(side='left',padx=16)
        self.destination=tk.StringVar(value='HOME / CHAT');ttk.Label(self.header,textvariable=self.destination,style='Muted.TLabel').pack(side='left',padx=12)
        self.cancel=ttk.Button(self.header,text='Cancel',command=app.client.cancel,state='disabled');self.cancel.pack(side='right')
        self.model_state=tk.StringVar(value='Model not checked');ttk.Label(self.header,textvariable=self.model_state,style='Muted.TLabel').pack(side='right',padx=8)
        app.status=tk.StringVar(value='Starting protected application…');ttk.Label(self.header,textvariable=app.status,style='Muted.TLabel').pack(side='right',padx=12)
        divider=tk.Frame(root,height=1,background=C['border']);divider.pack(fill='x',padx=16)
        self.stack=ttk.Frame(root);self.stack.pack(fill='both',expand=True,padx=16,pady=(8,12))
        self.stack.rowconfigure(0,weight=1);self.stack.columnconfigure(0,weight=1)
        # Keep the original six workspaces as internal components, not tabs.
        app.tabs={};self.legacy={}
        for name in ('Assistant','Knowledge','Learning','Projects','Tools','Settings'):
            if name=='Assistant':frame=ttk.Frame(self.stack);app.tabs[name]=frame;self.legacy[name]=frame
            else:
                frame=Workspace(self.stack);app.tabs[name]=frame.content;self.legacy[name]=frame
            frame.grid(row=0,column=0,sticky='nsew')
        self.views={'Home / Chat':self.legacy['Assistant'],'Projects':self.legacy['Projects'],'Knowledge':self.legacy['Knowledge'],'Memory':self.legacy['Knowledge'],'Settings':self.legacy['Settings'],'Advanced':self.legacy['Tools']}
        self.create_home();self.create_history();self.create_investigations()
        self.menu=tk.Frame(root,background=C['border'],padx=1,pady=1);panel=ttk.Frame(self.menu,padding=10);panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='WORKSPACE',style='Muted.TLabel').pack(anchor='w',padx=10,pady=(4,8))
        self.menu_buttons=[];self.nav={}
        for group in (PRIMARY,SECONDARY):
            if group==SECONDARY:ttk.Separator(panel).pack(fill='x',pady=10)
            for name in group:
                button=ttk.Button(panel,text=name,command=lambda n=name:self.navigate(n));button.pack(fill='x',pady=2);self.menu_buttons.append(button);self.nav[name]=button
                button.bind('<Down>',lambda e:self.menu_focus(1));button.bind('<Up>',lambda e:self.menu_focus(-1))
        root.bind('<Escape>',lambda e:self.hide_menu(),add='+');root.bind('<Alt-m>',lambda e:self.toggle_menu(),add='+');root.bind('<Button-1>',self.dismiss,add='+')
        self.navigate('Home / Chat',load=False)
    def create_home(self):
        a=self.app;home=a.tabs['Assistant'];home.rowconfigure(1,weight=1);home.columnconfigure(0,weight=1)
        self.core=Core(home);self.core.grid(row=0,column=0,sticky='ew')
        stream=ttk.Frame(home);stream.grid(row=1,column=0,sticky='nsew');stream.rowconfigure(0,weight=1);stream.columnconfigure(0,weight=1)
        a.chat=tk.Text(stream,wrap='word',font=FONT['body'],state='disabled',borderwidth=0,highlightthickness=0,padx=20,pady=14,spacing1=6,spacing3=12)
        a.chat.grid(row=0,column=0,sticky='nsew');scroll=ttk.Scrollbar(stream,command=a.chat.yview);scroll.grid(row=0,column=1,sticky='ns');a.chat.configure(yscrollcommand=self.scroll_changed)
        a.chat.tag_configure('user',foreground=C['ice']);a.chat.tag_configure('system',foreground=C['muted'],font=FONT['small'])
        self.stream=stream;stream.grid_remove();self.core.grid_configure(rowspan=2,sticky='nsew')
        self.latest=ttk.Button(home,text='↓ Latest',command=self.to_latest);self.latest.grid(row=2,column=0,sticky='e',padx=16);self.latest.grid_remove()
        command=tk.Frame(home,background=C['border'],padx=1,pady=1);command.grid(row=3,column=0,sticky='ew',pady=(10,0))
        inside=ttk.Frame(command,padding=10);inside.pack(fill='x');inside.columnconfigure(0,weight=1)
        a.question=CommandInput(inside,height=3,wrap='word',undo=True,relief='flat',borderwidth=0,highlightthickness=1,padx=10,pady=8,font=FONT['body']);a.question.grid(row=0,column=0,sticky='ew')
        a.question.bind('<Return>',self.enter);a.question.bind('<Shift-Return>',self.newline)
        self.send=ttk.Button(inside,text='Send ↗',style='Accent.TButton',command=a.send_chat);self.send.grid(row=0,column=1,padx=(10,0))
        ttk.Label(inside,text='Enter sends · Shift+Enter adds a line · Entirely local',style='Muted.TLabel').grid(row=1,column=0,sticky='w',pady=(7,0))
        self.options=ttk.Frame(home,padding=(10,8));self.options.grid(row=4,column=0,sticky='ew');self.options.grid_remove()
        self.more_history=ttk.Button(self.options,text='Load next saved turns',command=a.load_history);self.more_history.pack(anchor='w',pady=4)
        a.planning_enabled=tk.BooleanVar(value=False);a.semantic_enabled=tk.BooleanVar(value=False);a.active_planning=None
        ttk.Checkbutton(self.options,text='Question planning (experimental)',variable=a.planning_enabled).pack(anchor='w')
        ttk.Checkbutton(self.options,text='Connected evidence (experimental)',variable=a.semantic_enabled).pack(anchor='w')
        row=ttk.Frame(self.options);row.pack(fill='x',pady=4)
        for label,cmd in [('Clarify',a.clarify_investigation),('Resume',a.resume_investigation),('Explore unverified ideas',a.explore_investigation),('Checked findings',a.checked_results),('Inspect response / evidence',self.inspect_active_plan)]:ttk.Button(row,text=label,command=cmd).pack(side='left',padx=3)
        bar=ttk.Frame(home);bar.grid(row=5,column=0,sticky='ew',pady=(6,0))
        ttk.Button(bar,text='Investigation / evidence controls',command=self.toggle_options).pack(side='left')
        ttk.Button(bar,text='New conversation',command=lambda:a.call('new_conversation',{},lambda r:a.reset_history('New conversation.'))).pack(side='right')
    def create_history(self):
        frame=ttk.Frame(self.stack,padding=18);frame.grid(row=0,column=0,sticky='nsew');self.views['History']=frame
        ttk.Label(frame,text='History',style='Brand.TLabel').pack(anchor='w');ttk.Label(frame,text='Saved turns retain their conversation, project and original record identity.',style='Muted.TLabel').pack(anchor='w',pady=8)
        self.history_list=ttk.Treeview(frame,columns=('created','question','project'),show='headings');self.history_list.pack(fill='both',expand=True,pady=12)
        for key,width in [('created',180),('question',460),('project',200)]:self.history_list.heading(key,text=key.title());self.history_list.column(key,width=width,minwidth=90)
        self.history_list.bind('<Double-1>',lambda e:self.open_history())
        controls=ttk.Frame(frame);controls.pack(fill='x')
        ttk.Button(controls,text='Next saved turns',command=self.browse_history).pack(side='left');ttk.Button(controls,text='Open selected conversation',command=self.open_history).pack(side='left',padx=8)
        ttk.Button(controls,text='Inspect record identity',command=self.history_identity).pack(side='left',padx=8)
        ttk.Button(controls,text='Investigation history',command=lambda:self.navigate('Investigations')).pack(side='right')
    def create_investigations(self):
        frame=ttk.Frame(self.stack,padding=18);frame.grid(row=0,column=0,sticky='nsew');self.views['Investigations']=frame
        ttk.Label(frame,text='Investigations',style='Brand.TLabel').pack(anchor='w')
        ttk.Label(frame,text='Real persisted objectives, checkpoints and evidence. Proposals remain unverified.',style='Muted.TLabel').pack(anchor='w',pady=10)
        self.investigation_list=tk.Listbox(frame,height=10);self.investigation_list.pack(fill='both',expand=True);self.investigations=[];self.investigation_cursor=0
        row=ttk.Frame(frame);row.pack(fill='x',pady=12)
        for label,cmd in [('Next objectives',self.load_investigations),('Inspect plan / checkpoint',self.inspect_investigation),('Checked findings',self.findings),('Open planned chat',self.open_planned)]:ttk.Button(row,text=label,command=cmd).pack(side='left',padx=3)
        controls=ttk.Frame(frame);controls.pack(fill='x')
        for label,action in [('Pause','pause'),('Resume local steps','resume'),('Cancel investigation','cancel')]:ttk.Button(controls,text=label,command=lambda action=action:self.control_investigation(action)).pack(side='left',padx=3)
        ttk.Label(frame,text='Resume uses a bounded local slice with zero model calls. Use Cancel above to interrupt an active operation.',style='Muted.TLabel',wraplength=700).pack(anchor='w',pady=8)
    def control_investigation(self,action):
        row=self.selected_investigation()
        if not row:return
        def refreshed(result):self.investigation_cursor=0;self.load_investigations()
        def current(state):
            def controlled(result):
                if action=='resume':self.app.call('investigation_run',{'id':row['id'],'approved':True,'budget':{'steps':16,'model_calls':0,'seconds':30}},refreshed)
                else:refreshed(result)
            self.app.call('investigation_control',{'id':row['id'],'revision':state['revision'],'action':action,'approved':True},controlled)
        self.app.call('investigation_get',{'id':row['id']},current)
    def finish(self):
        a=self.app
        for label,cmd in [('Import / learning',lambda:self.internal('Learning')),('Literary library',a.open_library)]:ttk.Button(a.tabs['Knowledge'],text=label,command=cmd).pack(anchor='w',pady=4)
        ttk.Button(a.tabs['Projects'],text='Investigations',command=lambda:self.navigate('Investigations')).pack(anchor='w',pady=5)
        ttk.Label(a.tabs['Assistant'],textvariable=a.project_status,style='Muted.TLabel',wraplength=720).grid(row=6,column=0,sticky='w',pady=(4,0))
        ttk.Button(a.tabs['Settings'],text='Storage, backups and diagnostics',command=lambda:self.navigate('Advanced')).pack(anchor='w',pady=8)
        self.reduced=tk.BooleanVar(value=os.environ.get('VECTOR_REDUCED_MOTION')=='1')
        ttk.Checkbutton(a.tabs['Settings'],text='Reduce motion / disable core animation',variable=self.reduced,command=self.set_motion_preference).pack(anchor='w',pady=10)
        # Backend diagnostics/storage remain available with original approval flows.
        ttk.Button(a.tabs['Tools'],text='Model and appearance settings',command=lambda:self.navigate('Settings')).pack(anchor='w')
        self.core.state(motion=not self.reduced.get());self.navigate('Home / Chat',load=False)
    def set_motion_preference(self):
        self.core.state(motion=not self.reduced.get());self.app.call('appearance_set',{'reduced_motion':self.reduced.get()})
    def inspect_active_plan(self):
        if getattr(self.app,'active_response',None):self.app.show_result(self.app.active_response)
        elif self.app.active_planning:self.app.show_result(self.app.active_planning['planning'])
    def document_text(self,document):
        if document.get('simulated'):return document['text']
        blocks=[]
        for finding,block in zip(document['findings'],document['blocks']):
            if finding['status']=='verified-computation' and finding['kind']=='deterministic-computation':
                op=finding['operation'];expression=op['parameters'].get('expression',op['tool']);value=finding['values'][0]
                rendered='Verified calculation: '+expression+' = '+str(value['value'])
                if value.get('unit') not in (None,'','1'):rendered+=' '+value['unit']
                if finding['dependencies']:rendered+='\nUses the earlier checked result.'
                rendered+='\n'+ ' '.join(finding['qualifications']);blocks.append(rendered)
            else:blocks.append(block['text'])
        return '\n\n'.join(blocks)
    def toggle_options(self):
        if self.options.winfo_ismapped():self.options.grid_remove()
        else:self.options.grid()
    def enter(self,event=None):self.app.send_chat();return 'break'
    def newline(self,event=None):self.app.question.insert('insert','\n');return 'break'
    def toggle_menu(self):
        if self.menu_open:self.hide_menu()
        else:
            self.menu.place(x=16,y=self.header.winfo_height()+8,width=278);self.menu.lift();self.menu_open=True;self.menu_buttons[0].focus_set()
    def hide_menu(self):
        if self.menu_open:self.menu.place_forget();self.menu_open=False;self.hamburger.focus_set()
    def dismiss(self,event):
        widget=event.widget
        while widget is not None:
            if widget in (self.menu,self.hamburger):return
            widget=getattr(widget,'master',None)
        if self.menu_open:self.menu.place_forget();self.menu_open=False
    def menu_focus(self,direction):
        current=self.app.root.focus_get();index=self.menu_buttons.index(current) if current in self.menu_buttons else 0;self.menu_buttons[(index+direction)%len(self.menu_buttons)].focus_set();return 'break'
    def navigate(self,name,load=True):
        if name not in self.views:raise ValueError('Unknown interface destination.')
        self.hide_menu();self.current=name;self.destination.set(name.upper());self.views[name].tkraise();self.core.state(visible=name=='Home / Chat')
        for key,button in self.nav.items():button.configure(style='Selected.TButton' if key==name else 'TButton')
        if load and not self.app.client.pending:
            if name=='Projects' and not self.app.project_rows:self.app.projects()
            elif name=='History' and not self.history_rows:self.browse_history()
            elif name=='Investigations' and not self.investigations:self.load_investigations()
    def internal(self,name):
        self.hide_menu();self.current=name;self.destination.set(name.upper());self.legacy[name].tkraise();self.core.state(visible=False)
    def pending(self):
        busy=bool(self.app.client.pending);self.core.state(busy=busy);self.send.configure(state='disabled' if busy else 'normal');self.cancel.configure(state='normal' if busy else 'disabled')
    def scroll_changed(self,first,last):
        self.follow=float(last)>=.995
        if self.follow:self.latest.grid_remove()
    def append(self,text,tag=None):
        chat=self.app.chat;follow=self.follow;position=chat.index('@0,0');chat.configure(state='normal');chat.insert('end',text+'\n\n',tag or ());chat.configure(state='disabled')
        if follow:chat.see('end')
        else:chat.yview(position);self.latest.grid()
        if not self.has_text:
            self.has_text=True;self.core.grid_configure(rowspan=1,sticky='ew');self.stream.grid();self.core.state(compact=True)
    def to_latest(self):self.app.chat.see('end');self.follow=True;self.latest.grid_remove()
    def reset(self):
        self.app.chat.configure(state='normal');self.app.chat.delete('1.0','end');self.app.chat.configure(state='disabled');self.follow=True;self.app.active_planning=None;self.has_text=False;self.stream.grid_remove();self.core.grid_configure(rowspan=2,sticky='nsew');self.core.state(compact=False)
    def browse_history(self):
        def loaded(result):
            self.history_rows=result['items'];self.history_cursor=result['next_cursor'] if result['items'] else 0;self.history_list.delete(*self.history_list.get_children())
            for i,row in enumerate(result['items']):self.history_list.insert('', 'end',iid=str(i),values=(row.get('created') or 'Legacy timestamp unavailable',row['question'],row['project_id'] or 'Global'))
        self.app.call('conversation_browse',{'after':self.history_cursor},loaded)
    def history_identity(self):
        selected=self.history_list.selection()
        if selected:self.app.show_result(self.history_rows[int(selected[0])])
    def open_history(self):
        selection=self.history_list.selection()
        if not selection:return
        row=self.history_rows[int(selection[0])]
        def loaded(result):
            self.app.active_project=result['project_id'];self.app.project_status.set('Active project: '+str(result['project_id']) if result['project_id'] else 'Global conversation');self.app.reset_history('Saved conversation resumed.');self.navigate('Home / Chat',load=False);self.app.load_history()
        self.app.call('conversation_resume',{'conversation_id':row['conversation_id']},loaded)
    def load_investigations(self):
        def loaded(result):
            self.investigations=result['items'];self.investigation_cursor=result['next_cursor'] if result['items'] else 0;self.investigation_list.delete(0,'end')
            for row in result['items']:self.investigation_list.insert('end',row['status']+' · '+row['goal'])
        self.app.call('investigation_list',{'after':self.investigation_cursor},loaded)
    def selected_investigation(self):
        selected=self.investigation_list.curselection();return self.investigations[selected[0]] if selected else None
    def inspect_investigation(self):
        row=self.selected_investigation()
        if row:self.app.call('investigation_get',{'id':row['id']},self.app.show_result)
    def findings(self):
        row=self.selected_investigation()
        if row:self.app.call('investigation_answer',{'id':row['id']},self.app.checked_answer);self.navigate('Home / Chat',load=False)
    def open_planned(self):
        row=self.selected_investigation()
        if not row:return
        def loaded(view):
            self.app.active_planning={'planning':view};self.navigate('Home / Chat',load=False);self.app.planned_answer(view)
        self.app.call('question_get',{'id':row['id']},loaded)
    def close(self):self.core.stop()
