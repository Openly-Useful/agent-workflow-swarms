#!/usr/bin/env python3
"""Functional process-boundary tests; these are not model behavior evaluations."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

CLI=Path(__file__).resolve().parents[1]/'skills/loop-improvement/scripts/loop.py'

class LoopTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'candidate.txt').write_text('Use explicit session selection')
        (self.root/'oracle.py').write_text('import sys\nmode,case=sys.argv[1:]\nraise SystemExit(1 if mode=="baseline" and case=="target" else 0)\n')
        self.contract={'evaluator_revision':'fixture-v1','lesson_artifacts':['candidate.txt'],'cases':[
            {'id':role,'role':role,'baseline':[sys.executable,'oracle.py','baseline',role],
             'candidate':[sys.executable,'oracle.py','candidate',role],'timeout_seconds':2,'artifacts':['oracle.py','candidate.txt']}
            for role in ['target','guard']]}
    def call(self,command,data=None,ok=True,**options):
        argv=[sys.executable,str(CLI),'--project-root',str(self.root),command]
        if data is not None:
            path=self.root/('input-'+hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()+'.json')
            path.write_text(json.dumps(data));argv+=['--input',str(path)]
        for k,v in options.items():argv+=['--'+k.replace('_','-'),str(v)]
        r=subprocess.run(argv,capture_output=True,text=True)
        if ok:self.assertEqual(r.returncode,0,r.stderr)
        else:self.assertNotEqual(r.returncode,0,r.stdout)
        return json.loads(r.stdout if ok else r.stderr)
    def proposal(self):
        m=self.call('capture',{'milestone':'integration','task_key':'session-selection','revision':'fixture-r1',
                              'outcome':'failed','summary':'Ambiguous session selection failed','artifacts':['candidate.txt']})['milestone_id']
        p=self.call('propose',{'schema_version':1,'proposal_id':'prop_fixture','skill':'conductor-swarm','kind':'correction',
                             'title':'Select session','rationale':'Avoid ambiguity','suggested_change':'Pass explicit session ID',
                             'signals':['Ambiguity'],'observation_ids':['obs_fixture'],'confidence':0.7,
                             'raw_evidence':'must never be persisted'},milestone=m)['proposal_id']
        return p
    def evaluated(self,contract=None):
        return self.call('evaluate',contract or self.contract,proposal=self.proposal())
    def accepted(self):
        e=self.evaluated();self.assertTrue(e['passed'])
        return self.call('accept',{'reviewer':'fixture-reviewer','rationale':'Both checks inspected','expires_at':time.time()+3600},experiment=e['experiment_id'])['lesson_id']
    def test_fresh_process_lifecycle_reuses_and_retires(self):
        lesson=self.accepted()
        out=self.call('retrieve',task_key='session-selection')
        self.assertEqual(out['count'],1);self.assertEqual(out['lessons'][0]['lesson_id'],lesson)
        self.assertEqual(out['lessons'][0]['authority'],'advisory_only')
        self.assertEqual(self.call('retrieve',task_key='unrelated')['count'],0)
        self.call('retire',lesson=lesson,reason='Superseded by changed assumptions')
        self.assertEqual(self.call('retrieve',task_key='session-selection')['count'],0)
    def test_readonly_does_not_initialize_state(self):
        self.call('status');self.call('retrieve',task_key='missing')
        self.assertFalse((self.root/'.loop-improvement').exists())
    def test_readonly_preserves_database(self):
        self.accepted();path=self.root/'.loop-improvement/lessons.sqlite3';before=path.read_bytes()
        self.call('status');self.call('retrieve',task_key='session-selection')
        self.assertEqual(before,path.read_bytes())
    def test_changed_artifact_invalidates_retrieval(self):
        self.accepted();(self.root/'candidate.txt').write_text('changed')
        self.assertEqual(self.call('retrieve',task_key='session-selection')['count'],0)
    def test_changed_evaluator_blocks_acceptance(self):
        e=self.evaluated();(self.root/'oracle.py').write_text('raise SystemExit(0)')
        self.call('accept',{'reviewer':'reviewer','rationale':'checked','expires_at':time.time()+60},experiment=e['experiment_id'],ok=False)
    def test_regression_blocks_promotion(self):
        self.contract['cases'][1]['candidate']=[sys.executable,'-c','raise SystemExit(1)']
        e=self.evaluated();self.assertFalse(e['passed'])
        self.call('accept',{'reviewer':'reviewer','rationale':'checked','expires_at':time.time()+60},experiment=e['experiment_id'],ok=False)
    def test_no_improvement_is_not_a_pass(self):
        self.contract['cases'][0]['baseline']=self.contract['cases'][0]['candidate']
        self.assertFalse(self.evaluated()['passed'])
    def test_timeout_is_not_improvement(self):
        self.contract['cases'][0]['baseline']=[sys.executable,'-c','import time; time.sleep(2)']
        self.contract['cases'][0]['timeout_seconds']=0.05
        self.assertFalse(self.evaluated()['passed'])
    def test_guard_required(self):
        self.contract['cases'][1]['role']='target'
        self.call('evaluate',self.contract,proposal=self.proposal(),ok=False)
    def test_repeated_proposal_is_idempotent_and_drops_raw_evidence(self):
        self.assertEqual(self.proposal(),self.proposal())
        counts=self.call('status')['counts'];self.assertEqual(counts['proposal'],1);self.assertEqual(counts['milestone'],1)
        con=sqlite3.connect(self.root/'.loop-improvement/lessons.sqlite3')
        try:self.assertNotIn('must never be persisted',str(con.execute('SELECT body FROM records').fetchall()))
        finally:con.close()
    def test_concurrent_milestone_capture_deduplicates(self):
        data={'milestone':'integration','task_key':'session-selection','revision':'fixture-r1','outcome':'failed',
              'summary':'Concurrent observation','artifacts':['candidate.txt']}
        path=self.root/'capture.json';path.write_text(json.dumps(data))
        def run(_):
            return subprocess.run([sys.executable,str(CLI),'--project-root',str(self.root),'capture','--input',str(path)],capture_output=True,text=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,range(4)))
        for r in results:self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(len({json.loads(r.stdout)['milestone_id'] for r in results}),1)
    def test_expiry_and_private_material_rejected(self):
        e=self.evaluated()
        self.call('accept',{'reviewer':'reviewer','rationale':'checked','expires_at':time.time()-1},experiment=e['experiment_id'],ok=False)
        self.call('capture',{'milestone':'m','task_key':'t','revision':'r','outcome':'failed','summary':'/Users/private/data',
                             'artifacts':['candidate.txt']},ok=False)
    def test_concurrent_acceptance_cannot_duplicate_or_revive(self):
        e=self.evaluated()
        inputs=[]
        for i in range(12):
            p=self.root/('decision-'+str(i)+'.json')
            p.write_text(json.dumps({'reviewer':'reviewer-'+str(i),'rationale':'checked','expires_at':time.time()+3600+i}))
            inputs.append(p)
        def run(p):
            return subprocess.run([sys.executable,str(CLI),'--project-root',str(self.root),'accept','--experiment',e['experiment_id'],'--input',str(p)],capture_output=True,text=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(run,inputs))
        for r in results:self.assertEqual(r.returncode,0,r.stderr)
        ids={json.loads(r.stdout)['lesson_id'] for r in results}
        self.assertEqual(len(ids),1)
        lesson=ids.pop();self.call('retire',lesson=lesson,reason='retired')
        self.assertEqual(run(inputs[0]).returncode,0)
        self.assertEqual(self.call('retrieve',task_key='session-selection')['count'],0)
    def test_malformed_inputs_return_json_errors(self):
        self.call('capture',{'milestone':'m','task_key':'t','revision':'r','outcome':'failed','summary':'bounded','artifacts':[{}]},ok=False)
        self.contract['cases']=[None,{}]
        self.call('evaluate',self.contract,proposal=self.proposal(),ok=False)
    def test_artifact_escape_rejected(self):
        self.call('capture',{'milestone':'m','task_key':'t','revision':'r','outcome':'failed','summary':'example',
                             'artifacts':['../outside']},ok=False)

if __name__=='__main__':unittest.main(verbosity=2)
