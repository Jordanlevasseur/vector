"""Native Library destination: catalogue, originals, reading and owner organization."""
from collections import deque
import json
from pathlib import Path

class ResourceDesktop:
    def __init__(self,app,parent):
        self.app=app;self.tk=app.tk;self.ttk=app.ttk;self.parent=parent;self.loaded=False;self.rows={};self.cursor=0;self.previous=[];self.next_cursor=None;self.collection_ids={'All collections':''};self.queue=deque();self.timer=None
        self.key=None;self.member='';self.kind=None;self.offset=0;self.page=1;self.pages=1;self.next_offset=None;self.font_size=12;self.scroll=0.;self.width=850;self.epoch=0;self.find_after=0;self.find_page=1;self.last_query='';self.save_timer=None;self.image=None
        self.catalog=self.ttk.Frame(parent);self.catalog.pack(fill='both',expand=True);self.reader=self.ttk.Frame(parent)
        self.loading=False;self.catalog_epoch=0;self.search_timer=None;self.scroll_timer=None;self.window_start=0;self.window_limit=200;self.total=0;self.browse_y=0.;self.restoring=False;self.category_choices={};self.shelf_view='bookshelf';self.shelf_pages=[];self.page_history={}
        heading=self.ttk.Frame(self.catalog);heading.pack(fill='x',pady=(4,10));self.ttk.Label(heading,text='Library',style='Heading.TLabel').pack(side='left')
        self.count=self.tk.StringVar(value='Your downloaded books and documents');self.ttk.Label(heading,textvariable=self.count,style='Muted.TLabel').pack(side='left',padx=14)
        self.botanical=None;self.more=self.ttk.Menubutton(heading,text='More ▾');self.more.pack(side='right');menu=self.tk.Menu(self.more,tearoff=False);self.more.configure(menu=menu)
        for label,command in [('Botanical research',self.open_botanical),('New manual',self.edit_manual),('New collection',self.new_collection),('Details',self.details),('Edit manual',self.edit_selected_manual),('Export original',self.export),('Add to collection',self.add_collection),('Remove from collection',self.remove_collection),('Advanced filters',self.toggle_advanced),('All stored records',lambda:self.change_view('all')),('Bookshelf',lambda:self.change_view('bookshelf')),('Coverage',lambda:self.call('resource_inventory',{},app.show_result)),('Refresh',self.search)]:menu.add_command(label=label,command=command)
        filters=self.ttk.Frame(self.catalog);filters.pack(fill='x',pady=(0,8));self.ttk.Label(filters,text='Search',style='Muted.TLabel').pack(side='left',padx=(0,7));self.query_value=self.tk.StringVar();self.query=self.ttk.Entry(filters,textvariable=self.query_value);self.query.pack(side='left',fill='x',expand=True,padx=(0,10));self.query.bind('<Return>',lambda e:self.search());self.query_value.trace_add('write',lambda *args:self.defer_search())
        self.filters={}
        for name,values,width in [('category',('All Books',),27),('sort',('Title A–Z','Title Z–A','Author','Recently added','Recently opened'),18)]:
            var=self.tk.StringVar(value=values[0]);box=self.ttk.Combobox(filters,textvariable=var,values=values,state='readonly',width=width);box.pack(side='left',padx=(0,5));box.bind('<<ComboboxSelected>>',lambda e:self.search());self.filters[name]=(var,box)
        self.advanced=self.ttk.Frame(self.catalog)
        self.search_mode=self.tk.StringVar(value='Titles / metadata');self.ttk.Combobox(self.advanced,textvariable=self.search_mode,values=('Titles / metadata','Indexed content'),state='readonly',width=20).pack(side='left')
        for name,values,width in [('format',('All formats',),13),('collection',('All collections',),28)]:
            var=self.tk.StringVar(value=values[0]);box=self.ttk.Combobox(self.advanced,textvariable=var,values=values,state='readonly',width=width);box.pack(side='left',padx=5);box.bind('<<ComboboxSelected>>',lambda e:self.search());self.filters[name]=(var,box)
        self.search_button=self.ttk.Button(self.advanced,text='Search',command=self.search);self.search_button.pack(side='left')
        self.notice=self.tk.StringVar(value='Books load automatically. Search is optional.');self.notice_label=self.ttk.Label(self.catalog,textvariable=self.notice,style='Muted.TLabel',wraplength=940);self.notice_label.pack(anchor='w',pady=4)
        self.retry_button=self.ttk.Button(self.catalog,text='Retry loading Library',command=self.search)
        table=self.ttk.Frame(self.catalog);table.pack(fill='both',expand=True)
        self.book_icon=self.tk.PhotoImage(width=20,height=26);self.book_icon.put('#19a9b5',to=(2,1,18,25));self.book_icon.put('#17313c',to=(5,3,17,23));self.book_icon.put('#b3d9df',to=(8,6,15,7));self.book_icon.put('#b3d9df',to=(8,10,15,11))
        style=self.ttk.Style();style.configure('Bookshelf.Treeview',rowheight=40)
        self.listing=self.ttk.Treeview(table,columns=('title','author','category','format','reading'),show='tree headings',style='Bookshelf.Treeview',selectmode='browse');self.listing.column('#0',width=32,minwidth=32,stretch=False);self.listing.heading('#0',text='')
        for name,width,label in [('title',290,'Title'),('author',135,'Author'),('category',135,'Collection'),('format',60,'Format'),('reading',90,'Reading')]:self.listing.heading(name,text=label);self.listing.column(name,width=width,minwidth=50,stretch=name=='title')
        self.listing.pack(side='left',fill='both',expand=True);self.scrollbar=self.ttk.Scrollbar(table,command=self.listing.yview);self.scrollbar.pack(side='right',fill='y');self.listing.configure(yscrollcommand=self.scrolled)
        self.listing.bind('<ButtonRelease-1>',self.click_book);self.listing.bind('<Return>',lambda e:self.open_selected());self.listing.bind('<<TreeviewSelect>>',lambda e:self.selection_notice())
        # Preserve the original command for keyboard/accessibility and callers;
        # ordinary browsing opens a real original with a single click.
        self.open_button=self.ttk.Button(self.catalog,text='Read original',command=self.open_selected)
        top=self.ttk.Frame(self.reader);top.pack(fill='x');self.back_button=self.ttk.Button(top,text='← Library',command=self.back);self.back_button.pack(side='left')
        self.title=self.tk.StringVar();self.ttk.Label(top,textvariable=self.title,style='Heading.TLabel',wraplength=450).pack(side='left',fill='x',expand=True,padx=10)
        self.ttk.Button(top,text='Source details',command=lambda:self.call('resource_detail',{'id':self.key},app.show_result) if self.key else None).pack(side='right')
        controls=self.ttk.Frame(self.reader);controls.pack(fill='x',pady=7)
        self.previous_button=self.ttk.Button(controls,text='← Previous',command=lambda:self.turn(-1));self.previous_button.pack(side='left')
        self.next_button=self.ttk.Button(controls,text='Next →',command=lambda:self.turn(1));self.next_button.pack(side='left',padx=3)
        self.jump=self.ttk.Entry(controls,width=9);self.jump.pack(side='left',padx=3);self.jump.bind('<Return>',lambda e:self.jump_to());self.ttk.Button(controls,text='Go',command=self.jump_to).pack(side='left')
        for label,command in [('A−',lambda:self.font(-1)),('A+',lambda:self.font(1)),('Zoom −',lambda:self.zoom(-150)),('Zoom +',lambda:self.zoom(150))]:self.ttk.Button(controls,text=label,command=command).pack(side='left',padx=2)
        tools=self.ttk.Frame(self.reader);tools.pack(fill='x',pady=(0,5))
        for label,command in [('Bookmark',self.bookmark),('Bookmarks',self.bookmarks),('Sections / package files',self.sections)]:self.ttk.Button(tools,text=label,command=command).pack(side='left',padx=2)
        search=self.ttk.Frame(self.reader);search.pack(fill='x',pady=(0,5));self.find_entry=self.ttk.Entry(search);self.find_entry.pack(side='left',fill='x',expand=True);self.find_entry.bind('<Return>',lambda e:self.find());self.find_button=self.ttk.Button(search,text='Find next in original',command=self.find);self.find_button.pack(side='left',padx=4)
        self.raw=self.tk.BooleanVar(value=False);self.ttk.Checkbutton(search,text='Raw markup',variable=self.raw,command=self.render).pack(side='left')
        self.reader_notice=self.tk.StringVar();self.ttk.Label(self.reader,textvariable=self.reader_notice,style='Muted.TLabel',wraplength=940).pack(anchor='w',pady=3)
        self.body=self.ttk.Frame(self.reader);self.body.pack(fill='both',expand=True)
        from tkinter.scrolledtext import ScrolledText
        from vector_core.desktop_theme import COLORS as C
        self.text=ScrolledText(self.body,wrap='word',font=('DejaVu Sans',12),background=C['surface'],foreground=C['text'],insertbackground=C['cyan'],relief='flat',padx=18,pady=14,state='disabled')
        self.text.bind('<MouseWheel>',lambda e:self.schedule_save(),add='+');self.text.bind('<ButtonRelease-1>',lambda e:self.schedule_save(),add='+');self.text.bind('<KeyRelease>',lambda e:self.schedule_save(),add='+')
        self.canvas_frame=self.ttk.Frame(self.body);self.canvas=self.tk.Canvas(self.canvas_frame,background=C['background'],highlightthickness=0)
        sy=self.ttk.Scrollbar(self.canvas_frame,orient='vertical',command=self.canvas.yview);sx=self.ttk.Scrollbar(self.canvas_frame,orient='horizontal',command=self.canvas.xview);self.canvas.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');self.canvas_frame.rowconfigure(0,weight=1);self.canvas_frame.columnconfigure(0,weight=1)
        self.canvas.bind('<ButtonRelease-1>',lambda e:self.schedule_save(),add='+')
        self.canvas.configure(yscrollcommand=lambda a,b:(sy.set(a,b),self.schedule_save()))
        self.text.configure(yscrollcommand=lambda a,b:(self.text.vbar.set(a,b),self.schedule_save()))
        for event,delta in [('<Button-4>',-3),('<Button-5>',3)]:self.canvas.bind(event,lambda e,d=delta:self.canvas.yview_scroll(d,'units'))
        self.member_list=self.tk.Listbox(self.body,background=C['surface'],foreground=C['text'],selectbackground=C['selection'],font=('DejaVu Sans',12));self.member_list.bind('<Double-1>',lambda e:self.open_member());self.member_list.bind('<Return>',lambda e:self.open_member())
        self.member_actions=self.ttk.Frame(self.reader);self.ttk.Button(self.member_actions,text='Open selected file',command=self.open_member).pack(side='left');self.ttk.Button(self.member_actions,text='Next files',command=self.more_members).pack(side='left',padx=4);self.ttk.Button(self.member_actions,text='Export original package',command=self.export).pack(side='left',padx=4)
    def open_botanical(self):
        if self.botanical is None:
            from vector_core.botany_desktop import BotanicalDesktop
            self.botanical=BotanicalDesktop(self)
        self.botanical.show()

    def call(self,op,p,callback=None,on_error=None):
        if len(self.queue)>=16:
            if on_error:on_error('Wait for the current Library operation, then retry.')
            else:self.notice.set('Wait for the current Library operation.')
            return
        self.queue.append((op,p,callback,on_error));self.pump()
    def pump(self):
        if self.timer is not None:return
        def step():
            self.timer=None
            if not self.parent.winfo_exists():return
            if not self.app.client.pending and self.queue:
                op,p,callback,on_error=self.queue.popleft();self.app.call(op,p,callback,on_error=on_error)
            if self.queue:self.timer=self.app.root.after(80,step)
        step()
    def toggle_advanced(self):
        if self.advanced.winfo_manager():self.advanced.pack_forget()
        else:self.advanced.pack(fill='x',before=self.notice_label,pady=5)
    def change_view(self,view):
        self.shelf_view=view;self.filters['category'][0].set('All Books');self.search_mode.set('Titles / metadata');self.search()
    def defer_search(self):
        if self.search_timer is not None:self.app.root.after_cancel(self.search_timer)
        self.search_timer=self.app.root.after(250,self.search)
    def enter(self):
        if not self.loaded and not self.loading:self.search()
    def search(self):
        if self.search_timer is not None:self.app.root.after_cancel(self.search_timer);self.search_timer=None
        if getattr(self.app,'backend_error',None):self.catalog_failed(self.app.backend_error);return
        self.catalog_epoch+=1;self.cursor=0;self.previous=[];self.next_cursor=None;self.window_start=0;self.shelf_pages=[];self.page_history={};self.rows={};self.listing.delete(*self.listing.get_children());self.retry_button.pack_forget()
        self.notice.set('Loading your Library…');self.count.set('Loading books and documents…')
        if not self.loading:self.load()
    def catalog_failed(self,error,token=None):
        self.loading=False;self.loaded=False
        if token is not None and token!=self.catalog_epoch:self.load();return
        self.notice.set('Could not load Library: '+str(error)[:400]+'. Retry, or restart VECTOR if the application is unavailable.');self.count.set('Library unavailable');self.retry_button.pack(anchor='w',before=self.notice_label,pady=4)
    def load(self,after=0,direction='replace'):
        if self.loading:return
        self.loading=True;token=self.catalog_epoch
        if self.search_mode.get()=='Indexed content' and self.query.get().strip():
            self.call('resource_search',{'query':self.query.get()},lambda r:self.content_rows(r,token),lambda error:self.catalog_failed(error,token));return
        order={'Title A–Z':'title','Title Z–A':'title_desc','Author':'author','Recently added':'newest','Recently opened':'recent'}
        p={'query':self.query.get(),'after':after,'limit':40,'sort':order.get(self.filters['sort'][0].get(),self.filters['sort'][0].get()),'view':self.shelf_view}
        category=self.filters['category'][0].get();choice=self.category_choices.get(category)
        if choice:
            p.update(choice)
        elif category not in ('All Books','All categories'):p['category']=category
        value=self.filters['format'][0].get()
        if value!='All formats':p['format']=value
        collection=self.filters['collection'][0].get()
        if self.collection_ids.get(collection):p['collection']=self.collection_ids[collection]
        self.call('resource_list',p,lambda r:self.catalog_rows(r,token,after,direction),lambda error:self.catalog_failed(error,token))
    def catalog_rows(self,r,token=None,after=0,direction='replace'):
        self.loading=False
        if token is not None and token!=self.catalog_epoch:self.load();return
        self.loaded=True;self.total=r['total'];self.retry_button.pack_forget();old=list(self.listing.get_children());fraction=float(self.listing.yview()[0]) if old else 0.;anchor=old[min(len(old)-1,int(fraction*len(old)))] if old else None
        selected=self.listing.selection()
        if direction=='replace':self.shelf_pages=[]
        if direction=='backward':self.shelf_pages.insert(0,(after,r['items'],r['next_cursor']))
        else:self.shelf_pages.append((after,r['items'],r['next_cursor']))
        if r['next_cursor'] is not None:self.page_history[r['next_cursor']]=after
        if len(self.shelf_pages)>5:self.shelf_pages.pop(-1 if direction=='backward' else 0)
        self.rows={};self.listing.delete(*old)
        for page_start,items,next_page in self.shelf_pages:
            for i,row in enumerate(items):
                key=str(page_start+i);state=row.get('reading');progress=('Page '+str(state['page']) if row['format']=='PDF' else 'In progress' if state.get('offset') or state.get('scroll') else 'Opened') if state else ''
                self.rows[key]=row;self.listing.insert('', 'end',iid=key,image=self.book_icon,values=(row['title'],'; '.join(row['authors']),self.category_label(row['category']),row['format'],progress))
        children=list(self.listing.get_children());self.window_start=self.shelf_pages[0][0];self.next_cursor=self.shelf_pages[-1][2]
        if selected and selected[0] in self.rows:self.listing.selection_set(selected[0])
        self.restoring=True
        if anchor in children:self.listing.yview_moveto(children.index(anchor)/max(1,len(children)))
        elif direction=='replace':self.listing.yview_moveto(0)
        self.app.root.after_idle(lambda:setattr(self,'restoring',False))
        self.count.set(str(r.get('catalogue_total',r['total']))+' books and documents' if self.shelf_view=='bookshelf' else str(r.get('catalogue_total',r['total']))+' stored records')
        self.notice.set(('No matching books. Clear the search or choose All Books.' if not self.total else str(self.total)+' matching books and documents · Scroll to browse · Click to read the original') if self.query.get().strip() or self.filters['category'][0].get() not in ('All Books','All categories') else 'All Books · '+str(self.total)+' books and documents · Entirely local')
        categories=r.get('category_counts',{c:0 for c in r['categories']});collections=r.get('collection_counts',{});self.category_choices={}
        labels=['All Books']
        for category,count in sorted(categories.items(),key=lambda item:self.category_label(item[0])):
            label=self.category_label(category)+' ('+str(count)+')';labels.append(label);self.category_choices[label]={'category':category}
        for collection in r['collections']:
            count=collections.get(collection['id'],0)
            if count:
                label=collection['name']+' ('+str(count)+')'
                if label in self.category_choices:label+=' · collection'
                labels.append(label);self.category_choices[label]={'collection':collection['id']}
        self.filters['category'][1].configure(values=tuple(labels));self.filters['format'][1].configure(values=('All formats',*r['formats']))
        self.collection_ids={'All collections':''};self.collection_ids.update({c['name']+' ['+c['id'][:6]+']':c['id'] for c in r['collections']});self.filters['collection'][1].configure(values=tuple(self.collection_ids))
    @staticmethod
    def category_label(value):return {'Books':'Literature','Botanical sources':'Natural Medicine'}.get(value,value)
    def content_rows(self,r,token=None):
        self.loading=False
        if token is not None and token!=self.catalog_epoch:self.load();return
        self.count.set(str(len(r['items']))+' indexed matches')
        self.loaded=True;self.next_cursor=None;self.rows={};self.listing.delete(*self.listing.get_children())
        for i,row in enumerate(r['items']):
            key=str(i);self.rows[key]={**row,'id':row['resource_id'],'content_hit':True};self.listing.insert('', 'end',iid=key,image=self.book_icon,values=(row['title'],'','Indexed content','',''))
        self.notice.set(str(len(r['items']))+' indexed matches. Clear the search to return to your books.')
    def scrolled(self,first,last):
        self.scrollbar.set(first,last)
        if self.restoring or self.loading or self.search_timer is not None or self.search_mode.get()=='Indexed content' and self.query.get().strip():return
        if self.scroll_timer is not None:self.app.root.after_cancel(self.scroll_timer);self.scroll_timer=None
        if float(last)>=.96 and self.next_cursor is not None:self.scroll_timer=self.app.root.after(60,lambda:self.scroll_load('forward'))
        elif float(first)<=.02 and self.window_start>0:self.scroll_timer=self.app.root.after(60,lambda:self.scroll_load('backward'))
    def scroll_load(self,direction):
        self.scroll_timer=None
        if self.loading or not self.catalog.winfo_ismapped():return
        if direction=='forward' and self.next_cursor is not None:self.load(self.next_cursor,direction)
        elif direction=='backward' and self.window_start>0:self.load(self.page_history.get(self.window_start,max(0,self.window_start-40)),direction)
    def click_book(self,event):
        if self.listing.identify_region(event.x,event.y) in ('tree','cell') and self.listing.identify_row(event.y):self.open_selected()
    def selected(self):
        selected=self.listing.selection();return self.rows.get(selected[0]) if selected else None
    def selection_notice(self):
        row=self.selected()
        if row:self.notice.set(row.get('reason') or ' • '.join(v for v in (row.get('description'),', '.join(row.get('subjects',[])),str(row.get('bytes',''))+' original bytes',str(row.get('duplicate_count',0))+' other records with the same bytes') if v))
    def next(self):self.scroll_load('forward')
    def prev(self):self.scroll_load('backward')
    def details(self):
        row=self.selected()
        if row:self.call('resource_detail',{'id':row['id']},self.app.show_result)
    def open_selected(self):
        row=self.selected()
        if not row:return
        self.browse_y=float(self.listing.yview()[0])
        if row.get('content_hit'):
            self.call('resource_reference',{'event_id':row['id'],'start':row['start']},lambda ref:self.open(ref['resource_id'],location=ref))
        else:self.open(row['id'])
    def open(self,key,member='',location=None):
        if location and not member:member=location.get('member','')
        self.epoch+=1;epoch=self.epoch;self.key=key;self.member=member;self.kind=None;self.last_query='';self.find_after=0;self.find_page=1
        self.catalog.pack_forget();self.reader.pack(fill='both',expand=True);self.reader_notice.set('Verifying complete original and opening local reader…')
        def loaded(r):
            if epoch!=self.epoch:return
            self.title.set(r['resource']['title']);self.kind=r['kind'];state=location or r.get('state') or {};self.offset=state.get('offset',0);self.page=state.get('page',1);self.font_size=state.get('font_size',12);self.scroll=state.get('scroll',0);self.pages=r.get('pages',1)
            if not member and not location and state.get('member') and self.kind=='archive':self.open(key,state['member'],location=state);return
            for widget in (self.text,self.canvas_frame,self.member_list,self.member_actions):widget.pack_forget()
            if self.kind=='archive':
                self.members=r['members'];self.member_cursor=r['next_member_cursor'];self.show_members();self.member_list.pack(fill='both',expand=True);self.member_actions.pack(fill='x',pady=5);self.reader_notice.set(str(r['member_total'])+' files • '+r['message']);return
            if self.kind=='unsupported':
                self.text.pack(fill='both',expand=True);self.set_text(r['reason']);self.reader_notice.set('Original retained • unsupported reader • use exact export');return
            self.render(restore_scroll=True)
        self.call('resource_open',{'id':key,'member':member},loaded)
    def set_text(self,text):self.text.configure(state='normal',font=('DejaVu Sans',self.font_size));self.text.delete('1.0','end');self.text.insert('1.0',text.replace('\r\n','\n').replace('\r','\n'));self.text.configure(state='disabled')
    def show_members(self):
        self.member_list.delete(0,'end')
        for m in self.members:self.member_list.insert('end',m['name']+' ['+m['format']+']'+(' — '+m['note'] if m.get('note') else '')+('' if m['readable'] else ' — '+m['reason']))
    def open_member(self):
        chosen=self.member_list.curselection()
        if not chosen:return
        row=self.members[chosen[0]]
        if not row['readable']:self.app.dialog.showinfo('Preserved archive member',row['reason']);return
        self.open(self.key,row['name'],location={'offset':0,'page':1,'font_size':self.font_size})
    def more_members(self):
        if self.member_cursor is None:return
        def loaded(r):self.members=r['items'];self.member_cursor=r['next_cursor'];self.show_members()
        self.call('resource_members',{'id':self.key,'after':self.member_cursor},loaded)
    def render(self,restore_scroll=False):
        if not self.key or self.kind not in {'text','pdf','image'}:return
        epoch=self.epoch;scroll=self.scroll if restore_scroll else 0
        def loaded(r):
            if epoch!=self.epoch:return
            self.next_offset=r.get('next_offset');self.jump.delete(0,'end');self.jump.insert(0,str(self.page if self.kind in {'pdf','image'} else self.offset))
            if self.kind in {'pdf','image'}:
                self.text.pack_forget();self.canvas_frame.pack(fill='both',expand=True);self.image=self.tk.PhotoImage(file=r['image_path']);self.canvas.delete('all');self.canvas.create_image(0,0,image=self.image,anchor='nw');self.canvas.configure(scrollregion=(0,0,self.image.width(),self.image.height()));self.canvas.yview_moveto(scroll);self.reader_notice.set('Original '+('PDF page '+str(self.page)+' / '+str(r['pages']) if self.kind=='pdf' else 'image')+' • zoom '+str(self.width)+' px'+(' • '+self.member if self.member else ''))
            else:
                self.canvas_frame.pack_forget();self.text.pack(fill='both',expand=True);self.set_text(r['text']);self.text.yview_moveto(scroll);self.reader_notice.set('Complete original text • character '+str(self.offset)+' • '+('more text follows' if self.next_offset is not None else 'end of original')+(' • NCBI ASN.1 source; no 3D rendering' if r['format']=='NCBI ASN.1' else '')+(' • '+self.member if self.member else ''))
            self.save_position(scroll=scroll)
        self.call('resource_read',{'id':self.key,'member':self.member,'offset':self.offset,'page':self.page,'width':self.width,'raw':self.raw.get()},loaded)
    def turn(self,delta):
        if self.kind=='archive':return
        if self.kind=='pdf':self.page=min(self.pages,max(1,self.page+delta))
        elif self.kind=='text':
            if delta>0 and self.next_offset is None:return
            self.offset=self.next_offset if delta>0 else max(0,self.offset-16000)
        else:return
        self.render()
    def jump_to(self):
        try:value=int(self.jump.get())
        except ValueError:self.app.dialog.showerror('Reading location','Enter a page number or text character offset.');return
        if self.kind=='pdf':self.page=min(self.pages,max(1,value))
        elif self.kind=='text':self.offset=max(0,value)
        self.render()
    def font(self,delta):self.font_size=min(36,max(8,self.font_size+delta));self.text.configure(font=('DejaVu Sans',self.font_size));self.schedule_save(force=True)
    def zoom(self,delta):self.width=min(1600,max(400,self.width+delta));self.render()
    def save_position(self,scroll=None):
        if not self.key or self.kind not in {'text','pdf','image'}:return
        if scroll is None:scroll=float((self.canvas if self.kind in {'pdf','image'} else self.text).yview()[0])
        self.scroll=scroll;self.call('resource_position',{'id':self.key,'member':self.member,'page':self.page,'offset':self.offset,'font_size':self.font_size,'scroll':scroll})
    def schedule_save(self,force=False):
        if not self.key or self.kind not in {'text','pdf','image'}:return
        current=float((self.canvas if self.kind in {'pdf','image'} else self.text).yview()[0])
        if not force and abs(current-self.scroll)<.00001:return
        if self.save_timer is not None:self.app.root.after_cancel(self.save_timer)
        self.save_timer=self.app.root.after(600,self.saved_scroll)
    def saved_scroll(self):self.save_timer=None;self.save_position()
    def back(self):
        self.save_position();self.epoch+=1;self.reader.pack_forget();self.catalog.pack(fill='both',expand=True);self.restoring=True;self.listing.yview_moveto(self.browse_y);self.app.root.after_idle(lambda:setattr(self,'restoring',False))
    def find(self):
        query=self.find_entry.get()
        if not query or self.kind not in {'text','pdf'}:return
        if query!=self.last_query:self.find_after=0;self.find_page=1;self.last_query=query
        if self.kind=='pdf' and self.find_page>self.pages:self.find_page=1;self.reader_notice.set('End of original. The next search starts at the beginning.');return
        key=self.key;member=self.member;epoch=self.epoch
        def loaded(r):
            if epoch!=self.epoch:return
            if r.get('found'):
                if self.kind=='pdf':self.page=r['page'];self.find_page=self.page+1
                else:self.offset=r['offset'];self.find_after=self.offset+len(query)
                self.render();return
            if r.get('incomplete'):
                self.find_after=r.get('next_offset',0);self.find_page=r.get('next_page',1);self.reader_notice.set('Searching the complete original…');self.app.root.after(20,self.find);return
            self.find_after=0;self.find_page=1;self.reader_notice.set('No further match. The next search starts at the beginning.')
        self.call('resource_find',{'id':key,'member':member,'query':query,'after':self.find_after,'page':min(self.pages,self.find_page)},loaded)
    def sections(self):
        if self.member:self.open(self.key,location={'offset':0,'page':1});return
        if self.kind=='archive':return
        def loaded(r):
            if not r['items']:self.app.dialog.showinfo('Document navigation',r.get('message','No literal chapter headings were identified. Read using page/section controls.'));return
            window=self.tk.Toplevel(self.app.root);window.title('Original sections');listing=self.tk.Listbox(window,width=85,height=22);listing.pack(fill='both',expand=True)
            for p in r['items']:listing.insert('end',p['title'])
            def choose(e=None):
                selected=listing.curselection()
                if selected:
                    item=r['items'][selected[0]]
                    if self.kind=='pdf':
                        if not item.get('page'):self.app.dialog.showinfo('PDF destination',item.get('reason','No verified local page target.'));return
                        self.page=item['page']
                    else:self.offset=item['offset']
                    self.render();window.destroy()
            listing.bind('<Double-1>',choose);self.ttk.Button(window,text='Read selected section',command=choose).pack()
        self.call('resource_outline',{'id':self.key,'member':self.member},loaded)
    def bookmark(self):
        if not self.key or self.kind not in {'text','pdf','image'}:return
        label=self.app.simple.askstring('Bookmark','Bookmark name:',parent=self.app.root)
        if label:self.call('resource_position',{'id':self.key,'member':self.member,'page':self.page,'offset':self.offset,'font_size':self.font_size,'scroll':float((self.canvas if self.kind in {'pdf','image'} else self.text).yview()[0]),'bookmark':label},lambda r:self.reader_notice.set('Bookmark saved. Original unchanged.'))
    def bookmarks(self):
        if not self.key:return
        def loaded(r):
            window=self.tk.Toplevel(self.app.root);window.title('Bookmarks');listing=self.tk.Listbox(window,width=75,height=16);listing.pack(fill='both',expand=True)
            for b in r['items']:listing.insert('end',b['label']+' • '+(b['member'] or 'original')+' • page '+str(b['page'])+' / character '+str(b['offset']))
            def choose():
                selected=listing.curselection()
                if selected:
                    b=r['items'][selected[0]];self.open(self.key,b['member'],location=b);window.destroy()
            self.ttk.Button(window,text='Open bookmark',command=choose).pack()
        self.call('resource_bookmarks',{'id':self.key},loaded)
    def new_collection(self):
        name=self.app.simple.askstring('New collection','Collection name:',parent=self.app.root)
        if name:self.call('resource_collection_create',{'name':name,'approved':True},lambda r:self.search())
    def add_collection(self):
        row=self.selected()
        if not row:return
        def loaded(r):
            if not r['items']:self.app.dialog.showinfo('Collections','Create a collection first.');return
            window=self.tk.Toplevel(self.app.root);window.title('Add to collection');listing=self.tk.Listbox(window,width=60,height=14);listing.pack(fill='both',expand=True)
            for c in r['items']:listing.insert('end',c['name'])
            def save():
                selected=listing.curselection()
                if selected:self.call('resource_membership',{'collection':r['items'][selected[0]]['id'],'id':row['id'],'approved':True},lambda r:self.search());window.destroy()
            self.ttk.Button(window,text='Add selected resource',command=save).pack()
        self.call('resource_collections',{},loaded)
    def remove_collection(self):
        row=self.selected();collection=self.collection_ids.get(self.filters['collection'][0].get())
        if not row or not collection:self.app.dialog.showinfo('Collections','Select a named collection and its resource first.');return
        self.call('resource_membership',{'collection':collection,'id':row['id'],'included':False,'approved':True},lambda r:self.search())
    def export(self):
        row=self.selected() if self.catalog.winfo_ismapped() else None;key=row['id'] if row else self.key
        if not key:return
        path=self.app.files.asksaveasfilename(title='Export exact preserved original to a NEW local file')
        if path:self.call('resource_export',{'id':key,'output':path},self.app.show_result)
    def edit_selected_manual(self):
        row=self.selected()
        if not row:return
        def detail(r):
            if not r.get('manual_id'):self.app.dialog.showinfo('Read-only original','Select a user-authored structured manual. Imported originals are never edited.');return
            self.call('resource_manual_get',{'id':r['manual_id']},self.edit_manual)
        self.call('resource_detail',{'id':row['id']},detail)
    def edit_manual(self,record=None):
        window=self.tk.Toplevel(self.app.root);window.title('New structured manual — originals are preserved');window.geometry('850x650')
        title=self.ttk.Entry(window);title.pack(fill='x',padx=10,pady=8);title.insert(0,record['title'] if record else 'New manual')
        sections=record['sections'] if record else [{'title':'Introduction','body':'','level':1}];current=[0]
        listing=self.tk.Listbox(window,height=6);listing.pack(fill='x',padx=10)
        fields=self.ttk.Frame(window);fields.pack(fill='x',padx=10);name=self.ttk.Entry(fields);name.pack(side='left',fill='x',expand=True);level=self.tk.IntVar(value=1);self.ttk.Spinbox(fields,from_=1,to=6,textvariable=level,width=4,state='readonly').pack(side='left',padx=5)
        from tkinter.scrolledtext import ScrolledText
        body=ScrolledText(window,wrap='word',height=15);body.pack(fill='both',expand=True,padx=10,pady=5)
        def store():sections[current[0]]={'title':name.get(),'body':body.get('1.0','end-1c'),'level':level.get()}
        def labels():
            listing.delete(0,'end')
            for s in sections:listing.insert('end','  '*(s['level']-1)+s['title'])
        def load(index):current[0]=index;name.delete(0,'end');name.insert(0,sections[index]['title']);level.set(sections[index]['level']);body.delete('1.0','end');body.insert('1.0',sections[index]['body']);listing.selection_clear(0,'end');listing.selection_set(index)
        def select(e=None):
            selected=listing.curselection()
            if selected:store();load(selected[0])
        listing.bind('<<ListboxSelect>>',select)
        def add():store();sections.append({'title':'New section','body':'','level':1});labels();load(len(sections)-1)
        def move(delta):
            store();new=max(0,min(len(sections)-1,current[0]+delta));sections[current[0]],sections[new]=sections[new],sections[current[0]];labels();load(new)
        def remove():
            if len(sections)==1:return
            sections.pop(current[0]);labels();load(min(current[0],len(sections)-1))
        def save():
            store();p={'title':title.get(),'sections':sections,'approved':True}
            if record:p.update(manual_id=record['id'],revision=record['revision'])
            if len(json.dumps(p).encode())>60000:self.app.dialog.showerror('Manual size','This editor save exceeds the bounded desktop transfer size. Keep the manual revision below 60 KiB, or preserve a larger complete document through Import file.');return
            if self.app.dialog.askyesno('Save manual','Save the complete manual as a new immutable source revision?'):
                self.call('resource_manual_save',p,lambda r:(window.destroy(),self.search(),self.open(r['resource_id'])))
        actions=self.ttk.Frame(window);actions.pack(fill='x',padx=10,pady=8)
        for label,cmd in [('Add section',add),('Move up',lambda:move(-1)),('Move down',lambda:move(1)),('Remove section',remove),('Save complete manual',save),('Cancel',window.destroy)]:self.ttk.Button(actions,text=label,command=cmd).pack(side='left',padx=3)
        labels();load(0)
    def close(self):
        if self.timer is not None:self.app.root.after_cancel(self.timer);self.timer=None
        if self.save_timer is not None:self.app.root.after_cancel(self.save_timer);self.save_timer=None
