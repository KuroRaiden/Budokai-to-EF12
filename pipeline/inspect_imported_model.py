"""Safe model import and rig compatibility check; never execute embedded Blender scripts."""
import bpy,os,json,pathlib,mathutils
src=pathlib.Path(os.environ['STUDIO_IMPORT_SOURCE']);out=pathlib.Path(os.environ['STUDIO_MODEL_DIR']);base=pathlib.Path(os.environ['DBZ_WORKSPACE']);out.mkdir(parents=True,exist_ok=True)
if src.suffix.lower()=='.blend':bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
else:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if src.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(src))
 elif src.suffix.lower() in ('.glb','.gltf'):bpy.ops.import_scene.gltf(filepath=str(src))
 elif src.suffix.lower()=='.obj':bpy.ops.wm.obj_import(filepath=str(src))
 else:raise ValueError('Supported model formats: .blend, .fbx, .glb, .gltf, .obj')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.visible_get() and not o.hide_render]
if not meshes:raise ValueError('No visible mesh found in this model.')
armatures=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
arm=max(armatures,key=lambda o:len(o.data.bones),default=None)
reference=json.loads((base/'work/ef12/rig_inspection.json').read_text())['source']['armatures'][0]['bones']
canonical={b['name'].casefold():b['name'] for b in reference}
if arm:
 for bone in arm.data.bones:
  short=bone.name.split(':')[-1];new=canonical.get(short.casefold())
  if new and new!=bone.name and arm.data.bones.get(new) is None:
   old=bone.name;bone.name=new
   for obj in meshes:
    vg=obj.vertex_groups.get(old)
    if vg and obj.vertex_groups.get(new) is None:vg.name=new
required=set('waist stmc chest neck head lchn larm1 larm2 lhandrot lhand rchn rarm1 rarm2 rhandrot rhand lleg1 lleg2 lfoot1 lfoot2 rleg1 rleg2 rfoot1 rfoot2'.split())
missing=sorted(required-set(b.name for b in arm.data.bones)) if arm else sorted(required)
compatible=not missing
# Store an immediate static mesh preview even when no usable rig is supplied.
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];floor=min(p.z for p in points);height=max(p.z for p in points)-floor;scale=20/max(height,.0001)
records=[];materials={};warnings=[]
for obj in meshes:
 mesh=obj.data;mesh.calc_loop_triangles();verts=[];faces=[];uv=[];indices=[]
 if not mesh.materials:
  mat=bpy.data.materials.new('ImportedMaterial');mat.diffuse_color=(.65,.7,.8,1);mesh.materials.append(mat)
 for slot in obj.material_slots:
  mat=slot.material
  if not mat:
   mat=bpy.data.materials.new('ImportedMaterial');slot.material=mat
  if mat.name in materials:continue
  image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat.node_tree else None
  texture=None
  if image:
   texture='preview_'+str(len(materials))+'.png'
   try:image.save_render(str(out/texture),scene=bpy.context.scene)
   except Exception:warning='Missing texture for '+mat.name;warnings.append(warning);texture=None
  materials[mat.name]=dict(texture=texture,color=list(mat.diffuse_color))
 for tri in mesh.loop_triangles:
  start=len(verts);faces.append([start,start+1,start+2]);indices.append(tri.material_index)
  for vi,li in zip(tri.vertices,tri.loops):
   v=obj.matrix_world@mesh.vertices[vi].co;verts.append([v.x*scale,v.y*scale,(v.z-floor)*scale]);uv.append(list(mesh.uv_layers.active.data[li].uv) if mesh.uv_layers.active else [0,0])
 records.append(dict(name=obj.name,vertices=verts,faces=faces,uv=uv,weights=[{} for v in verts],materials=[s.material.name for s in obj.material_slots],material_indices=indices))
(out/'static_geometry.json').write_text(json.dumps(dict(meshes=records,materials=materials),separators=(',',':')))
for image in bpy.data.images:
 if image.source=='FILE':
  try:image.pack()
  except Exception:pass
if arm:
 for obj in list(bpy.context.scene.objects):obj.select_set(False)
 arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(out/'imported_source.blend'))
(out/'inspection.json').write_text(json.dumps(dict(compatible=compatible,missing_bones=missing,mesh_parts=len(meshes),warnings=warnings),indent=2))
print('MODEL_INSPECTED',compatible,len(meshes),'meshes',flush=True)
