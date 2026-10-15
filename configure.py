"""Configure an existing local EF-12 conversion workspace; never download game assets."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from pack_validation import validate_template

HERE=Path(__file__).resolve().parent

def configure(args):
    if args.from_config:
        config=json.loads(Path(args.from_config).read_text(encoding='utf-8'))
    else:
        config=json.loads((HERE/'config.example.json').read_text(encoding='utf-8'))
        for key in ('assets','template','workspace'):
            supplied=getattr(args,key)
            config[key]=supplied or input(f'Local {key} folder: ').strip().strip('"')
        config['exports']=str(HERE/'Characters')
    config['python']=sys.executable
    if args.port:config['port']=args.port
    for key in ('assets','template','workspace','exports'):
        config[key]=str(Path(config[key]).expanduser().resolve())
    for key in ('assets','template','workspace'):
        if not Path(config[key]).is_dir():raise ValueError(f'Missing {key} directory: {config[key]}')
    workspace=Path(config['workspace'])
    header=Path(config['template'])/'mth'/config['template_header']
    if not header.is_file():raise ValueError('The prepared VF template needs mth/'+config['template_header'])
    validate_template(config['template'])
    if args.install_pipeline:
        dest=workspace/'work/ef12';dest.mkdir(parents=True,exist_ok=True)
        backup=dest/'before_budokai_to_ef12';backup.mkdir(exist_ok=True)
        for p in (HERE/'pipeline').glob('*.py'):
            target=dest/p.name
            if target.exists() and not (backup/p.name).exists():shutil.copy2(target,backup/p.name)
            shutil.copy2(p,target)
    if not (workspace/'work/ef12/rig_inspection.json').is_file():
        raise ValueError('Missing local rig_inspection.json. See docs/SETUP.md; binary/reference game data is not included.')
    geometry=workspace/'work/ef12/pilot_v2/Goku_geometry.json'
    if geometry.is_file():
        from mesh_assets import write_assets
        write_assets(geometry.parent,HERE/'assets')
        (HERE/'assets/mesh.json').replace(HERE/'assets/goku_mesh.json')
    else:raise ValueError('Missing prepared starter geometry. See docs/SETUP.md.')
    (HERE/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('Local configuration and mesh preview created. They are ignored by Git.')
    print('Run: python studio.py')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-config',help='Import an existing local Studio config without publishing it')
    for name in ('assets','template','workspace'):parser.add_argument('--'+name)
    parser.add_argument('--port',type=int,choices=range(1024,65536),metavar='PORT')
    parser.add_argument('--install-pipeline',action='store_true',help='Copy included pipeline scripts into workspace/work/ef12; back up existing files first')
    try:configure(parser.parse_args())
    except (ValueError,OSError,KeyError) as error:raise SystemExit(str(error))
