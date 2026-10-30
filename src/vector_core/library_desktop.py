"""Real library workspace hosted by the existing protected local desktop."""
import json
from vector_core.literature import PG_NOTICE

class LiteraryDesktop:
    def __init__(self,app):
        self.app=app;self.tk=app.tk;self.ttk=app.ttk;self.selected=None;self.units={};self.editions={};self.offset=0;self.unit_cursor=-1;self.current_passage=None;self.stop_batch=False
        window=self.tk.Toplevel(app.root);self.window=window;window.title('VECTOR — Literary library');window.geometry('1000x700')
        self.notice=self.tk.StringVar(value='Originals and licenses are preserved. Interpretations are not established facts.')
        self.ttk.Label(window,textvariable=self.notice,wraplength=950).pack(fill='x',padx=10,pady=6)
        controls=self.ttk.Frame(window);controls.pack(fill='x',padx=10)
        self.query=self.ttk.Entry(controls,width=28);self.query.pack(side='left');self.language=self.ttk.Entry(controls,width=10);self.language.pack(side='left')
        for label,command in [('Titles',self.titles),('Passages',self.search),('Import pack',self.import_pack),('Languages',self.languages),('Status',lambda:app.call('library_stats',{},app.show_result))]:self.ttk.Button(controls,text=label,command=command).pack(side='left',padx=2)
        filters=self.ttk.Frame(window);filters.pack(fill='x',padx=10,pady=4);self.fields={}
        for name in ('author','subject','since','until'):
            self.ttk.Label(filters,text=name.title()).pack(side='left');entry=self.ttk.Entry(filters,width=18 if name in ('author','subject') else 8);entry.pack(side='left');self.fields[name]=entry
        notebook=self.ttk.Notebook(window);notebook.pack(fill='both',expand=True,padx=10,pady=6)
        browse=self.ttk.Frame(notebook);notebook.add(browse,text='Works and passages');self.listing=self.tk.Listbox(browse,height=7);self.listing.pack(fill='x');self.listing.bind('<<ListboxSelect>>',self.select)
        actions=self.ttk.Frame(browse);actions.pack(fill='x')
        for label,command in [('Next titles',self.next_titles),('Source & rights',self.rights),('Process / resume',self.process),('Body observations',self.body_observations),('Next passages',self.next_units),('Link to project',self.link_project),('Export original',self.export_original)]:self.ttk.Button(actions,text=label,command=command).pack(side='left',padx=2)
        from tkinter.scrolledtext import ScrolledText
        self.reader=ScrolledText(browse,wrap='word',height=13,state='disabled');self.reader.pack(fill='both',expand=True)
        analysis=self.ttk.Frame(browse);analysis.pack(fill='x')
        for label,command in [('Structure / poetry observations',self.observe),('Vocabulary proposals',self.vocabulary),('Add interpretation',self.annotate),('Historical layers',self.historical)]:self.ttk.Button(analysis,text=label,command=command).pack(side='left',padx=2)
        notes=self.ttk.Frame(notebook);notebook.add(notes,text='Knowledge / interpretation review');self.record_query=self.ttk.Entry(notes);self.record_query.pack(fill='x')
        bar=self.ttk.Frame(notes);bar.pack(fill='x')
        self.ttk.Button(bar,text='Find linguistic records',command=self.concepts).pack(side='left');self.ttk.Button(bar,text='Inspect selected',command=self.inspect_record).pack(side='left');self.ttk.Button(bar,text='Approve interpretation',command=self.review_record).pack(side='left');self.ttk.Button(bar,text='Link two records',command=self.relate).pack(side='left')
        self.record_list=self.tk.Listbox(notes,selectmode='extended');self.record_list.pack(fill='both',expand=True);self.records=[];self.reviewed=None
        resources=self.ttk.Frame(notebook);notebook.add(resources,text='Processing / resources')
        self.ttk.Button(resources,text='Process pending editions',command=self.process_pending).pack(anchor='w')
        self.ttk.Button(resources,text='Stop library batch',command=self.stop).pack(anchor='w')
        self.ttk.Button(resources,text='Processing status and errors',command=lambda:app.paged_records('Literary processing','library_processing',lambda r:r['status']+' — '+r['event_id'],app.show_result)).pack(anchor='w')
        self.ttk.Button(resources,text='Reset derived passage index (originals retained)',command=self.reset_index).pack(anchor='w')
        self.ttk.Button(resources,text='Import licensed CMU dictionary',command=self.dictionary).pack(anchor='w')
        self.ttk.Button(resources,text='Pronunciation reference',command=self.pronunciation).pack(anchor='w')
        self.ttk.Label(resources,text='No downloads occur in VECTOR. Import only reviewed offline packages.\nLanguage IDs describe a curriculum; grammar/translation proficiency remains unqualified.\nHistorical readings, glosses, translations and commentary remain separate source-linked records.',wraplength=900).pack(anchor='w',pady=10)
        self.titles()
    def parameters(self):
        p={'query':self.query.get(),'after':self.offset}
        if self.language.get():p['language']=self.language.get()
        for key,entry in self.fields.items():
            if entry.get():p[key]=entry.get()
        return p
    def titles(self):
        self.offset=0;self.load_titles()
    def next_titles(self):self.load_titles()
    def load_titles(self):
        def loaded(result):
            self.offset=result['next_cursor'] if result['items'] else 0;self.listing.delete(0,'end');self.editions={};self.units={}
            for i,row in enumerate(result['items']):self.listing.insert('end',row['metadata']['title'].replace('\n',' ')+' ['+row['metadata']['language']+']');self.editions[i]=row
        self.app.call('library_editions',self.parameters(),loaded)
    def select(self,event=None):
        selected=self.listing.curselection()
        if not selected:return
        index=selected[0]
        if index in self.editions:
            self.selected=self.editions[index];self.current_passage=None;self.unit_cursor=-1
            self.notice.set(PG_NOTICE if self.selected['metadata']['rights']['status']=='provider-unrestricted-us' else self.selected['metadata']['rights']['basis'])
            self.rights()
        elif index in self.units:self.app.call('library_passage',{'id':self.units[index]['id']},self.show_passage)
    def show_passage(self,record):
        self.selected={'id':record['edition_id'],'event_id':record['event_id'],'metadata':{'language':record['language'],'rights':{'status':record['rights_status'],'basis':record['rights_notice']}}};self.notice.set(record['rights_notice'])
        self.current_passage=record;self.reader.configure(state='normal');self.reader.delete('1.0','end');self.reader.insert('1.0',record['quote']);self.reader.configure(state='disabled')
        self.app.selected_event=record['event_id']
    def rights(self):
        if self.selected:self.app.call('library_edition',{'id':self.selected['id']},self.app.show_result)
    def search(self):
        p={'query':self.query.get()}
        if self.language.get():p['language']=self.language.get()
        def loaded(result):
            self.listing.delete(0,'end');self.editions={};self.units={}
            for i,row in enumerate(result['items']):self.listing.insert('end',row['name']+' — '+row['excerpt'][:100].replace('\n',' '));self.units[i]=row
            self.notice.set(next((r['rights_notice'] for r in result['items'] if r.get('rights_status')=='provider-unrestricted-us'),'Inspect source-specific rights before reuse.'))
        self.app.call('library_search',p,loaded)
    def next_units(self):
        if not self.selected:return
        def loaded(result):
            self.unit_cursor=result['next_cursor'] if result['items'] else -1;self.listing.delete(0,'end');self.editions={};self.units={}
            for i,row in enumerate(result['items']):self.listing.insert('end',str(row['ordinal'])+' — '+row['kind']);self.units[i]=row
        self.app.call('library_units',{'event_id':self.selected['event_id'],'after':self.unit_cursor},loaded)
    def body_observations(self):
        if self.selected:self.app.call('library_observations',{'event_id':self.selected['event_id']},self.app.show_result)
    def process(self):
        self.stop_batch=False
        if not self.selected:return
        event=self.selected['event_id']
        def completed(result):
            self.app.status.set('Literary processing: '+result['status']+' / '+str(result['ordinal'])+' units')
            if result['status']=='partial' and not self.stop_batch and self.window.winfo_exists():self.window.after(20,lambda:self.app.call('library_process',{'event_id':event},completed))
        self.app.call('library_process',{'event_id':event},completed)
    def stop(self):
        self.stop_batch=True;self.app.client.cancel()
    def process_pending(self):
        self.stop_batch=False;state={'after':0,'queue':[]}
        def step():
            if self.stop_batch or not self.window.winfo_exists():return
            if state['queue']:
                event=state['queue'][0]
                def processed(result):
                    self.app.status.set('Library: '+result['status']+' / '+str(result['ordinal'])+' units')
                    if result['status']!='partial':state['queue'].pop(0)
                    self.window.after(20,step)
                self.app.call('library_process',{'event_id':event},processed)
            else:
                def page(result):
                    state['queue']=[r['event_id'] for r in result['items'] if r['status'] in ('pending','partial','failed')]
                    state['after']=result['next_cursor']
                    if result['items']:self.window.after(20,step)
                    else:self.app.status.set('Library processing scan complete; deferred editions remain explicit.')
                self.app.call('library_processing',{'after':state['after']},page)
        step()
    def import_pack(self):
        directory=self.app.files.askdirectory(title='Select reviewed offline literature package')
        if not directory or not self.app.dialog.askyesno('Approve local package and rights','Import this reviewed package? PG works are U.S.-only provider assertions; all originals and license evidence are retained. No network request is made.'):return
        self.stop_batch=False;state={'offset':0,'count':0,'fingerprint':None}
        def completed(result):
            state['count']+=len(result['items']);state['offset']=result['next_cursor'];state['fingerprint']=result['fingerprint'];self.app.status.set('Imported / reused '+str(state['count'])+' editions; sources retained.')
            if not result['complete'] and not self.stop_batch and self.window.winfo_exists():self.window.after(20,step)
        def step():self.app.call('library_import',{'directory':directory,'offset':state['offset'],'fingerprint':state['fingerprint'],'approved':True},completed)
        step()
    def languages(self):self.app.paged_records('Language curriculum','library_languages',lambda r:r['payload']['name']+' — '+r['payload']['coverage'],self.app.show_result)
    def link_project(self):
        if self.selected:self.app.selected_event=self.selected['event_id'];self.app.link_selected_project()
    def export_original(self):
        if self.current_passage:self.app.selected_event=self.current_passage['event_id']
        elif self.selected:self.app.selected_event=self.selected['event_id']
        self.app.export_original()
    def observe(self):
        if self.current_passage:self.app.call('library_observe',{'event_id':self.current_passage['event_id'],'start':self.current_passage['start'],'end':self.current_passage['end']},self.app.show_result)
    def vocabulary(self):
        if self.current_passage:self.app.call('library_vocabulary',{'event_id':self.current_passage['event_id'],'start':self.current_passage['start'],'end':self.current_passage['end'],'language':self.language.get() or (self.selected['metadata']['language'] if self.selected else 'und'),'approved':True},self.app.show_result)
    def annotate(self):
        if not self.current_passage:return
        window=self.tk.Toplevel(self.window);window.title('Source-linked interpretation')
        kind=self.tk.StringVar(value='commentary');self.ttk.Combobox(window,textvariable=kind,values=('morphology','gloss','translation','transliteration','textual_variant','theme','metaphor','grammar','ambiguity','idiom','etymology','commentary'),state='readonly').pack(fill='x')
        label=self.ttk.Entry(window);label.pack(fill='x');self.ttk.Label(window,text='Interpretation / alternatives (not a verified fact)').pack(anchor='w');body=self.tk.Text(window,height=6);body.pack(fill='both',expand=True)
        self.ttk.Label(window,text='Uncertainty / disagreement').pack(anchor='w');uncertainty=self.ttk.Entry(window);uncertainty.pack(fill='x')
        def save():
            p=self.current_passage;a={k:p[k] for k in ('event_id','start','end','quote','sha256')}
            self.app.call('library_annotate',{'language':self.language.get() or 'und','kind':kind.get(),'label':label.get(),'features':{'interpretation':body.get('1.0','end-1c')},'attestations':[a],'uncertainty':uncertainty.get(),'approved':True},self.app.show_result)
        self.ttk.Button(window,text='Submit pending interpretation',command=save).pack(anchor='w')
    def historical(self):
        language=self.language.get()
        self.app.call('library_historical',{'language':language},self.app.show_result)
    def concepts(self):
        def loaded(result):
            self.records=result['items'];self.record_list.delete(0,'end');self.reviewed=None
            for row in self.records:self.record_list.insert('end',row['label']+' ['+row['language']+'] — '+row['status'])
        self.app.call('library_concepts',{'query':self.record_query.get(),'language':self.language.get() or None},loaded)
    def inspect_record(self):
        selected=self.record_list.curselection()
        if selected:
            row=self.records[selected[0]]
            def inspected(result):self.reviewed=result;self.app.show_result(result)
            self.app.call('library_record',{'id':row['id']},inspected)
    def review_record(self):
        selected=self.record_list.curselection()
        if not selected or not self.reviewed or self.records[selected[0]]['id']!=self.reviewed['id']:self.app.dialog.showinfo('Inspect first','Inspect exact source attestations before approval.');return
        if self.app.dialog.askyesno('Approve interpretation','Record human approval? The interpretation remains source-linked and is not established truth.'):
            self.app.call('library_review',{'id':self.reviewed['id'],'revision':self.reviewed['revision'],'accept':True,'approved':True},self.app.show_result)
    def relate(self):
        selected=self.record_list.curselection()
        if len(selected)!=2:self.app.dialog.showinfo('Select two','Select two linguistic records to relate.');return
        window=self.tk.Toplevel(self.window);window.title('Explicit concept relationship');relation=self.tk.StringVar(value='uncertain');self.ttk.Combobox(window,textvariable=relation,values=('exact-equivalence','approximate-translation','related-meaning','etymological','borrowing','uncertain'),state='readonly').pack(fill='x')
        self.ttk.Label(window,text='Reason and source interpretation').pack(anchor='w');reason=self.ttk.Entry(window);reason.pack(fill='x');uncertainty=self.ttk.Entry(window);uncertainty.insert(0,'User interpretation; not independently verified.');uncertainty.pack(fill='x')
        self.ttk.Button(window,text='Save explicit relationship',command=lambda:self.app.call('library_relate',{'left':self.records[selected[0]]['id'],'right':self.records[selected[1]]['id'],'relation':relation.get(),'reason':reason.get(),'uncertainty':uncertainty.get(),'approved':True},self.app.show_result)).pack(anchor='w')
    def reset_index(self):
        if self.app.dialog.askyesno('Rebuild derived index','Reset only derived literary passages/postings? All originals, interpretations and histories remain. Reprocess editions afterwards.'):
            self.app.call('library_reset_index',{'approved':True},self.app.show_result)
    def dictionary(self):
        self.stop_batch=False
        file=self.app.files.askopenfilename(title='Select local CMUdict data');license_file=self.app.files.askopenfilename(title='Select its complete CMU license') if file else None
        if not license_file:return
        def completed(result):
            self.app.status.set('Pronunciation entries: '+str(result['entries']))
            if not result['complete'] and not self.stop_batch and self.window.winfo_exists():self.window.after(20,step)
        def step():self.app.call('library_dictionary_import',{'file':file,'license_file':license_file,'approved':True},completed)
        if self.app.dialog.askyesno('Import pronunciation resource','Import the dictionary and its license as source data, without model training?'):step()
    def pronunciation(self):
        word=self.app.simple.askstring('Pronunciation','English written word:')
        if word:self.app.call('library_pronunciation',{'word':word},self.app.show_result)
