"""Validate combo trees and compile native EF-12 MTH/CMH rows."""
import hashlib
import re

BUTTONS = {'L': 'A', 'H': 'B', 'E': 'Y'}

def entry_commands(rows, action):
    raw = rows[action['row']][1]
    return [r for r in rows if len(r)>11 and r[0]=='CMH' and r[3]==raw and r[9]=='-']

def clean_combos(value, actions, clips, rows, assignments):
    if not isinstance(value,list) or len(value)>16: raise ValueError('Use up to 16 combo strings.')
    result=[]; roots=set(); all_ids=set()
    def integer(value, low, high, label):
        if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high:
            raise ValueError(f'{label} must be a whole number from {low} to {high}.')
        return value
    for combo in value:
        if not isinstance(combo,dict):raise ValueError('Invalid combo string.')
        ident=str(combo.get('id',''));name=str(combo.get('name','')).strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',ident) or ident in all_ids:raise ValueError('Combo IDs must be unique.')
        if not name or len(name)>64:raise ValueError('Give each combo a name of 1–64 characters.')
        all_ids.add(ident);entry=combo.get('entry');action=actions.get(entry)
        if not action or action['category']!='STRIKE' or not entry_commands(rows,action):raise ValueError('Choose an attack with a direct entry command for each combo.')
        if entry in roots:raise ValueError('Two strings cannot replace the same entry move. Use a branch in one string instead.')
        if entry in assignments:raise ValueError('This entry move also has a single-move replacement. Restore that replacement or choose another combo entry.')
        roots.add(entry);nodes=combo.get('nodes')
        if not isinstance(nodes,list) or not 2<=len(nodes)<=24:raise ValueError('A combo needs 2–24 moves.')
        found={};siblings=set();clean=[];depths={}
        for i,node in enumerate(nodes):
            if not isinstance(node,dict):raise ValueError('Invalid combo move.')
            nid=str(node.get('id',''));parent=node.get('parent')
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',nid) or nid in found:raise ValueError('Move IDs must be unique within each string.')
            if (i==0 and parent is not None) or (i>0 and parent not in found):raise ValueError('Each follow-up must connect to an earlier move; loops are not supported.')
            clip=node.get('clip');source=clips.get(clip)
            if not source:raise ValueError('A combo references a missing source animation.')
            if source['frames']<4:raise ValueError('Combo animations need at least four frames.')
            button=node.get('button','L')
            if button not in BUTTONS:raise ValueError('Combo attack inputs must be L, H or E.')
            direction=str(node.get('direction','5'))
            if direction not in '123456789' or len(direction)!=1:raise ValueError('Choose a valid follow-up direction.')
            damage=integer(node.get('damage',12),0,999,'Damage');hit=integer(node.get('hit',-1),-1,source['frames']-1,'Hit frame')
            start=end=0
            if i:
                limit=clips[found[parent]['clip']]['frames']-1
                start=integer(node.get('start',1),1,limit,'Transition frame')
                end=integer(node.get('end',limit),start,limit,'Follow-up deadline')
                key=(parent,button,direction)
                if key in siblings:raise ValueError('Branches from the same move need different button/direction inputs.')
                siblings.add(key)
            n=dict(id=nid,parent=parent,clip=clip,button=button,direction=direction,damage=damage,hit=hit,start=start,end=end)
            clean.append(n);found[nid]=n;depths[nid]=0 if i==0 else depths[parent]+1
        result.append(dict(id=ident,name=name,entry=entry,nodes=clean))
    return result

def motion_entries(recipe):
    return list(recipe['assignments'].values())+[n for c in recipe.get('combos',[]) for n in c['nodes']]

def configure_attack(row, motion, source, damage, hit, cancel=None):
    """A copied VF attack supplies attack part, strength and guard reaction defaults."""
    nf=source['frames'];hit=hit if hit>=0 else max(1,min(nf-3,round(nf*.35)))
    row[2]=motion;row[3]='Unique';row[4]='STAND[1]';row[5]='STRIKE';row[6]='-'
    row[7]=str(cancel if cancel is not None else max(1,nf-8));row[8]='6';row[9]='0';row[10]='-';row[21]='3'
    row[12]=f'[{hit}:{hit}:{min(nf-1,hit+2)}={damage}=0.05=0]'
    for col in (23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38):
        if len(row)>col:row[col]='-'
    return row

def compile_combos(rows, combos, actions, clips, native):
    report=[]
    templates={r[2]:r[:] for r in rows if len(r)>23 and r[0]=='MTH'}
    all_commands=[r for r in rows if len(r)>11 and r[0]=='CMH']
    default_cmd=next(r for r in all_commands if r[3]==next(a['raw_name'] for a in actions.values() if a['motion']=='M0_LJAB') and r[9]=='-')
    for combo in combos:
        action=actions[combo['entry']];root_raw=action['raw_name']
        entries=[r for r in all_commands if r[3]==root_raw and r[9]=='-']
        # Reuse entry inputs but remove their inherited combo descendants.
        root_names={r[1] for r in entries};blocked=set(root_names)
        while True:
            added={r[1] for r in all_commands if r[9] in blocked}-blocked
            if not added:break
            blocked.update(added)
        rows[:]=[r for r in rows if not (len(r)>9 and r[0]=='CMH' and r[1] in blocked-root_names)]
        key=hashlib.sha256(combo['id'].encode()).hexdigest()[:10]
        names={n['id']:f'DBZC_{key}_{i}' for i,n in enumerate(combo['nodes'])}
        commands={};depths={};route_report=[]
        for index,node in enumerate(combo['nodes']):
            name=names[node['id']];source=clips[node['clip']]
            template=templates['M_LHK' if node['button']=='H' else 'M0_LJAB']
            r=template[:];r[1]=name
            children=[n for n in combo['nodes'] if n['parent']==node['id']]
            configure_attack(r,native[node['clip']],source,node['damage'],node['hit'],min(n['start'] for n in children) if children else None)
            rows.append(r)
            if index==0:
                for command in entries:command[3]=name
                commands[node['id']]=[r[1] for r in entries];depths[node['id']]=0
            else:
                depths[node['id']]=depths[node['parent']]+1;commands[node['id']]=[]
                for branch,parent_command in enumerate(commands[node['parent']]):
                    c=default_cmd[:];c[1]=name+'_cmd'+str(branch);c[2]='150';c[3]=name
                    held='-' if node['direction']=='5' else 'D'+node['direction']
                    c[4]=f'[{BUTTONS[node["button"]]}:{held}:-:-:-:0:-]';c[5]='[STAND]';c[6]='-';c[7]='1';c[8]='1'
                    c[9]=parent_command;c[10]=f'{node["end"]}[{depths[node["id"]]}]';c[11]=str(node['start'])
                    # No inherited throw scripts, effects, resource conditions or combo-cut flags.
                    for col in range(13,len(c)):c[col]='-'
                    rows.append(c);commands[node['id']].append(c[1])
            route_report.append(dict(node=node['id'],parent=node['parent'],action=name,commands=commands[node['id']],source=node['clip'],native=native[node['clip']],transition=node['start'],deadline=node['end'],button=node['button'],engine_button=BUTTONS[node['button']],direction=node['direction']))
        report.append(dict(name=combo['name'],entry=action['display_name'],entry_commands=list(root_names),removed_followups=len(blocked-root_names),nodes=route_report))
    return report
