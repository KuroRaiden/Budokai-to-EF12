"""Readable VF action names and command summaries derived from the loaded header."""
import re

NAMES = dict(line.split('=', 1) for line in '''Goku_Footwork=Fighting stance
DASH_FORWARD=Forward dash
DASH_FORWARD_Q=Forward dash (fast)
DASH_BACK=Back dash
DASH_BACK_Q=Back dash (fast)
M_WALK_FORWARD=Walk forward
M_WALK_BACK=Walk backward
TA_POSE_C=Return to stance / stop walking
M_DASH_L=Sidestep left
M_DASH_R=Sidestep right
M_DASH_LR=Turn and sidestep left
M_DASH_RR=Turn and sidestep right
M_TA2SY=Enter crouch
M_RUN_ST=Start running
M_RUN_LP=Running loop
M_RUN_ED=Stop running
M_TURN=Turn around
M_TAGA_LP=Standing guard
M_SYGA_LP=Crouching guard
M_TURN_GST=Turn into standing guard
M_TURN_GSY=Turn into crouching guard
SY_POSE=Crouching stance
M_SY2TA=Stand up from crouch
M_SY_FWALK=Crouch walk forward
M_SY_BWALK=Crouch walk backward
JUMP_ST=Jump takeoff
JUMP_ST_Q=Jump takeoff (fast)
JUMP_AIR=Jump in place (air loop)
JUMP_FORWARD=Forward jump (air loop)
JUMP_BACK=Backward jump (air loop)
M0_LJAB=Left jab
M0_P6P=Shovel hook
M0_LJAB2=Second left jab
M0_5PPP=Right straight punch
M_LHK=Right high kick
M0_LHK2=Second high kick
M0_LHK3=Third high kick
M0_PPPLK=Low kick after punch combo
M0_PPPLKG=Guard recovery after low kick combo
M0_LHK2SEIKEN=Left straight punch after kicks
M0_R_UPPER=Right uppercut
M0_AS_MAWAK=Roundhouse kick
M0_HMAWAKFK=High spinning kick feint
M_SHORYU_Q=Rising uppercut
M_SHORYU=Rising uppercut (strong)
M0_SHORYU2JK=Jump kick after rising uppercut
M0_66K=Jumping roundhouse kick
M0_66KCLK=Low jumping roundhouse kick
M0_6P=Forward jab
M0_6PP=Downward punch follow-up
M0_6PPP=Straight punch finisher
M0_5PPPP=Fourth punch in combo
M0_5PPPPTK=Toe kick after four punches
M0_INSTEP_K=Instep kick
M0_INSTEP_K2MP=Straight punch after instep kick
M0_1LKLK=Low kick after instep kick
M0_3K=Stepping middle kick
M0_3KCFUMI=Stomp follow-up
M0_66P=Step-in right uppercut
M0_44P=Swaying straight punch
M0_44P2=Swaying punch follow-up 2
M0_44P2B=Swaying punch follow-up 2 (alternate)
M0_44P3=Swaying punch follow-up 3
M0_44PF=Swaying punch finisher
M0_BIN_CUT=Downward chopping strike
U_C0_9K=Rolling body kick
M0_66ST=Stepping high straight punch
M0_66ST2KO=Power punch follow-up
M0_66ST2KAKA=Heel kick follow-up
M0_BreakingBodyP=Haganken / body-breaking punch
M0_LowSweep=Low sweeping kick
M_REV_RP=Turnaround right punch
M_REV_HK2=Turnaround high kick
M_SLIDE_LUP=Sidestep uppercut
M_SMAWAK=Sidestep roundhouse kick
M_HMAWAKG=Spinning kick guard transition
M_SY_LP=Crouching left jab
M_SY_LPB=Second crouching left jab
M_R_SYLOWK=Crouching right low kick
M_L_CLOWK=Turnaround crouching low kick
M_SY_REVLP=Turnaround crouching jab
M_FJK=Forward jump kick
M_VJK=Vertical jump kick
M_BJK=Backward jump kick
M_AIR_LJAB=Air jab
M_JPLK=Air low kick
M_AirDmgEscape=Emergency air recovery
M_RUN_SLA=Running slide kick
M0_RUN_MST=Running middle punch
M_ST_TUKA=Standing grab
Crh_TUKAHIZA=Crouching knee grab
M_CATCH=Counter grab
MontTojo=Character entrance
Cmn_Win01=Victory pose'''.splitlines())

def friendly(raw, motion):
    if raw.startswith('mth_AirCover'): return 'Air recovery ' + ('right' if raw.endswith('R') else 'left')
    if motion == 'Goku_Footwork': return 'Fighting stance — ' + ('entry' if raw.endswith('１') else 'loop')
    if motion in NAMES: return NAMES[motion]
    if motion.startswith(('M_AOKI_', 'M_UOKI_')) and ('MK' in motion or 'LK' in motion or 'HK' in motion):
        return 'Get-up ' + ('low kick' if 'LK' in motion else 'middle kick') + (' (face down)' if motion.startswith('M_U') else ' (face up)') + (' — toward head' if motion.endswith('180') else ' — toward feet')
    if motion.startswith(('M_AO_', 'M_UTSU_')) or motion in ('M_ADOWN_POSE','M_UDOWN_POSE','M_AOKI_00','M_AOKI_180'):
        pose='face down' if 'UTSU' in motion or motion=='M_UDOWN_POSE' else 'face up'
        role=next((v for k,v in [('KOTEN','Roll backward to stand'),('ZENTEN','Roll forward to stand'),('RGORO','Roll right'),('LGORO','Roll left'),('POSE','Downed idle')] if k in motion),'Get up')
        return f'{role} ({pose})' + (' — turn' if motion.endswith('_R') or motion.endswith('180') else '')
    english=re.sub(r'[^\x20-\x7e]','',raw).split('_')
    text=' '.join(x for x in english if x and x not in ('mth','mtn'))
    text=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',text)
    for a,b in [('Passive','(receiving throw)'),('Active','(performing throw)'),('Dif Skl','alternate rig'),('Diff SKL','alternate rig'),('Seoi','Shoulder throw'),('German SPX','German suplex')]:text=text.replace(a,b)
    return text.strip() or 'Template action'

DIRECTIONS={'1':'↙','2':'↓','3':'↘','4':'←','5':'neutral','6':'→','7':'↖','8':'↑','9':'↗'}
def input_summary(raw):
    steps=[]
    for block in re.findall(r'\[([^\]]+)\]', raw):
        fields=block.split(':'); parts=[]
        if len(fields)!=7:return 'See advanced command details'
        for index,prefix in [(0,''),(1,'hold '),(2,'release '),(3,'release '),(4,'hold ')]:
            value=fields[index]
            if value in ('','-'):continue
            value=re.sub(r'\((\d+)\)',r' for \1 frames',value)
            value=re.sub(r'(?:D[1-9]){2,}',lambda m:'('+ ' / '.join(DIRECTIONS[n] for n in re.findall(r'D([1-9])',m[0])) +')',value)
            value=re.sub(r'D([1-9])',lambda m:DIRECTIONS[m[1]],value).rstrip('-')
            value=re.sub(r'(?<=[ABXY])(?=[ABXY])',' + ',value)
            parts.append(prefix+value)
        steps.append(' + '.join(parts) or 'automatic')
    return ' then '.join(steps) or 'automatic'

def decorate(actions, rows):
    commands=[r for r in rows if len(r)>10 and r[0]=='CMH']
    byname={r[1]:r for r in commands}
    def chain(r, seen=()):
        if r[1] in seen:return input_summary(r[4])
        parent=byname.get(r[9])
        return (chain(parent,seen+(r[1],))+' then ' if parent else '')+input_summary(r[4])
    for a in actions:
        raw=rows[a['row']][1];a['display_name']=friendly(raw,a['motion'])
        related=[r for r in commands if r[3]==raw]
        a['commands']=[dict(input=chain(r),state=r[5],raw=r[4],parent=r[9]) for r in related]
        a['input']=' / '.join(dict.fromkeys(chain(r) for r in related)) or 'Automatic / follow-up animation'
        a['target_level']={'Hi':'High','Mid':'Middle','Low':'Low'}.get(rows[a['row']][13],rows[a['row']][13])
        a['raw_name']=raw
