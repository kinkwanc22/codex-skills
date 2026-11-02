import copy, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest

SCRIPT = pathlib.Path(__file__).with_name('opening_rotation.py')
spec = importlib.util.spec_from_file_location('rotation', SCRIPT)
rotation = importlib.util.module_from_spec(spec); spec.loader.exec_module(rotation)

def fixture():
    return {'revision': 0, 'cycle': 1, 'used_in_cycle': ['a','b'], 'last_batch_groups': ['b'], 'active_plan': None, 'history': [],
            'groups': [{'id': c, 'label': c, 'enabled': True, 'last_used_at': None, 'assets': [{'sha256': c, 'readable': True}]} for c in 'abcd']}

class Tests(unittest.TestCase):
    def test_exhaust_then_cross_cycle(self):
        plan = rotation.allocate(fixture(), 'test', 3)
        self.assertEqual({v['group_id'] for v in plan['selections'][:2]}, {'c','d'})
        self.assertEqual([v['cycle'] for v in plan['selections']], [1,1,2])
        self.assertEqual(len({v['group_id'] for v in plan['selections']}), 3)
        self.assertEqual(plan['selections'][2]['group_id'], 'a')

    def test_same_scene_variants_not_extra_quota(self):
        s=fixture();s['groups'][0]['assets'].append({'sha256':'alias','readable':True})
        with self.assertRaises(ValueError): rotation.allocate(s,'big',5)

    def test_disabled_unreadable_not_selected(self):
        s=fixture();s['groups'][2]['enabled']=False;s['groups'][3]['assets'][0]['readable']=False
        plan=rotation.allocate(s,'small',2)
        self.assertEqual({x['group_id'] for x in plan['selections']},{'a','b'})

    def test_commit_does_not_consume_missing_drafts(self):
        s=fixture();s['active_plan']=rotation.allocate(s,'batch',1);before=copy.deepcopy(s)
        item=s['active_plan']['selections'][0]
        with self.assertRaises(ValueError): rotation.commit(s,'batch',[{'group_id':item['group_id'],'source_sha256':item['candidates'][0]['sha256'],'draft_path':'/does-not-exist'}])
        self.assertEqual(s,before)

    def test_cli_resume_reserve_commit(self):
        with tempfile.TemporaryDirectory() as td:
            base=pathlib.Path(td);state=base/'state.json';out=base/'plan.json';state.write_text(json.dumps(fixture()))
            def cli(*args): return subprocess.run([sys.executable,str(SCRIPT),*args,'--state',str(state)],capture_output=True,text=True)
            self.assertEqual(cli('plan','--batch-id','x','--count','3','--out',str(out)).returncode,0)
            plan=json.loads(out.read_text());s=json.loads(state.read_text());self.assertEqual(s['used_in_cycle'],['a','b'])
            self.assertEqual(cli('plan','--batch-id','x','--count','3','--out',str(out)).returncode,0)
            self.assertEqual(json.loads(out.read_text()),plan)
            self.assertNotEqual(cli('plan','--batch-id','y','--count','1','--out',str(base/'y.json')).returncode,0)
            delivered=[]
            for n,item in enumerate(plan['selections']):
                d=base/str(n);d.mkdir();(d/'draft_content.json').write_text('{}')
                delivered.append({'group_id':item['group_id'],'source_sha256':item['candidates'][0]['sha256'],'draft_path':str(d)})
            df=base/'delivery.json';df.write_text(json.dumps(delivered))
            self.assertEqual(cli('commit','--batch-id','x','--delivery',str(df)).returncode,0)
            s=json.loads(state.read_text());self.assertEqual(s['cycle'],2);self.assertIsNone(s['active_plan'])
            self.assertNotEqual(cli('commit','--batch-id','x','--delivery',str(df)).returncode,0)

    def test_cancel_keeps_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            s=fixture();s['active_plan']=rotation.allocate(s,'cancel',1);f=pathlib.Path(td)/'state.json';f.write_text(json.dumps(s))
            r=subprocess.run([sys.executable,str(SCRIPT),'cancel','--batch-id','cancel','--state',str(f)],capture_output=True)
            self.assertEqual(r.returncode,0);after=json.loads(f.read_text());self.assertEqual(after['used_in_cycle'],s['used_in_cycle']);self.assertIsNone(after['active_plan'])

if __name__=='__main__': unittest.main()
