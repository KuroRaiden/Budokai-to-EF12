import bpy,sys,struct,math,json,os
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector,Euler
base=Path(os.environ.get('DBZ_WORKSPACE',str(Path(__file__).resolve().parents[2])))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_skeleton import skeleton
assets=Path(os.environ.get('SHIN_ASSETS',str(base/'local/Shin_Budokai_Another_Road_Assets')))
model=Path(os.environ['SHIN_SOURCE_MODEL']) if 'SHIN_SOURCE_MODEL' in os.environ else next(assets.glob('models/data_btl_cmn/Goku__0093*/*.amo'))
amm=Path(os.environ['SHIN_SOURCE_AMM']) if 'SHIN_SOURCE_AMM' in os.environ else next(assets.glob('animations/data_btl_cmn/Goku__0092*/Goku__0005.amm'))
sk=skeleton(model.read_bytes());b=amm.read_bytes()
na,t,nb,no=struct.unpack_from('<4I',b,16)
def key(n):
 s=n.split('_',1)[-1]
 return s.replace('L00_','').lower()
names=[key(b[no+i*32:no+(i+1)*32].split(b'\0')[0].decode()) for i in range(nb)]
mapping={'Waist':'waist','Chest_R':'stmc','Breast':'chest','Neck':'neck','Face':'head','ShoulderR_R':'lchn','ArmR_R':'larm1','ArmR_J':'larm2','WristR':'lhandrot','HandR_R':'lhand','ShoulderL_R':'rchn','ArmL_R':'rarm1','ArmL_J':'rarm2','WristL':'rhandrot','HandL_R':'rhand','LegR_R':'lleg1','LegR_J':'lleg2','FootR_R':'lfoot1','ToeR_R':'lfoot2','LegL_R':'rleg1','LegL_J':'rleg2','FootL_R':'rfoot1','ToeL_R':'rfoot2'}
C=Matrix(((1,0,0,0),(0,0,1,0),(0,1,0,0),(0,0,0,1)))
def globals_for(tracks,frame):
 result={}
 def get(i):
  if i in result:return result[i]
  nm,q,p,par=sk[i];q=Quaternion((q[3],q[0],q[1],q[2]));p=Vector(p)
  for cls,frames,values in tracks.get(key(nm),[]):
   v=values[0]
   for k in range(len(frames)-1):
    if frames[k]<=frame<=frames[k+1]:
     a=(frame-frames[k])/max(1,frames[k+1]-frames[k]);v=[values[k][j]*(1-a)+values[k+1][j]*a for j in range(3)];break
    if frame>frames[-1]:v=values[-1]
   if cls==0:q=Euler(v,'XYZ').to_quaternion()
   elif cls==1:p+=Vector(v)
  m=Matrix.LocRotScale(p,q,Vector((1,1,1)))
  if par>=0 and par!=i:m=get(par)@m
  result[i]=m;return m
 for i in range(len(sk)):get(i)
 return {key(sk[i][0]):C@m@C.inverted() for i,m in result.items()}
rest=globals_for({},0)
inspection=json.loads((base/'work/ef12/rig_inspection.json').read_text())['source']
src_arm=inspection['armatures'][0]
src_obj=next(o for o in inspection['objects'] if o['name']==src_arm['name'])
src_world=Matrix(src_obj['matrix'])
source_bones={b['name']:b for b in src_arm['bones']}
def model_name(role):return role
model_heads={role:(src_world@Vector(source_bones[model_name(role)]['head']))*10 for role in set(mapping.values())}
floor_shift=9.474419951
for v in model_heads.values():v.z+=floor_shift
role_parents={}
for role in model_heads:
 par=source_bones[model_name(role)]['parent']
 while par and par not in model_heads:par=source_bones[par]['parent']
 role_parents[role]=par
if os.environ.get('STUDIO_MODEL_DIR'):
 model_dir=Path(os.environ['STUDIO_MODEL_DIR']);bind=json.loads((model_dir/'source_bind.json').read_text())
 model_heads={role:Vector(bind['heads'][role]) for role in set(mapping.values())}
 role_parents={}
 for role in model_heads:
  par=bind['parents'][role]
  while par and par not in model_heads:par=bind['parents'][par]
  role_parents[role]=par
bpy.ops.wm.open_mainfile(filepath=str(Path(os.environ['STUDIO_MODEL_DIR'])/'model_review.blend' if os.environ.get('STUDIO_MODEL_DIR') else base/'outputs/Goku_Corrected_Review.blend'))
arm=bpy.data.objects['G6Lite_Rig'];arm.animation_data_create()
for bone in arm.data.bones:bone.use_deform=True
for pb in arm.pose.bones:
 for con in list(pb.constraints):pb.constraints.remove(con)
payload={}
# BSK action code 0 explicitly selects pool 3 / animation 0: original fighting idle.
selection=json.loads(Path(os.environ['SHIN_SELECTION']).read_text()) if 'SHIN_SELECTION' in os.environ else [(0,'Goku_Shin_Idle'),(17,'Goku_Shin_Light1'),(25,'Goku_Shin_Light2'),(29,'Goku_Shin_Heavy1'),(20,'Goku_Shin_Heavy2'),(44,'Goku_Shin_LightHeavy')]
for index,name in selection:
 nf,opt,tab=struct.unpack_from('<HHI',b,t+8*index);tracks={}
 for j,nm in enumerate(names):
  cnt,ptr=struct.unpack_from('<II',b,tab+8*j);tr=[]
  for r in range(cnt):
   cls,nk,typ,fp,vp=struct.unpack_from('<IHHII',b,ptr+16*r)
   if not nk or cls>2:continue
   frames=list(b[fp:fp+nk]);fmt='<3h' if cls==0 else '<3f';stride=6 if cls==0 else 12
   vals=[list(struct.unpack_from(fmt,b,vp+stride*k)) for k in range(nk)]
   if cls==0:
    vals=[[v*math.tau/65536 for v in row] for row in vals]
    for k in range(1,len(vals)):
     for axis in range(3):vals[k][axis]=vals[k-1][axis]+(vals[k][axis]-vals[k-1][axis]+math.pi)%math.tau-math.pi
   tr.append((cls,frames,vals))
  tracks[nm]=tr
 action=bpy.data.actions.new(name);action.use_fake_user=True;arm.animation_data.action=action;baked=[]
 parent_first=sorted(arm.pose.bones,key=lambda pb:len(pb.parent_recursive))
 first=globals_for(tracks,0)
 # Keep the idle rooted; game translation units are ~1/10 of target Blender units.
 for f in range(nf):
  posed=globals_for(tracks,f);bpy.context.scene.frame_set(f)
  deltas={role:posed[role].to_quaternion()@rest[role].to_quaternion().inverted() for role in model_heads}
  heads={}
  def head_for(role):
   if role in heads:return heads[role]
   par=role_parents[role]
   if par:head=head_for(par)+deltas[par]@(model_heads[role]-model_heads[par])
   else:head=model_heads[role]+(posed[role].translation-first[role].translation)*1.3
   heads[role]=head;return head
  for role in model_heads:head_for(role)
  lift=min(heads['lfoot2'].z,heads['rfoot2'].z)-min(model_heads['lfoot2'].z,model_heads['rfoot2'].z)
  for h in heads.values():h.z-=lift
  for pb in parent_first:
   pb.rotation_mode='XYZ';pb.location=(0,0,0);pb.scale=(1,1,1)
   src=mapping.get(pb.name)
   if src and src in posed and src in rest:
    delta=deltas[src]
    deform=Matrix.LocRotScale(heads[src]-delta@model_heads[src],delta,Vector((1,1,1)))
    pb.matrix=deform@pb.bone.matrix_local
   else:pb.rotation_euler=(0,0,0)
   bpy.context.view_layer.update()
   if src:
    pb.keyframe_insert('rotation_euler',frame=f);pb.keyframe_insert('location',frame=f)
  baked.append(dict(frame=f,bones={pb.name:dict(rotation=list(pb.rotation_euler),location=list(pb.location)) for pb in arm.pose.bones if pb.name in mapping}))
 payload[name]=baked
out=Path(os.environ.get('SHIN_OUT_DIR',str(base/'work/ef12/shin_motion')));out.mkdir(parents=True,exist_ok=True)
(out/'retargeted_motion.json').write_text(json.dumps(payload,separators=(',',':')))
bpy.context.scene.frame_set(0);bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=nf-1
arm.animation_data.action=bpy.data.actions[selection[0][1]];bpy.context.scene.frame_end=len(payload[selection[0][1]])-1
print('TARGET_RIG_STATE',arm.data.pose_position,[(n,arm.data.bones[n].use_inherit_rotation,list(arm.pose.bones[n].rotation_euler),list(arm.pose.bones[n].head)) for n in ('Waist','ArmL_R','ArmL_J','LegL_R','LegL_J')],flush=True)
if os.environ.get('SHIN_PREVIEW_JSON'):
 geometry=json.loads((Path(os.environ.get('STUDIO_MODEL_DIR',str(base/'work/ef12/pilot_v2')))/'Goku_geometry.json').read_text())
 names=sorted({n for mesh in geometry['meshes'] for w in mesh['weights'] for n in w})
 arm.animation_data.action=bpy.data.actions[selection[0][1]]
 samples=[]
 for frame in range(len(payload[selection[0][1]])):
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  row=[]
  for name in names:
   pb=arm.pose.bones[name];matrix=arm.matrix_world@pb.matrix@pb.bone.matrix_local.inverted()@arm.matrix_world.inverted()
   row.append([round(matrix[r][c],6) for c in range(4) for r in range(4)])
  samples.append(row)
 Path(os.environ['SHIN_PREVIEW_JSON']).write_text(json.dumps(dict(bones=names,frames=samples,fps=60,retargeted=True),separators=(',',':')))
if os.environ.get('SHIN_PREVIEW_ONLY')!='1':bpy.ops.wm.save_as_mainfile(filepath=str(out/'Goku_Shin_Idle_Review.blend'))
print('SHIN_IDLE_RETARGETED',nf,'frames',flush=True)
