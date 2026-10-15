"""Read-only Shin Budokai AMM/AMO library, using documented native layouts."""
import struct, math, hashlib, bisect
from pathlib import Path
from shared_labels import shared_label

def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def role(n):return n.split('_',1)[-1].replace('L00_','').lower()
def qmul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def qrot(q,v):return qmul(qmul(q,(*v,0)),(-q[0],-q[1],-q[2],q[3]))[:3]
def euler(v):
 q=(0,0,0,1)
 for ax in (2,1,0):
  a=[0.,0.,0.];a[ax]=math.sin(v[ax]/2);q=qmul(q,(*a,math.cos(v[ax]/2)))
 return q

class Library:
 def __init__(self,root):
  self.root=Path(root);self.files={};self.entries=[];self.cache={};self.skels={};self.models=list(self.root.glob('models/data_btl_cmn/**/*.amo'));self.skipped=[]
  for p in sorted(self.root.glob('animations/**/*.amm')):
   try:
    b=p.read_bytes();n,t,nb,no=struct.unpack_from('<4I',b,16)
    if b[:4]!=b'#AMM' or not 0<n<2000 or not 0<nb<300 or no+nb*32>len(b):raise ValueError('Unsupported animation header')
    ptrs=[struct.unpack_from('<HHI',b,t+8*i)[2] for i in range(n)]
    if min(x for x in ptrs if x)!=t+8*n:raise ValueError('Alternate track layout')
    fid=hashlib.sha256(str(p.relative_to(self.root)).encode()).hexdigest()[:16];self.files[fid]=p
    char=p.name.split('__')[0] if '__' in p.name else 'Shared'
    labels=self.labels(p)
    for i,ptr in enumerate(ptrs):
     nf,opt,_=struct.unpack_from('<HHI',b,t+8*i)
     if ptr and nf>1:
      entry=dict(id=f'{fid}:{i}',character=char,archive=p.parent.name,file=p.name,index=i,frames=nf,label=labels.get(i,f'Clip {i:03}'),named=i in labels)
      description=shared_label(p,i) if char=='Shared' else None
      if description:entry.update(description)
      self.entries.append(entry)
   except (ValueError,struct.error,StopIteration) as ex:self.skipped.append(dict(file=str(p.relative_to(self.root)),reason=str(ex)))
  self.byid={e['id']:e for e in self.entries}
 def labels(self,p):
  support=self.root/'support'/p.parent.parent.name/p.parent.name
  skeleton=self.root/'skeletons'/p.parent.parent.name/p.parent.name
  cm=list(support.glob('*.bcm'));bs=list(skeleton.glob('*.bsk'))
  if not cm or not bs:return {}
  # Only the primary character animation pool is resolved here.
  siblings=sorted(p.parent.glob('*.amm'))
  if siblings and p!=siblings[0]:return {}
  try:
   c=cm[0].read_bytes();b=bs[0].read_bytes();n=struct.unpack_from('<H',c,0x1e)[0];count,tab=struct.unpack_from('<II',b,16);out={};seen=set()
   def walk(o,path):
    if o in seen or not 0x50<=o<=len(c)-64:return
    seen.add(o);w=struct.unpack_from('<16H',c,o)
    direction={0:'',1:'Forward + ',2:'Back + ',16:'Up + ',32:'Down + '}.get(w[0],'Direction + ')
    btn={1:'L',2:'H',4:'G',5:'L+G',6:'H+G',8:'E',15:'L+H+G+E'}.get(w[1],f'Button {w[1]}')
    seq=path+[direction+btn];code=w[12]
    if code<count:
     off=u32(b,tab+code*4)
     if off:
      anim,pool=struct.unpack_from('<HH',b,off)
      if pool==3:
       label=' → '.join(seq)
       if w[4]:label+=' (special condition)'
       if w[6]&0x40:label='Air: '+label
       if anim not in out or len(label)<len(out[anim]):out[anim]=label
    for j in range(min(w[7],64)):walk(u32(c,o+64+4*j),seq)
   for k in range(n):walk(u32(c,0x50+4*k),[])
   if count:
    p0=u32(b,tab)
    if p0:
     idle,pool=struct.unpack_from('<HH',b,p0)
     if pool==3:out[idle]='Fighting idle'
   return out
  except (ValueError,struct.error,IndexError):return {}
 def source(self,clipid):
  if clipid not in self.byid:raise ValueError('Unknown library move')
  e=self.byid[clipid];return self.files[clipid.split(':')[0]],e['index']
 def model_for(self,p):
  char=p.name.split('__')[0] if '__' in p.name else 'Goku';archive=p.parent.name.upper();stem=archive.split('_')[-1].split('.')[0]
  candidates=[m for m in self.models if m.name.startswith(char+'__') and 'B00' in m.parent.name.upper()]
  exact=[m for m in candidates if (stem+'B00') in m.parent.name.upper()]
  if exact:return exact[0]
  if candidates:return candidates[0]
  raise ValueError('No associated source skeleton found for this archive')
 def skeleton(self,p):
  m=self.model_for(p)
  if str(m) in self.skels:return self.skels[str(m)]
  b=m.read_bytes();g=b.find(b'#AMG')
  if g<0:raise ValueError('No native skeleton')
  n=u32(b,g+16);axes=g+u32(b,g+20);names=g+u32(b,g+28);out=[]
  for i in range(n):
   o=axes+i*80;v=struct.unpack_from('<7f',b,o);par=u32(b,o+64)
   nm=b[names+32*i:names+32*(i+1)].split(b'\0')[0].decode('latin1')
   parent=(g+par-axes)//80 if par else -1
   if parent==i:parent=-1
   out.append((nm,v[:4],v[4:],parent))
  self.skels[str(m)]=out;return out
 def preview(self,clipid):
  if clipid in self.cache:return self.cache[clipid]
  p,index=self.source(clipid);b=p.read_bytes();n,t,nb,no=struct.unpack_from('<4I',b,16);nf,opt,tab=struct.unpack_from('<HHI',b,t+index*8);tracks={}
  for j in range(nb):
   nm=role(b[no+j*32:no+(j+1)*32].split(b'\0')[0].decode('latin1'));cnt,ptr=struct.unpack_from('<II',b,tab+8*j);tr=[]
   if cnt>8:raise ValueError('Unsupported track layout')
   for k in range(cnt):
    cls,nk,typ,fp,vp=struct.unpack_from('<IHHII',b,ptr+k*16)
    if not nk or cls>2:continue
    fr=list(b[fp:fp+nk]);size=6 if cls==0 else 12;fmt='<3h' if cls==0 else '<3f'
    vals=[list(struct.unpack_from(fmt,b,vp+size*i)) for i in range(nk)]
    if cls==0:
     vals=[[v*math.tau/65536 for v in row] for row in vals]
     for i in range(1,len(vals)):
      for a in range(3):vals[i][a]=vals[i-1][a]+(vals[i][a]-vals[i-1][a]+math.pi)%math.tau-math.pi
    tr.append((cls,fr,vals))
   tracks[nm]=tr
  sk=self.skeleton(p);frames=[]
  for f in range(nf):
   G={};active=set()
   def get(i):
    if i in G:return G[i]
    if i in active:raise ValueError('Cyclic skeleton')
    active.add(i);nm,q,pos,par=sk[i];pos=list(pos)
    for cls,fr,vals in tracks.get(role(nm),[]):
     k=max(0,bisect.bisect_right(fr,f)-1);v=vals[k]
     if k+1<len(fr):
      a=(f-fr[k])/max(1,fr[k+1]-fr[k]);v=[v[j]*(1-a)+vals[k+1][j]*a for j in range(3)]
     if cls==0:q=euler(v)
     elif cls==1:pos=[pos[j]+v[j] for j in range(3)]
    if par>=0:
     pq,pp=get(par);pos=[a+b for a,b in zip(pp,qrot(pq,pos))];q=qmul(pq,q)
    active.remove(i);G[i]=(q,pos);return G[i]
   frames.append([list(get(i)[1]) for i in range(len(sk))])
  result=dict(names=[x[0] for x in sk],parents=[x[3] for x in sk],frames=frames,fps=60)
  if len(self.cache)>30:self.cache.clear()
  self.cache[clipid]=result;return result
