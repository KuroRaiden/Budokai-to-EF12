from pathlib import Path
import json
from PIL import Image

def write_assets(folder,out):
 folder=Path(folder);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 d=json.loads((folder/'Goku_geometry.json').read_text())
 names=sorted({n for mesh in d['meshes'] for w in mesh['weights'] for n in w});lookup={n:i for i,n in enumerate(names)};meshes=[]
 for record in d['meshes']:
  for mi,material in enumerate(record['materials']):
   positions=[];uv=[];joints=[];weights=[]
   for face,index in zip(record['faces'],record['material_indices']):
    if mi!=index:continue
    for vi in face:
     positions.extend(record['vertices'][vi]);uv.extend(record['uv'][vi]);pairs=sorted(record['weights'][vi].items(),key=lambda p:p[1],reverse=True)[:4]
     joints.extend([lookup[n] for n,w in pairs]+[0]*(4-len(pairs)));weights.extend([w for n,w in pairs]+[0]*(4-len(pairs)))
   if not positions:continue
   info=d['materials'][material];texture=info.get('texture');png=Path(texture).with_suffix('.png').name if texture else None
   if texture:Image.open(folder/texture).convert('RGBA').save(out/png)
   meshes.append(dict(name=record['name'],material=material,positions=positions,uv=uv,joints=joints,weights=weights,texture=png,color=info.get('color',[.8,.8,.8,1])))
 (out/'mesh.json').write_text(json.dumps(dict(bones=names,meshes=meshes,coordinate_system='Z_UP'),separators=(',',':')))
 return dict(parts=len(meshes),triangles=sum(len(m['positions'])//9 for m in meshes),bones=len(names))
