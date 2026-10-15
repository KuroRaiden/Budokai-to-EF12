import sys,csv,copy,hashlib,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from combos import clean_combos,compile_combos,motion_entries
from action_labels import decorate

def mth(name,motion):
 r=['-']*45;r[0]='MTH';r[1]=name;r[2]=motion;r[5]='STRIKE';r[13]='H';return r

def cmh(name,action,button,parent='-'):
 r=['-']*45;r[0]='CMH';r[1]=name;r[2]='100';r[3]=action;r[4]='['+button+':-:-:-:-:0:-]';r[5]='[STAND]';r[9]=parent;return r
ROWS=[mth('Jab','M0_LJAB'),mth('Kick','M_LHK'),mth('Follow','follow'),cmh('JabCmd','Jab','A'),cmh('KickCmd','Kick','B'),cmh('OldFollow','Follow','A','JabCmd')]
A=[dict(id=hashlib.sha256(('MotHead-1.csv'+'|'+r[1]).encode()).hexdigest()[:16],row=i,motion=r[2],category=r[5]) for i,r in enumerate(ROWS) if len(r)>23 and r[0]=='MTH']
decorate(A,ROWS);A={a['id']:a for a in A};ENTRY=next(a['id'] for a in A.values() if a['motion']=='M0_LJAB')
CLIPS={'one':dict(frames=26),'two':dict(frames=34),'three':dict(frames=40)}
def draft():
 return [dict(id='test',name='LLH with E branch',entry=ENTRY,nodes=[dict(id='n1',parent=None,clip='one',button='L',direction='5',damage=12,hit=-1,start=0,end=0),dict(id='n2',parent='n1',clip='two',button='L',direction='5',damage=13,hit=9,start=10,end=23),dict(id='n3',parent='n2',clip='three',button='H',direction='5',damage=18,hit=-1,start=15,end=30),dict(id='n4',parent='n2',clip='one',button='E',direction='6',damage=20,hit=-1,start=15,end=32)])]
class ComboTests(unittest.TestCase):
 def clean(self,d=None,assignments={}):return clean_combos(d or draft(),A,CLIPS,ROWS,assignments)
 def test_compile_branch_and_preserve_other_entries(self):
  c=self.clean();rows=copy.deepcopy(ROWS);native={k:'native_'+k for k in CLIPS};report=compile_combos(rows,c,A,CLIPS,native)
  self.assertEqual(len(report[0]['nodes']),4);self.assertGreater(report[0]['removed_followups'],0)
  for n in report[0]['nodes'][1:]:
   command=next(r for r in rows if r[0]=='CMH' and r[1]==n['commands'][0]);self.assertEqual(command[11],str(n['transition']));self.assertTrue(command[10].startswith(str(n['deadline'])+'['))
   self.assertTrue(any(r[0]=='CMH' and r[1]==command[9] for r in rows))
  branch=next(r for r in rows if len(r)>4 and r[0]=='CMH' and r[3]==report[0]['nodes'][3]['action']);self.assertEqual(branch[4],'[Y:D6:-:-:-:0:-]')
  kick=next(r for r in ROWS if len(r)>9 and r[0]=='CMH' and r[3]==next(a['raw_name'] for a in A.values() if a['motion']=='M_LHK') and r[9]=='-');self.assertIn(kick,rows)
  names={r[1] for r in rows if len(r)>3 and r[0]=='CMH'}
  for r in rows:
   if len(r)>9 and r[0]=='CMH' and r[1].startswith('DBZC_'):self.assertIn(r[9],names)
  self.assertEqual(len(motion_entries(dict(assignments={},combos=c))),4)
 def test_invalid_loop(self):
  c=draft();c[0]['nodes'][1]['parent']='n3'
  with self.assertRaises(ValueError):self.clean(c)
 def test_duplicate_branch(self):
  c=draft();c[0]['nodes'][3].update(button='H',direction='5')
  with self.assertRaises(ValueError):self.clean(c)
 def test_parent_deadline(self):
  c=draft();c[0]['nodes'][1]['end']=26
  with self.assertRaises(ValueError):self.clean(c)
 def test_assignment_conflict(self):
  with self.assertRaises(ValueError):self.clean(assignments={ENTRY:{}})
 def test_singleton(self):
  c=draft();c[0]['nodes']=c[0]['nodes'][:1]
  with self.assertRaises(ValueError):self.clean(c)
 def test_nonfinite(self):
  c=draft();c[0]['nodes'][2]['damage']=float('nan')
  with self.assertRaises(ValueError):self.clean(c)
 def test_shared_clip_distinct_steps(self):
  rows=copy.deepcopy(ROWS);report=compile_combos(rows,self.clean(),A,CLIPS,{k:'native_'+k for k in CLIPS})
  self.assertNotEqual(report[0]['nodes'][0]['action'],report[0]['nodes'][3]['action'])
if __name__=='__main__':unittest.main()
