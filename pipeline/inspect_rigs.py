import bpy,pathlib,json,os
base=pathlib.Path(os.environ.get('DBZ_WORKSPACE',str(pathlib.Path(__file__).resolve().parents[2])))
paths={'target':base/'work/ef12/blenderSample/blenderSample/Skeleton/G6Lite_SKL_BL.blend','target_rig':base/'work/ef12/G6Lite_Rig/G6Lite_Rig/G6Lite_Rig.blend','source':pathlib.Path(str(base/'local/source_character.blend'))}
result={}
for key,path in paths.items():
 bpy.ops.wm.open_mainfile(filepath=str(path))
 result[key]=dict(objects=[dict(name=o.name,type=o.type,matrix=[list(r) for r in o.matrix_world]) for o in bpy.context.scene.objects],armatures=[])
 for obj in bpy.context.scene.objects:
  if obj.type!='ARMATURE':continue
  result[key]['armatures'].append(dict(name=obj.name,bones=[dict(name=b.name,parent=b.parent.name if b.parent else None,head=list(b.head_local),tail=list(b.tail_local),matrix=[list(r) for r in b.matrix_local],deform=b.use_deform) for b in obj.data.bones]))
(base/'work/ef12/rig_inspection.json').write_text(json.dumps(result,indent=2))
for key,value in result.items():
 print(key,[(a['name'],len(a['bones'])) for a in value['armatures']])
 print([(b['name'],b['head']) for a in value['armatures'] for b in a['bones']])
