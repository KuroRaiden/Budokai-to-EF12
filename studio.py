"""Local, offline character/move editor. Run with Python 3.10+."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import argparse,csv,hashlib,io,json,os,re,secrets,shutil,socket,subprocess,threading,time,traceback,webbrowser,mimetypes
from library import Library
from models import Models
from mesh_preview import MeshPreviews
from action_labels import decorate, input_summary
from combos import clean_combos, compile_combos, motion_entries, entry_commands

HERE=Path(__file__).resolve().parent
if not (HERE/'config.json').is_file():
 raise SystemExit('Run python configure.py first. See README.md for local asset and toolchain requirements.')
CFG=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
LIB=Library(CFG['assets'])
MODELS=Models(HERE,CFG)
MESH_PREVIEWS=MeshPreviews(HERE,CFG,LIB,MODELS)
TOKEN=secrets.token_urlsafe(24)
JOBS={};LOCK=threading.Lock()
ROWS={};ACTIONS=[]
for p in sorted((Path(CFG['template'])/'mth').glob('*.csv')):
 if p.name!=CFG['template_header']:continue
 rows=list(csv.reader(p.open(encoding='cp932',newline='')));ROWS[p.name]=rows
 for i,r in enumerate(rows):
  if len(r)>23 and r[0]=='MTH':
   ident=hashlib.sha256((p.name+'|'+r[1]).encode()).hexdigest()[:16]
   label=r[1].split('_',2)
   # Keep the original identifier for round-trip compatibility; display ASCII where available.
   label=re.sub(r'[^\x20-\x7e]','',r[1]).rstrip('_') or r[2]
   ACTIONS.append(dict(id=ident,label=label,motion=r[2],category=r[5],header=p.name,row=i))
decorate(ACTIONS, ROWS[CFG['template_header']])
ACTIONMAP={a['id']:a for a in ACTIONS}
for a in ACTIONS:
 direct=entry_commands(ROWS[CFG['template_header']],a)
 a['combo_entry']=a['category']=='STRIKE' and bool(direct)
 a['entry_input']=' / '.join(dict.fromkeys(input_summary(r[4]) for r in direct))

def clean_recipe(d):
 name=str(d.get('name','')).strip()
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _-]{0,47}',name):raise ValueError('Use a name of 1–48 letters, digits, spaces, underscores or hyphens.')
 assignments=d.get('assignments',{})
 model=d.get('model','Goku');MODELS.get(model)
 if not isinstance(assignments,dict):raise ValueError('Invalid move assignments.')
 result={}
 for action,entry in assignments.items():
  if action not in ACTIONMAP:raise ValueError('Unknown target action')
  if not isinstance(entry,dict) or entry.get('clip') not in LIB.byid:raise ValueError('Unknown source move')
  damage=int(entry.get('damage',12));hit=int(entry.get('hit',-1))
  if not 0<=damage<=999 or not -1<=hit<LIB.byid[entry['clip']]['frames']:raise ValueError('Damage or hit frame is out of range')
  result[action]=dict(clip=entry['clip'],damage=damage,hit=hit)
 combos=clean_combos(d.get('combos',[]),ACTIONMAP,LIB.byid,ROWS[CFG['template_header']],result)
 if not result and not combos:raise ValueError('Assign a move or create a combo string first.')
 return dict(version=5,name=name,model=model,style='3D',template=CFG.get('template_family','VF-Montauk'),assignments=result,combos=combos,combo_buttons=dict(L='A',H='B',E='Y'),controls=dict(L='Light',H='Heavy',G='Guard',E='Ki blast',RB='Ki charge'),notes=str(d.get('notes',''))[:4000])

def run_stage(args,cwd,env,log,timeout):
 with log.open('ab') as f:r=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 tail=log.read_text(errors='replace')[-6000:]
 if r.returncode or 'Traceback (most recent call last)' in tail:raise RuntimeError(f'Conversion failed. See {log}\n{tail[-1200:]}')

def build(job,recipe):
 try:
  root=Path(CFG['exports']);root.mkdir(parents=True,exist_ok=True)
  slug=re.sub(r'[^A-Za-z0-9_-]+','_',recipe['name'])
  folder=root/(slug+'_'+time.strftime('%Y%m%d_%H%M%S')+'_'+job['id'][:5]);folder.mkdir()
  work=folder/'conversion';work.mkdir();pack=folder/('DBZ-'+slug)
  (folder/'recipe.json').write_text(json.dumps(recipe,indent=2))
  base=Path(CFG['workspace']);python=CFG['python']
  modern=base/'work/blender/blender-4.0.2-windows-x64/blender.exe'
  legacy=next((base/'work/ef12/blender_legacy').rglob('blender.exe'))
  converter=base/'work/ef12/converter_new/ConvXSI2FMOT.exe'
  for required in (modern,legacy,converter,base/'outputs/Goku_Corrected_Review.blend'):
   if not required.is_file():raise RuntimeError(f'Missing configured converter dependency: {required}')
  grouped={};compiled={};unique={}
  for entry in motion_entries(recipe):
   clip=entry['clip']
   if clip not in unique:unique[clip]='DBZ_Shin_'+hashlib.sha256(clip.encode()).hexdigest()[:12]
  for clip,name in unique.items():
   p,index=LIB.source(clip);grouped.setdefault(p,[]).append((index,name))
  for k,(p,selection) in enumerate(grouped.items(),1):
   dest=work/f'bank_{k}';dest.mkdir();selectionfile=dest/'selection.json';selectionfile.write_text(json.dumps(selection))
   env=dict(os.environ,DBZ_WORKSPACE=str(base),SHIN_SOURCE_AMM=str(p),SHIN_SOURCE_MODEL=str(LIB.model_for(p)),SHIN_SELECTION=str(selectionfile),SHIN_OUT_DIR=str(dest),**MODELS.env(recipe['model']))
   job.update(stage=f'Retargeting source bank {k}/{len(grouped)}',progress=10+int(25*(k-1)/len(grouped)))
   log=dest/'conversion.log'
   run_stage([str(modern),'--background','--python',str(base/'work/ef12/retarget_shin_goku.py')],base,env,log,900)
   job.update(stage=f'Exporting EF-12 animation bank {k}/{len(grouped)}',progress=40+int(25*(k-1)/len(grouped)))
   run_stage([str(legacy),'--background','--factory-startup','--python',str(base/'work/ef12/export_shin_legacy.py')],base,env,log,1800)
   for index,name in selection:
    xsi=dest/(name+'.xsi')
    if not xsi.is_file():raise RuntimeError(f'Exporter did not produce {xsi.name}; inspect {log}')
    run_stage([str(converter),str(xsi),str(base/'work/ef12/converter_new/ConvMotion.csv')],dest,env,log,120)
    motion=dest/(name+'.fmot')
    if not motion.is_file() or motion.read_bytes()[:4]!=b'FMOT':raise RuntimeError(f'No valid native motion generated for {name}')
    compiled[name]=motion
  job.update(stage='Building character pack and action headers',progress=85)
  shutil.copytree(CFG['template'],pack,ignore=shutil.ignore_patterns('source','*.xls','*.blend1'))
  if recipe['model']!='Goku':
   modeldir=Path(MODELS.env(recipe['model'])['STUDIO_MODEL_DIR']);native=pack/'mdl/Studio_Model';native.mkdir(parents=True,exist_ok=True)
   shutil.copy2(modeldir/'Goku_EF12.fmdl',native/'Character.fmdl')
   for file in modeldir.iterdir():
    if file.suffix.lower() in ('.tga','.dds'):shutil.copy2(file,native/file.name)
   from PIL import Image,ImageDraw,ImageFont
   image=Image.open(modeldir/'thumbnail.png').convert('RGBA')
   for suffix,size in [('s',128),('m',256),('l',512)]:image.resize((size,size),Image.Resampling.LANCZOS).save(pack/f'portrait_{suffix}.dds',pixel_format='DXT5')
   plate=Image.new('RGBA',(256,64),(0,0,0,0));draw=ImageDraw.Draw(plate);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',24);draw.text((5,16),recipe['name'],font=font,fill='white');plate.save(pack/'nameplate.dds',pixel_format='DXT5')
  (pack/'mot/Unique').mkdir(parents=True,exist_ok=True)
  for name,file in compiled.items():shutil.copy2(file,pack/'mot/Unique'/file.name)
  rows={name:[r[:] for r in data] for name,data in ROWS.items()};report=[]
  for action_id,entry in recipe['assignments'].items():
   a=ACTIONMAP[action_id];r=rows[a['header']][a['row']];source=LIB.byid[entry['clip']];name=unique[entry['clip']];nf=source['frames']
   old=r[2];r[2]=name;r[3]='Unique';r[21]='3'
   if r[5]=='STRIKE':
    hit=entry['hit'] if entry['hit']>=0 else max(1,min(nf-3,round(nf*.35)))
    r[12]=f'[{hit}:{hit}:{min(nf-1,hit+2)}={entry["damage"]}=0.05=0]'
    r[7]=str(max(1,nf-8));r[8]='6';r[4]='STAND[1]';r[6]='-'
    for col in (29,30,31,33,35,37,38):
     if len(r)>col:r[col]='-'
   elif r[5]=='MOVE' and ('Idle' in a['label'] or 'Loop' in a['label']):r[9]='1'
   report.append(dict(action=a['label'],previous=old,source=source,native=name))
  combo_report=compile_combos(rows[CFG['template_header']],recipe.get('combos',[]),ACTIONMAP,LIB.byid,unique)
  (pack/'combo_report.json').write_text(json.dumps(combo_report,indent=2))
  for name,data in rows.items():
   with (pack/'mth'/name).open('w',encoding='cp932',newline='',errors='replace') as f:csv.writer(f,lineterminator='\r\n').writerows(data)
  ini=pack/'character.ini';s=ini.read_text(encoding='cp932');s=re.sub(r'(?m)^Name\s*=.*$',f'Name = "{recipe["name"]}"',s);s=re.sub(r'(?m)^Display\s*=.*$',f'Display = "{recipe["name"]}"',s);s=re.sub(r'(?m)^Style\d+\s*=.*(?:\n|$)','',s);s+=f'\nStyle0 = "VF 3D",{CFG["template_header"]},AI,{CFG["template_guard"]}\n';ini.write_text(s,encoding='cp932')
  if recipe['model']!='Goku':
   s=re.sub(r'(?m)^Costume\d+\s*=.*(?:\n|$)','',s);s+='\nCostume0 = "Default",\\Studio_Model\\Character.fmdl,G6Lite_HF.fskl,collision.csv,blendmot.lst,1.0\n';ini.write_text(s,encoding='cp932')
  (pack/'builder_recipe.json').write_text(json.dumps(recipe,indent=2));(pack/'builder_report.json').write_text(json.dumps(report,indent=2))
  (pack/'BUILDER_README.txt').write_text('Generated by Budokai-to-EF12.\n\nBase: VF-Montauk Speed template, single 3D style with button guard.\nSelected action entries use converted original Shin Budokai clips.\nCombo strings generate new actions and parent-linked commands; see combo_report.json.\nThe inherited follow-ups of each selected combo entry are replaced in this pack.\nAI scripts remain inherited and are not taught the new combo routes.\nUnassigned actions, sounds, effects, collisions and command logic inherit VF-Montauk.\nThis is an untested character pack; verify each action in EF-12.\nThe L/H/G/E + separate RB layout is saved in the design recipe; this version does not remap the controller or implement Ki charging.\nSpecial-move visual effects are not imported by selecting an animation.\n\nInstall manually by copying this character folder into EF-12/data/Cha and adding a new consecutive Character entry to data/select.ini.\nThe application does not alter your installed game.\n',encoding='utf-8')
  job.update(status='complete',stage='Pack exported. In-game validation required.',progress=100,output=str(pack),report=report)
 except Exception as ex:job.update(status='failed',stage=str(ex),error=traceback.format_exc(),progress=0)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,value,status=200,ctype='application/json; charset=utf-8'):
  raw=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  try:
   if u.path=='/':return self.send((HERE/'index.html').read_bytes().replace(b'__TOKEN__',TOKEN.encode()),ctype='text/html; charset=utf-8')
   if u.path=='/api/library':return self.send(dict(moves=LIB.entries,skipped=LIB.skipped,actions=ACTIONS,assets=CFG['assets'],exports=CFG['exports'],template=CFG['template_family'],models=MODELS.list()))
   if u.path=='/api/models':return self.send(MODELS.list())
   if u.path=='/api/model-library':return self.send(MODELS.library(q.get('q',[''])[0]))
   if u.path=='/api/mesh-preview':return self.send(MESH_PREVIEWS.request(q.get('id',[''])[0],q.get('model',['Goku'])[0]))
   if u.path=='/api/mesh-motion':return self.send(MESH_PREVIEWS.motion(q.get('id',[''])[0],q.get('model',['Goku'])[0]))
   if u.path.startswith('/assets/'):
    root=(HERE/'assets').resolve();p=(root/u.path.removeprefix('/assets/')).resolve()
    if not p.is_relative_to(root) or not p.is_file() or p.suffix not in ('.js','.png','.json'):raise ValueError('Unknown preview asset')
    return self.send(p.read_bytes(),ctype=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
   if u.path.startswith('/model-assets/'):
    parts=u.path.split('/',3)
    if len(parts)!=4:raise ValueError('Unknown model asset')
    p=MODELS.asset(parts[2],parts[3]);return self.send(p.read_bytes(),ctype=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
   if u.path=='/api/preview':return self.send(LIB.preview(q.get('id',[''])[0]))
   if u.path=='/api/jobs':return self.send(list(JOBS.values()))
   if u.path=='/api/health':return self.send(dict(app='ShinCharacterStudio',version=1))
   if u.path=='/api/preset':return self.send(json.loads((HERE/'Recipes/Goku_Shin_Starter.json').read_text()))
   return self.send(dict(error='Not found'),404)
  except Exception as ex:return self.send(dict(error=str(ex)),400)
 def do_POST(self):
  try:
   if self.headers.get('X-Studio-Token')!=TOKEN:return self.send(dict(error='Invalid request token'),403)
   length=int(self.headers.get('Content-Length','0'))
   if self.path.startswith('/api/models/upload?'):
    if not 0<length<=250*1024*1024:raise ValueError('Choose a model file up to 250 MB.')
    name=Path(parse_qs(urlparse(self.path).query).get('name',['model.blend'])[0]).name
    if Path(name).suffix.lower() not in ('.blend','.fbx','.glb','.obj'):raise ValueError('Upload .blend, .fbx, .glb or .obj files. Use a file path for multi-file glTF assets.')
    folder=HERE/'Models/Sources'/secrets.token_hex(8);folder.mkdir(parents=True);p=folder/name
    with p.open('wb') as f:
     remaining=length
     while remaining:
      chunk=self.rfile.read(min(1024*1024,remaining))
      if not chunk:raise ValueError('Incomplete model upload')
      f.write(chunk);remaining-=len(chunk)
    return self.send(MODELS.import_model(p),202)
   if not 0<length<200000:raise ValueError('Invalid request size')
   d=json.loads(self.rfile.read(length))
   if self.path=='/api/models/import':return self.send(MODELS.import_model(str(d.get('path','')),d.get('name')),202)
   if self.path=='/api/shutdown':
    if any(j['status']=='running' for j in JOBS.values()):raise ValueError('Wait for the current conversion to finish before stopping the server.')
    self.send(dict(status='stopping'));threading.Thread(target=self.server.shutdown,daemon=True).start();return
   recipe=clean_recipe(d)
   if self.path=='/api/validate':return self.send(recipe)
   if self.path=='/api/save':
    dest=HERE/'Recipes';dest.mkdir(exist_ok=True);p=dest/(re.sub(r'[^A-Za-z0-9_-]','_',recipe['name'])+'_'+time.strftime('%Y%m%d_%H%M%S')+'.json');p.write_text(json.dumps(recipe,indent=2));return self.send(dict(path=str(p)))
   if self.path=='/api/build':
    if MODELS.get(recipe['model'])['state']!='ready':raise ValueError('Map this mesh to a supported humanoid rig before exporting a character.')
    with LOCK:
     if any(j['status']=='running' for j in JOBS.values()):raise ValueError('A conversion is already running. Wait for it to finish.')
     ident=secrets.token_hex(6);job=dict(id=ident,status='running',stage='Preparing conversion',progress=1);JOBS[ident]=job
    threading.Thread(target=build,args=(job,recipe),daemon=True).start();return self.send(job,202)
   return self.send(dict(error='Not found'),404)
  except Exception as ex:return self.send(dict(error=str(ex)),400)

class StudioServer(ThreadingHTTPServer):
 allow_reuse_address=False
 def server_bind(self):
  if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
  super().server_bind()

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--no-browser',action='store_true');args=ap.parse_args()
 url=f'http://127.0.0.1:{int(CFG["port"])}'
 try:server=StudioServer(('127.0.0.1',int(CFG['port'])),Handler)
 except OSError:
  import urllib.request
  try:health=json.load(urllib.request.urlopen(url+'/api/health',timeout=2))
  except Exception:raise RuntimeError(f'Port {CFG["port"]} is occupied. Close the other program or change port in config.json.')
  if health.get('app')!='ShinCharacterStudio':raise RuntimeError('The configured port belongs to another program.')
  if not args.no_browser:webbrowser.open(url)
  print('Studio is already running: '+url);raise SystemExit(0)
 print(f'Budokai-to-EF12\n{url}\n{len(LIB.entries)} selectable clips. Keep this window open. Ctrl+C to close.',flush=True)
 if not args.no_browser:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
