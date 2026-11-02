"""Local native presentation tokens and a small, disposable Canvas identity.

No assets, network, model calls or persistence. Animation describes UI activity,
never model availability or an asserted reasoning result.
"""
import math
import tkinter as tk
from tkinter import ttk

COLORS={'background':'#070d16','surface':'#0d1826','raised':'#142438','border':'#244052',
        'cyan':'#42dfe8','ice':'#c4f4ff','text':'#e4edf5','muted':'#91a9ba','selection':'#193d52'}
SPACE={'small':6,'medium':12,'large':24}
FONT={'body':('DejaVu Sans',11),'small':('DejaVu Sans',9),'title':('DejaVu Sans',18),'mono':('DejaVu Sans Mono',10)}


def apply(root):
    c=COLORS;root.configure(background=c['background'])
    for kind in ('Text','Listbox','Canvas'):
        for key,value in [('background',c['background']),('foreground',c['text']),('highlightBackground',c['border']),('highlightColor',c['cyan']),('selectBackground',c['selection']),('selectForeground',c['ice']),('insertBackground',c['cyan']),('font',FONT['body'])]:
            root.option_add('*'+kind+'.'+key,value)
    root.option_add('*Toplevel.background',c['background'])
    style=ttk.Style(root);style.theme_use('clam')
    style.configure('.',background=c['background'],foreground=c['text'],font=FONT['body'],bordercolor=c['border'],troughcolor=c['surface'],focuscolor=c['cyan'])
    style.configure('TFrame',background=c['background'])
    style.configure('TLabel',background=c['background'],foreground=c['text'])
    style.configure('Muted.TLabel',foreground=c['muted'],font=FONT['small'])
    style.configure('Brand.TLabel',foreground=c['ice'],font=FONT['title'])
    style.configure('TButton',background=c['surface'],foreground=c['text'],padding=(10,7),borderwidth=1,relief='flat')
    style.map('TButton',background=[('active',c['selection']),('pressed',c['border'])],foreground=[('disabled',c['muted']),('active',c['ice'])],bordercolor=[('focus',c['cyan'])])
    style.configure('Accent.TButton',foreground=c['cyan'],background=c['raised'])
    style.configure('Selected.TButton',foreground=c['ice'],background=c['selection'])
    style.configure('TEntry',fieldbackground=c['surface'],foreground=c['text'],insertcolor=c['cyan'],padding=6)
    style.configure('TCombobox',fieldbackground=c['surface'],foreground=c['text'],arrowcolor=c['cyan'],padding=5)
    style.map('TCombobox',fieldbackground=[('readonly',c['surface'])],foreground=[('readonly',c['text'])])
    style.configure('Treeview',background=c['surface'],fieldbackground=c['surface'],foreground=c['text'],rowheight=30)
    style.configure('Treeview.Heading',background=c['raised'],foreground=c['ice'],padding=6)
    style.map('Treeview',background=[('selected',c['selection'])])
    style.configure('TCheckbutton',background=c['background'],foreground=c['text'])
    style.map('TCheckbutton',background=[('active',c['surface'])])
    return style


class Core(tk.Canvas):
    """Bounded vector primitives. One idle frame/s; four during actual local work."""
    def __init__(self,parent):
        super().__init__(parent,height=224,background=COLORS['background'],highlightthickness=0)
        self.motion=True;self.visible=True;self.busy=False;self.compact=False;self.phase=0;self.timer=None;self.frames=0
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Destroy>',lambda e:self.stop() if e.widget is self else None)
        self.arcs=[]
        for ring in range(3):
            for i in range(8):self.arcs.append((self.create_arc(0,0,1,1,style='arc',width=1 if ring!=1 else 2,outline=COLORS['cyan'] if ring==1 else COLORS['border']),ring,i))
        self.nodes=[self.create_oval(0,0,1,1,fill=COLORS['cyan'],outline='') for _ in range(4)]
        self.mark=self.create_line(0,0,1,1,fill=COLORS['ice'],width=2)
        self.word=self.create_text(0,0,text='V E C T O R',fill=COLORS['ice'],font=FONT['title'])
        self.caption=self.create_text(0,0,text='LOCAL KNOWLEDGE  /  EVIDENCE  /  INQUIRY',fill=COLORS['muted'],font=FONT['small'])
        self.circuits=[self.create_line(0,0,1,1,fill=COLORS['border']) for _ in range(2)]
        self.draw();self.schedule()
    def draw(self):
        self.frames+=1;w=max(300,self.winfo_width());h=72 if self.compact else 224;x=w/2;y=34 if self.compact else max(94,self.winfo_height()/2-35);r=26 if self.compact else 72
        self.configure(height=h)
        for item,ring,i in self.arcs:
            a=r-ring*(5 if self.compact else 8);self.coords(item,x-a,y-a,x+a,y+a);self.itemconfigure(item,start=i*45+self.phase*(1 if ring%2 else -1),extent=30 if ring==1 else 37)
        for i,item in enumerate(self.nodes):
            angle=math.radians(45+i*90);px=x+math.cos(angle)*r;py=y+math.sin(angle)*r;self.coords(item,px-2,py-2,px+2,py+2)
        self.coords(self.mark,x-r*.29,y-r*.25,x,y+r*.27,x+r*.29,y-r*.25)
        self.coords(self.word,x,y+r+27);self.coords(self.caption,x,y+r+51)
        for item in (self.word,self.caption):self.itemconfigure(item,state='hidden' if self.compact else 'normal')
        for side,item in enumerate(self.circuits):
            direction=-1 if side==0 else 1;self.coords(item,x+direction*(r+12),y,x+direction*(r+48),y,x+direction*(r+65),y-17,x+direction*(w/2-24),y-17)
    def schedule(self):
        self.stop()
        if self.motion and self.visible:self.timer=self.after(250 if self.busy else 1000,self.tick)
    def tick(self):
        self.timer=None
        if self.winfo_toplevel().state()!='iconic':self.phase=(self.phase+(7 if self.busy else 2))%360;self.draw()
        self.schedule()
    def stop(self):
        if self.timer is not None:self.after_cancel(self.timer);self.timer=None
    def state(self,*,visible=None,busy=None,compact=None,motion=None):
        for key,value in [('visible',visible),('busy',busy),('compact',compact),('motion',motion)]:
            if value is not None:setattr(self,key,value)
        self.draw();self.schedule()


class CommandInput(tk.Text):
    """Multiline entry with the old Desktop entry adapter kept for callers/tests."""
    def get(self,*args):return super().get(*(args or ('1.0','end-1c')))
    def insert(self,index,chars,*tags):return super().insert('1.0' if index==0 else index,chars,*tags)
    def delete(self,first,last=None):return super().delete('1.0' if first==0 else first,last)


class Workspace(ttk.Frame):
    """Existing detailed controls remain reachable at smaller laptop widths."""
    def __init__(self,parent):
        super().__init__(parent);self.canvas=tk.Canvas(self,highlightthickness=0);self.canvas.grid(row=0,column=0,sticky='nsew')
        self.rowconfigure(0,weight=1);self.columnconfigure(0,weight=1)
        v=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview);v.grid(row=0,column=1,sticky='ns')
        h=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview);h.grid(row=1,column=0,sticky='ew')
        self.canvas.configure(yscrollcommand=v.set,xscrollcommand=h.set)
        self.content=ttk.Frame(self.canvas,padding=16);self.item=self.canvas.create_window(0,0,window=self.content,anchor='nw')
        self.content.bind('<Configure>',self.layout);self.canvas.bind('<Configure>',self.layout)
    def layout(self,event=None):
        w=max(self.canvas.winfo_width(),self.content.winfo_reqwidth());h=max(self.canvas.winfo_height(),self.content.winfo_reqheight())
        self.canvas.itemconfigure(self.item,width=w,height=h);self.canvas.configure(scrollregion=(0,0,w,h))
