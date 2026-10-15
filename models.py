from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,threading,shutil,time
from mesh_assets import write_assets
from PIL import Image

class Models:
 def __init__(self,here,cfg):
  self.here=Path(here);self.cfg=cfg;self.root=self.here/'Models';self.root.mkdir(exist_ok=True);self.pool=ThreadPoolExecutor(max_workers=1);self.lock=threading.Lock();self.entries={}
  self.default=dict(id='Goku',name='Goku',state='ready',rigged=True,mesh_url='/assets/goku_mesh.json',stage='Ready · VF 3D rig')
  for p in self.root.glob('*/model.json'):
   try:
    d=json.loads(p.read_text());self.entries[d['id']]=d
    if d['state']=='importing':d.update(state='failed',stage='Import was interrupted. Import the file again to retry.')
   except Exception:pass
  self.catalog=None
 def list(self):return [self.default]+[dict(d) for d in self.entries.values()]
 def get(self,ident):
  if ident=='Goku':return self.default
  if ident not in self.entries:raise ValueError('Unknown character model')
  return dict(self.entries[ident])
 def env(self,ident):
  d=self.get(ident)
  return {} if ident=='Goku' else dict(STUDIO_MODEL_DIR=str(self.root/ident/'native'))
 def library(self,q):
  if self.catalog is None:
   root=Path(self.cfg['assets']).parent/'World_Mission_Converted/Battle/character/model'
   self.catalog=[dict(name=p.stem,path=str(p)) for p in sorted(root.rglob('*.blend'))] if root.exists() else []
  q=q.casefold();rows=[d for d in self.catalog if q in d['name'].casefold()]
  return dict(total=len(rows),models=rows[:40])
 def asset(self,ident,name):
  self.get(ident);root=(self.root/ident/'assets').resolve();p=(root/name).resolve()
  if not p.is_relative_to(root) or p.suffix.lower() not in ('.json','.png') or not p.is_file():raise ValueError('Unknown model preview asset')
  return p
 def import_model(self,path,name=None):
  p=Path(path).expanduser().resolve()
  if p.suffix.lower() not in ('.blend','.fbx','.glb','.gltf','.obj') or not p.is_file():raise ValueError('Choose an existing .blend, .fbx, .glb, .gltf or .obj model.')
  if p.stat().st_size>250*1024*1024:raise ValueError('Model files up to 250 MB are supported.')
  ident='model_'+hashlib.sha256((str(p)+'|'+str(p.stat().st_mtime_ns)).encode()).hexdigest()[:14]
  with self.lock:
   if ident in self.entries and self.entries[ident]['state'] in ('ready','needs_mapping','importing'):return self.get(ident)
   if sum(d['state']=='importing' for d in self.entries.values())>=3:raise ValueError('Finish the queued model imports before adding another.')
   d=dict(id=ident,name=(name or p.stem).strip()[:100],source=str(p),state='importing',rigged=False,stage='Import queued',mesh_url=None);self.entries[ident]=d
   self.save(d);self.pool.submit(self.prepare,d,p)
   return dict(d)
 def save(self,d):
  p=self.root/d['id'];p.mkdir(parents=True,exist_ok=True);tmp=p/'model.tmp';tmp.write_text(json.dumps(d,indent=2));tmp.replace(p/'model.json')
 def stage(self,d,text):d['stage']=text;self.save(d)
 def prepare(self,d,source):
  try:
   base=Path(self.cfg['workspace']);folder=self.root/d['id']/'native';folder.mkdir(parents=True,exist_ok=True)
   env=dict(os.environ,DBZ_WORKSPACE=str(base),STUDIO_IMPORT_SOURCE=str(source),STUDIO_MODEL_DIR=str(folder),STUDIO_MODEL_SOURCE=str(folder/'imported_source.blend'))
   modern=base/'work/blender/blender-4.0.2-windows-x64/blender.exe';legacy=next((base/'work/ef12/blender_legacy').rglob('blender.exe'));log=folder/'import.log'
   def run(args,timeout=600):
    with log.open('ab') as f:r=subprocess.run([str(a) for a in args],cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    tail=log.read_text(errors='replace')[-5000:]
    if r.returncode or 'Traceback (most recent call last)' in tail:raise RuntimeError('Model preparation failed. Details: '+str(log)+'\n'+tail[-700:])
   self.stage(d,'Reading mesh, textures and skeleton…')
   run([modern,'--background','--factory-startup','--disable-autoexec','--python',base/'work/ef12/inspect_imported_model.py'])
   inspection=json.loads((folder/'inspection.json').read_text());d['warnings']=inspection['warnings']
   if not inspection['compatible']:
    shutil.copy2(folder/'static_geometry.json',folder/'Goku_geometry.json');d.update(write_assets(folder,self.root/d['id']/'assets'))
    d.update(state='needs_mapping',rigged=False,mesh_url=f'/model-assets/{d["id"]}/mesh.json',stage='Mesh imported. Bone mapping is required before animations or EF-12 export.',missing_bones=inspection['missing_bones']);self.save(d);return
   self.stage(d,'Mapping skin weights to the EF-12 rig…')
   run([modern,'--background','--factory-startup','--disable-autoexec','--python',base/'work/ef12/prepare_goku_v2.py'])
   for n in ('toon_ramp.tga','toon_diffuse_sphere.tga','toon_black.tga'):shutil.copy2(base/'work/ef12/pilot_v2'/n,folder/n)
   self.stage(d,'Converting the character mesh for EF-12…')
   run([legacy,'--background','--factory-startup','--disable-autoexec','--python',base/'work/ef12/export_goku_v2_legacy.py'])
   run([self.cfg['python'],base/'work/ef12/restore_goku_normals.py'])
   run([base/'work/ef12/converter_new/ConvDAE2FMDL.exe',folder/'Goku_EF12.dae',base/'work/ef12/converter_new/ConvModel.csv'])
   if not (folder/'Goku_EF12.fmdl').is_file():raise RuntimeError('The native model converter did not produce a model.')
   self.stage(d,'Preparing textured preview and portrait…')
   run([modern,'--background','--factory-startup','--disable-autoexec','--python',base/'work/ef12/build_goku_review.py'])
   if not (folder/'model_review.blend').is_file():raise RuntimeError('The skinned preview could not be prepared.')
   for p in folder.glob('*.tga'):Image.open(p).convert('RGBA').save(p.with_suffix('.dds'),pixel_format='DXT5')
   d.update(write_assets(folder,self.root/d['id']/'assets'))
   d.update(state='ready',rigged=True,mesh_url=f'/model-assets/{d["id"]}/mesh.json',stage='Ready · mapped to VF 3D rig')
   self.save(d)
  except Exception as ex:d.update(state='failed',stage=str(ex));self.save(d)
