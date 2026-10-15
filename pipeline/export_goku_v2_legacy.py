import bpy,sys,os,json
base=os.environ.get('DBZ_WORKSPACE',os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
pilot=os.environ.get('STUDIO_MODEL_DIR',os.path.join(base,'work','ef12','pilot_v2'))
data=json.load(open(os.path.join(pilot,'Goku_geometry.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.join(base,'work','ef12','G6Lite_Rig','G6Lite_Rig','G6Lite_Rig.blend'))
arm=bpy.data.objects['G6Lite_Rig']
for bone in arm.data.bones:bone.use_deform=True
for pb in arm.pose.bones:
 pb.custom_shape=None
 for constraint in list(pb.constraints):pb.constraints.remove(constraint)
if arm.animation_data:arm.animation_data_clear()
for obj in list(bpy.context.scene.objects):
 if obj!=arm:bpy.context.scene.objects.unlink(obj)
sys.path.insert(0,os.path.join(base,'work','ef12','model_exporter','ef12_model_export'))
import ef12_model_export
ef12_model_export.register()
materials={}
for name,info in data['materials'].items():
 mat=bpy.data.materials.new(name);mat.diffuse_color=(1.,1.,1.);mat.diffuse_intensity=1.;mat.emit=0.;mat.specular_color=(0.,0.,0.);mat.specular_intensity=0.;mat.ef12.material_type='TOON';mat.ef12.emissive=(0.,0.,0.);mat.ef12.use_specular=False;mat.use_shadeless=False
 if info['texture']:
  img=bpy.data.images.load(os.path.join(pilot,info['texture']));tex=bpy.data.textures.new(name+'_diffuse',type='IMAGE');tex.image=img;slot=mat.texture_slots.add();slot.texture=tex;slot.texture_coords='UV';slot.use_map_color_diffuse=True
 for index,filename in enumerate(('toon_ramp.tga','toon_diffuse_sphere.tga','toon_black.tga','toon_black.tga'),1):
  if index==1:filename=info['texture']
  img=bpy.data.images.load(os.path.join(pilot,filename));tex=bpy.data.textures.new(name+'_toon_'+str(index),type='IMAGE');tex.image=img;slot=mat.texture_slots.add();slot.texture=tex;slot.texture_coords='UV'
 materials[name]=mat
for record in data['meshes']:
 mesh=bpy.data.meshes.new(record['name']);mesh.from_pydata(record['vertices'],[],record['faces']);mesh.update()
 obj=bpy.data.objects.new(record['name'],mesh);bpy.context.scene.objects.link(obj);obj.parent=arm
 for name in record['materials']:mesh.materials.append(materials[name])
 mesh.uv_textures.new(name='UVMap');uv=mesh.uv_layers.active
 for i,coords in enumerate(record['uv']):uv.data[i].uv=coords
 for poly,mi in zip(mesh.polygons,record['material_indices']):poly.material_index=mi;poly.use_smooth=True
 vg={b.name:obj.vertex_groups.new(name=b.name) for b in arm.data.bones}
 for i,weights in enumerate(record['weights']):
  for bone,value in weights.items():vg[bone].add([i],value,'REPLACE')
 modifier=obj.modifiers.new('EF12_G6Lite','ARMATURE');modifier.object=arm
 obj['source_file']=record['source'] or ''
 for poly in mesh.polygons:
  union=set(g.group for v in poly.vertices for g in mesh.vertices[v].groups if g.weight>1e-6)
  assert len(union)<=4
bpy.context.scene.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pilot,'Goku_EF12_G6Lite.blend'))
ef12_model_export.write_model_data(bpy.context,os.path.join(pilot,'Goku_EF12.dae'),True,False,False)
bpy.ops.wm.collada_export(filepath=os.path.join(pilot,'Goku_standard.dae'),selected=False,include_uv_textures=True,include_material_textures=True)
print('LEGACY_EXPORT_COMPLETE')
