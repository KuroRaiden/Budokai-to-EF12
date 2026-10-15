import bpy,pathlib,json,math,collections,sys,io,os
from mathutils import Vector
base=pathlib.Path(os.environ.get('DBZ_WORKSPACE',str(pathlib.Path(__file__).resolve().parents[2])))
sys.path.insert(0,str(base/'work/blender_pillow'))
from PIL import Image
out=pathlib.Path(os.environ.get('STUDIO_MODEL_DIR',str(base/'work/ef12/pilot_v2')));out.mkdir(parents=True,exist_ok=True)
src=pathlib.Path(os.environ.get('STUDIO_MODEL_SOURCE',str(base/'local/source_character.blend')))
bpy.ops.wm.open_mainfile(filepath=str(src))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.visible_get() and not o.hide_render]
target=json.loads((base/'work/ef12/rig_inspection.json').read_text())['target']['armatures'][0]['bones']
target_names={b['name'] for b in target}
mapping={'waist':'Waist','stmc':'Chest_R','chest':'Breast','neck':'Neck','head':'Face','lchn':'ShoulderR_R','rchn':'ShoulderL_R','larmrot':'ArmR_R','larm1':'ArmR_R','larm2':'ArmR_J','lhandrot':'WristR','lhand':'HandR_R','rarmrot':'ArmL_R','rarm1':'ArmL_R','rarm2':'ArmL_J','rhandrot':'WristL','rhand':'HandL_R','llegrot':'LegR_R','lleg1':'LegR_R','lleg2':'LegR_J','lfoot1':'FootR_R','lfoot2':'ToeR_R','rlegrot':'LegL_R','rleg1':'LegL_R','rleg2':'LegL_J','rfoot1':'FootL_R','rfoot2':'ToeL_R'}
for src_side,dst_side in [('L','R'),('R','L')]:
 for finger,target_finger in [('Thumb','Thumb'),('Index','Fore'),('Middle','Middle'),('Ring','Ring'),('Pinky','Pinky')]:
  for segment in (1,2,3):
   suffix=str(segment-1) if finger=='Thumb' else ('_R' if segment==1 else str(segment-1))
   mapping[src_side+finger+str(segment)]=target_finger+dst_side+suffix
mapping['f_jaw']='JawL_R';mapping['f_dteeth']='JawL_R'

def mapbone(name,fallback):
 seen=set()
 while name and name not in seen:
  seen.add(name)
  if name in mapping:return mapping[name]
  bone=arm.data.bones.get(name);name=bone.parent.name if bone and bone.parent else None
 return fallback
def interp(x,points):
 for (a,b),(c,d) in zip(points,points[1:]):
  if x<=c:return b+(x-a)*(d-b)/(c-a)
 a,b=points[-2];c,d=points[-1];return d+(x-c)*(d-b)/(c-a)
source_head=lambda name:(arm.matrix_world@arm.data.bones[name].head_local)
zpoints=[(source_head('rfoot2').z,0.2),(source_head('rfoot1').z,1.),(source_head('rleg2').z,6.),(source_head('rleg1').z,10.),(source_head('rarm1').z,14.7),(source_head('neck').z,15.4),(source_head('head').z,16.4)]
xpoints=[(0.,0.),(abs(source_head('rarm1').x),2.1),(abs(source_head('rarm2').x),4.5),(abs(source_head('rhand').x),7.2),(abs(source_head('rhand').x)+.2,9.2)]
floor_z=min((o.matrix_world@v.co).z for o in visible for v in o.data.vertices)
height=max((o.matrix_world@v.co).z for o in visible for v in o.data.vertices)-floor_z
scale=20./height if os.environ.get('STUDIO_MODEL_DIR') else 10.
def fit(v):return [v.x*scale,v.y*scale,(v.z-floor_z)*scale]
records=[];weight_changes=0;materials={}
for obj in visible:
 mesh=obj.data;mesh.calc_normals_split();mesh.calc_loop_triangles();verts=[];faces=[];uv=[];weights=[];normals=[];mat_indices=[]
 fallback='Face' if any(s in obj.name.lower() for s in ('face','teeth','mouth','eye','hair')) else 'Waist'
 if 'L_hand' in obj.name:fallback='HandR_R'
 if 'R_hand' in obj.name:fallback='HandL_R'
 group_names={g.index:g.name for g in obj.vertex_groups}
 for tri in mesh.loop_triangles:
  ws=[];scores=collections.Counter()
  for vi in tri.vertices:
   w=collections.Counter()
   for group in mesh.vertices[vi].groups:
    if group.weight>1e-6:w[mapbone(group_names[group.group],fallback)]+=group.weight
   if not w:w[fallback]=1.
   ws.append(w);scores.update(w)
  palette=set(k for k,v in scores.most_common(4))
  if len(scores)>4:weight_changes+=1
  start=len(verts);faces.append([start,start+1,start+2]);mat_indices.append(tri.material_index)
  for vi,li,w in zip(tri.vertices,tri.loops,ws):
   selected={k:v for k,v in w.items() if k in palette}
   if not selected:selected={scores.most_common(1)[0][0]:1.}
   total=sum(selected.values());weights.append({k:v/total for k,v in selected.items()})
   verts.append(fit(obj.matrix_world@mesh.vertices[vi].co))
   normals.append(list((obj.matrix_world.to_3x3().inverted().transposed()@mesh.loops[li].normal).normalized()))
   uv.append(list(mesh.uv_layers.active.data[li].uv) if mesh.uv_layers.active else [0,0])
 for slot in obj.material_slots:
  mat=slot.material
  if not mat or mat.name in materials:continue
  image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat.node_tree else None
  texture=None
  if image and image.packed_file:
   texture='tex_'+str(len(materials)).zfill(3)+'.tga';Image.open(io.BytesIO(bytes(image.packed_file.data))).convert('RGB').save(out/texture)
  if not texture and image and pathlib.Path(bpy.path.abspath(image.filepath)).is_file():
   texture='tex_'+str(len(materials)).zfill(3)+'.tga';Image.open(bpy.path.abspath(image.filepath)).convert('RGB').save(out/texture)
  if not texture:
   texture='tex_'+str(len(materials)).zfill(3)+'.tga';Image.new('RGB',(4,4),tuple(round(max(0,min(1,c))*255) for c in mat.diffuse_color[:3])).save(out/texture)
  materials[mat.name]=dict(texture=texture,color=list(mat.diffuse_color))
 records.append(dict(name=obj.name,source=obj.get('source_file'),vertices=verts,faces=faces,uv=uv,normals=normals,weights=weights,materials=[s.material.name for s in obj.material_slots if s.material],material_indices=mat_indices))
payload=dict(name='DBZ_Goku',meshes=records,materials=materials,mapping=mapping,weight_changes=weight_changes,target_rig=str(base/'work/ef12/blenderSample/blenderSample/Skeleton/G6Lite_SKL_BL.blend'))
(out/'Goku_geometry.json').write_text(json.dumps(payload,separators=(',',':')))
(out/'source_bind.json').write_text(json.dumps(dict(heads={b.name:fit(arm.matrix_world@b.head_local) for b in arm.data.bones},parents={b.name:b.parent.name if b.parent else None for b in arm.data.bones}),separators=(',',':')))
print('UNIFORM_SCALE',scale,'FLOOR_OFFSET',-floor_z*scale)
print('PREPARED',len(records),'meshes',sum(len(m['faces']) for m in records),'triangles','weight palette changes',weight_changes)
