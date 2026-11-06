"""Embedded native botanical workspace; uses the existing Library original reader."""
import json
from vector_core.botany import PREFERENCES,REGION,AVAILABILITY,KINDS,NOTICE

class BotanicalDesktop:
    def __init__(self,library):
        self.library=library;self.app=library.app;self.tk=library.tk;self.ttk=library.ttk
        self.frame=self.ttk.Frame(library.parent);self.cursor=0;self.next_cursor=None;self.stack=[];self.rows={};self.current=None;self.preferences=None
        head=self.ttk.Frame(self.frame);head.pack(fill='x')
        self.ttk.Button(head,text='← Library',command=self.back).pack(side='left')
        self.ttk.Label(head,text='BOTANICAL RESEARCH',style='Brand.TLabel').pack(side='left',padx=10)
        self.ttk.Button(head,text='Region / climate',command=self.region_dialog).pack(side='right')
        self.preference=self.tk.StringVar(value=PREFERENCES[0]);box=self.ttk.Combobox(head,textvariable=self.preference,values=PREFERENCES,state='readonly',width=22);box.pack(side='right',padx=5);box.bind('<<ComboboxSelected>>',lambda e:self.save_preference())
        bar=self.ttk.Frame(self.frame);bar.pack(fill='x',pady=6)
        self.query=self.ttk.Entry(bar);self.query.pack(side='left',fill='x',expand=True);self.query.bind('<Return>',lambda e:self.search())
        self.kind=self.tk.StringVar(value='taxon');self.ttk.Combobox(bar,textvariable=self.kind,values=('All',*KINDS),state='readonly',width=13).pack(side='left',padx=3)
        self.availability=self.tk.StringVar(value='Any availability');self.ttk.Combobox(bar,textvariable=self.availability,values=('Any availability',*AVAILABILITY),state='readonly',width=23).pack(side='left',padx=3)
        self.ttk.Button(bar,text='Search',style='Accent.TButton',command=self.search).pack(side='left')
        self.use_region=self.tk.BooleanVar(value=False);self.ttk.Checkbutton(self.frame,text='Filter distribution records by saved region (no inferred local presence)',variable=self.use_region,command=self.search).pack(anchor='w')
        self.notice=self.tk.StringVar(value=NOTICE);self.ttk.Label(self.frame,textvariable=self.notice,style='Muted.TLabel',wraplength=1000).pack(fill='x',pady=4)
        pane=self.ttk.Panedwindow(self.frame,orient='horizontal');pane.pack(fill='both',expand=True)
        left=self.ttk.Frame(pane);right=self.ttk.Frame(pane);pane.add(left,weight=1);pane.add(right,weight=2)
        self.listing=self.ttk.Treeview(left,columns=('title','kind'),show='headings',selectmode='browse')
        for n,w in [('title',250),('kind',85)]:self.listing.heading(n,text=n.title());self.listing.column(n,width=w,minwidth=50)
        self.listing.pack(side='left',fill='both',expand=True);sb=self.ttk.Scrollbar(left,command=self.listing.yview);sb.pack(side='right',fill='y');self.listing.configure(yscrollcommand=sb.set);self.listing.bind('<<TreeviewSelect>>',lambda e:self.select())
        from tkinter.scrolledtext import ScrolledText
        from vector_core.desktop_theme import COLORS as C
        self.body=ScrolledText(right,wrap='word',font=('DejaVu Sans',11),background=C['surface'],foreground=C['text'],insertbackground=C['cyan'],relief='flat',state='disabled');self.body.pack(fill='both',expand=True)
        self.sources=self.ttk.Frame(right);self.sources.pack(fill='x')
        actions=self.ttk.Frame(self.frame);actions.pack(fill='x',pady=5)
        self.ttk.Button(actions,text='← Previous',command=self.previous).pack(side='left');self.ttk.Button(actions,text='Next →',command=self.next).pack(side='left',padx=4)
        self.question=self.ttk.Entry(actions);self.question.pack(side='left',fill='x',expand=True,padx=4)
        self.ttk.Button(actions,text='Local AI research',command=self.research).pack(side='right')
        self.ttk.Button(actions,text='Cited evidence',command=lambda:self.research(True)).pack(side='right',padx=4)
    def call(self,op,p,callback):self.library.call(op,p,callback)
    def show(self):
        self.library.catalog.pack_forget();self.library.reader.pack_forget();self.frame.pack(fill='both',expand=True)
        self.call('botany_preferences_get',{},self.loaded_preferences);self.search()
    def back(self):self.frame.pack_forget();self.library.catalog.pack(fill='both',expand=True)
    def loaded_preferences(self,p):self.preferences=p;self.preference.set(p['preference'])
    def save_preference(self):
        if self.preferences is None:return
        p={**self.preferences,'preference':self.preference.get()};self.call('botany_preferences_set',p,self.loaded_preferences)
        if self.current:self.call('botany_detail',{'id':self.current},self.detail)
    def region_dialog(self):
        if self.preferences is None:return
        from tkinter import simpledialog
        parent=self.frame.winfo_toplevel();result={}
        for name in REGION:
            value=simpledialog.askstring('Research region',name.title()+' (blank = unknown / unrestricted)',initialvalue=self.preferences['region'][name] or '',parent=parent)
            if value is None:return
            result[name]=value.strip() or None
        self.call('botany_preferences_set',{'preference':self.preference.get(),'region':result},self.loaded_preferences)
    def search(self):self.cursor=0;self.stack=[];self.load()
    def load(self):
        p={'query':self.query.get(),'after':self.cursor}
        if self.kind.get()!='All':p['kind']=self.kind.get()
        if self.use_region.get():
            if self.preferences is None:return
            p['region']=self.preferences['region'];p['kind']='distribution'
        if self.availability.get()!='Any availability':p['availability']=self.availability.get();p['kind']='distribution'
        self.call('botany_list',p,self.results)
    def results(self,r):
        self.rows={};self.listing.delete(*self.listing.get_children());self.next_cursor=r['next_cursor']
        for i,item in enumerate(r['items']):
            k=str(i);self.rows[k]=item;self.listing.insert('','end',iid=k,values=(item['title'],item['kind']))
        self.notice.set(str(len(r['items']))+' records on this page. '+r['notice'])
    def next(self):
        if self.next_cursor is not None:self.stack.append(self.cursor);self.cursor=self.next_cursor;self.load()
    def previous(self):
        if self.stack:self.cursor=self.stack.pop();self.load()
    def select(self):
        selection=self.listing.selection()
        if selection:self.current=self.rows[selection[0]]['id'];self.call('botany_detail',{'id':self.current},self.detail)
    def detail(self,d):
        r=d['record'];lines=[r['title'],r['kind'].upper()+' • reviewed '+r['reviewed'],'',r['uncertainty'],'',NOTICE,'']
        def render(item):
            lines.extend([item['title'],'['+item['kind']+']'])
            for name,value in item['data'].items():
                if name in {'asset_events','rights_evidence'}:continue
                lines.append(name.replace('_',' ').title()+': '+('Unknown / not established' if value is None else json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else str(value)))
            lines.extend(['Uncertainty: '+item['uncertainty']])
            for c in item['citations']:lines.append('SOURCE '+c['event_id']+' ['+str(c['start'])+':'+str(c['end'])+']\n“'+c['quote']+'”')
            lines.append('')
        render(r)
        for item in d['related']:render(item)
        if d['related_truncated']:lines.append('More than 200 related records. Narrow the query; model synthesis is blocked until essential safety material can be included.')
        self.body.configure(state='normal');self.body.delete('1.0','end');self.body.insert('1.0','\n'.join(lines));self.body.configure(state='disabled')
        for widget in self.sources.winfo_children():widget.destroy()
        events=[]
        for item in [r,*d['related']]:
            if item['kind'] in {'image','document'}:events.append((item['title'],item['data']['event_id'],0))
            events.extend(('Source '+c['event_id'][:8],c['event_id'],c['start']) for c in item['citations'])
        if r['kind']=='source':events.extend(('Original '+e[:8],e,0) for e in r['data']['asset_events'])
        unique=list(dict.fromkeys(events))
        # A selector keeps sources accessible without hundreds of GUI widgets.
        if unique:
            self.source_choices=unique;self.source_choice=self.tk.StringVar(value=unique[0][0])
            self.ttk.Combobox(self.sources,textvariable=self.source_choice,values=tuple(x[0]+' ['+str(i)+']' for i,x in enumerate(unique)),state='readonly').pack(side='left',fill='x',expand=True)
            self.source_choice.set(unique[0][0]+' [0]');self.ttk.Button(self.sources,text='Open local source / image',command=self.open_source).pack(side='right')
    def open_source(self):
        i=int(self.source_choice.get().rsplit('[',1)[1][:-1]);_,event,start=self.source_choices[i]
        self.frame.pack_forget();self.app.open_resource_reference(event,start)
    def research(self,evidence_only=False):
        if not self.current:self.notice.set('Select a botanical subject first.');return
        q=self.question.get().strip()
        if not q:self.notice.set('Enter a research question.');return
        self.call('botany_research',{'id':self.current,'question':q,'evidence_only':evidence_only},self.app.show_result)
