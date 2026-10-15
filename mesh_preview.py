"""Cached skinned preview using exactly the same retargeter as native exports."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,threading

class MeshPreviews:
 def __init__(self,here,cfg,library,models):
  self.here=Path(here);self.cfg=cfg;self.library=library;self.models=models;self.pool=ThreadPoolExecutor(max_workers=1);self.jobs={};self.lock=threading.Lock()
  scripts=Path(cfg['workspace'])/'work/ef12';signature=b'mesh-v3'
  for name in ('retarget_shin_goku.py','retarget_quality.py'):
   p=scripts/name
   if p.is_file():signature+=p.read_bytes()
  self.version=hashlib.sha256(signature).hexdigest()[:16]
 def request(self,clip,model='Goku'):
  self.library.source(clip)
  info=self.models.get(model)
  if info['state']!='ready':return dict(status='failed',stage='This mesh needs bone mapping before it can play animations.')
  identity=model+'|'+clip
  with self.lock:
   if identity in self.jobs:return dict(self.jobs[identity])
   key=hashlib.sha256((self.version+'|'+identity).encode()).hexdigest()[:20]
   out=self.here/'PreviewCache'/key
   file=out/'mesh_motion.json'
   if file.is_file():return dict(status='complete',url='/api/mesh-motion?id='+clip+'&model='+model)
   if sum(j['status'] in ('queued','running') for j in self.jobs.values())>=4:return dict(status='busy',stage='Finishing other previews; retrying shortly.')
   job=dict(status='queued',stage='Preparing selected move on the character mesh…');self.jobs[identity]=job
   self.pool.submit(self.generate,clip,model,out,job)
   return dict(job)
 def motion(self,clip,model='Goku'):
  self.library.source(clip);self.models.get(model);key=hashlib.sha256((self.version+'|'+model+'|'+clip).encode()).hexdigest()[:20]
  p=self.here/'PreviewCache'/key/'mesh_motion.json'
  if not p.is_file():raise ValueError('Mesh preview is not ready yet')
  return p.read_bytes()
 def generate(self,clip,model_id,out,job):
  try:
   job.update(status='running');out.mkdir(parents=True,exist_ok=True)
   source,index=self.library.source(clip);model=self.library.model_for(source)
   selection=out/'selection.json';selection.write_text(json.dumps([(index,'Studio_Mesh_Preview')]))
   base=Path(self.cfg['workspace']);env=dict(os.environ,DBZ_WORKSPACE=str(base),SHIN_SOURCE_AMM=str(source),SHIN_SOURCE_MODEL=str(model),SHIN_SELECTION=str(selection),SHIN_OUT_DIR=str(out),SHIN_PREVIEW_ONLY='1',SHIN_PREVIEW_JSON=str(out/'mesh_motion.json'),**self.models.env(model_id))
   log=out/'preview.log'
   with log.open('wb') as f:
    result=subprocess.run([str(base/'work/blender/blender-4.0.2-windows-x64/blender.exe'),'--background','--python',str(base/'work/ef12/retarget_shin_goku.py')],cwd=base,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
   if result.returncode or not (out/'mesh_motion.json').is_file():raise RuntimeError('This move could not be retargeted onto the selected character. Source skeleton preview remains available. Details: '+str(log))
   d=json.loads((out/'mesh_motion.json').read_text());assert d['frames'] and d['bones']
   job.update(status='complete',stage='Character mesh · retargeted move',url='/api/mesh-motion?id='+clip+'&model='+model_id)
  except Exception as ex:job.update(status='failed',stage=str(ex))
