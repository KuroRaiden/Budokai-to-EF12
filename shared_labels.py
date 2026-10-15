"""Descriptive labels from shared-bank motion review, not official move names.

Scoped to BCCMN child 2. Indices from other banks must not inherit these labels.
Original file names, clip IDs and frame counts remain unchanged.
"""
COMMON={
0:'Fighting idle',1:'Guarded stance',2:'Forward dash',3:'Backward evasive hop',
4:'Left sidestep dash',5:'Right sidestep dash',6:'Raise arms and brace',
7:'Braced defensive hold',8:'Return from braced stance',9:'Forward-leaning flight pose',
10:'Extended flight pose',11:'Short forward step',12:'Forward lean transition',
13:'Forward-leaning hold',14:'Short backward step',15:'Defensive sway A',
16:'Defensive sway B',17:'Right-arm extension',18:'Left-arm extension',
19:'Air fighting idle',20:'Air guarded stance',21:'Air forward dash',
22:'Air backward evasive hop',23:'Air right sidestep dash',24:'Air left sidestep dash',
25:'Air raise arms and brace',26:'Air braced defensive hold',27:'Air return from braced stance',
28:'Air forward-leaning pose',29:'Air extended flight pose',30:'Air short forward step',
31:'Air arm-forward hold',32:'Air low-arm hold',33:'Air short backward step',
34:'Air defensive sway A',35:'Air defensive sway B',36:'Air right-arm extension',
37:'Air left-arm extension',50:'Backward travelling recoil',63:'Air backward travelling recoil',
64:'Low forward recoil',65:'Air low forward recoil',
96:'Deep body recoil A',97:'Deep body recoil B',98:'Backward body recoil',99:'Forward body recoil',
100:'Forward travelling stumble A',101:'Forward travelling stumble B',
102:'Backward travelling stumble A',103:'Backward travelling stumble B',
104:'Air torso recoil A',105:'Air torso recoil B',
134:'Air deep body recoil A',135:'Air deep body recoil B',136:'Air backward body recoil',137:'Air forward body recoil',
138:'Tumbling fall A',139:'Tumbling fall B',140:'Horizontal fall transition A',
141:'Vertical drop A',142:'Rise from low pose A',143:'Standing-to-ground fall A',
144:'Standing-to-ground fall B',145:'Lying flat hold A',146:'Get-up from ground A',
147:'Horizontal fall transition B',148:'Vertical drop B',149:'Rise from low pose B',
150:'Standing-to-ground fall C',151:'Ground impact A',152:'Ground impact B',
153:'Lying flat hold B',154:'Get-up from ground B',155:'Air low-pose recovery A',
156:'Air tumbling fall',157:'Bent-over horizontal hold',158:'Air low-pose recovery B',
159:'Air turning recovery',160:'Ground drop A',161:'Ground drop B',
162:'Bent-over ground hold',163:'Air rising recovery',164:'Horizontal falling hold A',
165:'Horizontal falling hold B',166:'Turning recovery',167:'Stretched ground hold A',
168:'Stretched ground hold B',169:'Get-up with low turn A',170:'Air get-up with low turn A',
171:'Get-up with low turn B',172:'Air get-up with low turn B',
173:'Forward low recovery A',174:'Air forward low recovery A',
175:'Forward low recovery B',176:'Air forward low recovery B',
177:'Horizontal airborne hold A',178:'Horizontal airborne hold B',
179:'Tumbling recovery A',180:'Tumbling recovery B',181:'Tumbling recovery C',
182:'Falling pose A',183:'Falling pose B',184:'Falling pose C',185:'Falling pose D',
186:'Ground landing A',187:'Ground landing B',188:'Ground landing C',189:'Ground landing D',
190:'Recovery twist A',191:'Recovery twist B',192:'Recovery twist C',193:'Recovery twist D',194:'Recovery twist E',
195:'Stretched-out fall hold',196:'Standing flinch recovery A',197:'Standing flinch recovery B',
198:'Forward hand thrust A',199:'Forward hand thrust B',200:'Air forward hand thrust A',201:'Air forward hand thrust B',
220:'Raised-arm reach',221:'Air raised-arm reach',222:'Compact defensive stance',223:'Air compact defensive stance',
224:'Low-arm braced stance',225:'Air low-arm braced stance',226:'Quick torso sway',227:'Air quick torso sway',
228:'Forward-bent hold',229:'Air forward-bent hold',230:'Quick upper-body turn A',231:'Air quick upper-body turn A',
232:'Arms-out transition A',233:'Air arms-out transition A',234:'Bent-arm hold',235:'Air bent-arm hold',
236:'Quick upper-body turn B',237:'Air quick upper-body turn B',238:'Brief arm-up pose',239:'Brief arms-out pose',
240:'Arms-forward reach',241:'Long backward dash A',242:'Long backward dash B',
243:'Long forward dash A',244:'Long forward dash B',245:'Forward dash recovery',246:'Backward dash recovery',
247:'Vertical tumble A',248:'Vertical tumble B',249:'Hands-low transition A',250:'Air hands-low transition A',
251:'Slumped standing hold A',252:'Air slumped standing hold A',253:'Return to standing A',254:'Air return to standing A',
255:'Hands-near-head transition',256:'Air hands-near-head transition',257:'Head-clutching hold',258:'Air head-clutching hold',
259:'Return to guarded stance',260:'Air return to guarded stance',261:'Low turning movement',
262:'Brief horizontal pose',263:'Turning body recoil',264:'Backward tumbling recovery',
}

def variants(start,end,title):
    for index in range(start,end+1):COMMON[index]=f'{title} {index-start+1:02}'

variants(38,49,'Standing recoil')
variants(51,62,'Air recoil')
variants(66,89,'Standing hit-response motion')
variants(90,92,'Backward travelling reaction')
variants(93,95,'Forward travelling reaction')
variants(106,129,'Air hit-response motion')
variants(130,131,'Air forward travelling reaction')
variants(132,133,'Air backward travelling reaction')
variants(202,210,'Quick upper-body sway')
variants(211,219,'Air quick upper-body sway')

def shared_label(path,index):
    """Return only bank-scoped descriptions; never label character clips by index alone."""
    archive=path.parent.name.upper()
    if archive=='0000_BCCMN.AMB' and path.name.lower()=='0002.amm':
        label=COMMON.get(index)
        if label:
            tags=['shared','common','descriptive']
            if index in (3,22):tags+=['dash','backward','evade']
            if 'dash' in label.lower() or 'step' in label.lower():tags+=['movement','travel','dodge']
            if index in (1,6,7,8,15,16,20,25,26,27,34,35,222,223):tags+=['guard','block','defense','brace']
            if any(word in label.lower() for word in ('recoil','reaction','response','fall','ground')):tags+=['damage','hurt','recovery']
            return dict(label=label,label_kind='description',label_note='Descriptive name from shared-motion review; not an original game label.',tags=tags)
    if archive in ('0005_BBDST.AMB','0008_BBMND.AMB','0012_BBSNW.AMB','0013_BBTPL.AMB'):
        bank=archive.split('_',1)[1].split('.')[0]
        return dict(label=f'Environment bank {bank} — motion {index:03}',label_kind='bank',label_note='Environment-bank label; its gameplay purpose is unverified.',tags=['environment','stage','shared',bank])
    return None
