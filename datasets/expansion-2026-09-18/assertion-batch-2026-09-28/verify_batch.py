"""Recompute evidence gates independently of both execution programs."""
import ast
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(o):
    a=np.asarray(o['values'],dtype=o['dtype'])
    assert list(a.shape)==o['shape']
    return a
def hashes(base, mapping):
    for f,h in mapping.items():assert sha(base/f)==h,f
def keyed(rows, fields):
    index={tuple(r[k] for k in fields):r for r in rows}
    assert len(index)==len(rows), 'duplicate record identity'
    return index


def verify_diagnostic():
    manifest=load(ROOT/'manifest.json');hashes(ROOT,manifest['files'])
    run=ROOT/'run-01';hashes(run,load(run/'SHA256.json'))
    probes=load(DATA/'runs/2026-09-20-dynamic-v3/inputs.freeze.json')
    assert sha(DATA/'runs/2026-09-20-dynamic-v3/inputs.freeze.json')==manifest['input_manifest_sha256']
    payload=load(run/'executions.json');rows=payload['records']
    index=keyed(rows,['case_id','input_index','side','mode','repeat'])
    gates={(g['case_id'],g['input_index']):g for g in payload['gates']}
    assert len(gates)==len(probes)==1920
    expected_keys=set();outcomes=[]
    def group(cid,i,side,mode):
        keys=[(cid,i,side,mode,r) for r in range(3)];expected_keys.update(keys)
        return [index[k] for k in keys]
    def stable(rs):
        fields=['status','native','delivered','assertion','error','message']
        return all([r.get(k) for k in fields]==[rs[0].get(k) for k in fields] for r in rs)
    for p in probes:
        cid=p['case_id'];i=p['input_index'];e=np.asarray(p['expected']['values'],dtype=p['expected']['dtype'])
        def qualified(r):
            if r['status']!='executed':return False
            a=arr(r['native']);ref=a.shape==e.shape and a.dtype==e.dtype and np.allclose(a,e,**p['tolerance'])
            assert bool(ref)==r['reference_ok']
            assert r['delivered']==r['native']
            return bool(ref and r['assertion']=='accepted')
        sr=group(cid,i,'source','original');sq=stable(sr) and all(qualified(r) for r in sr)
        tq=False;transparent=False;witnesses=[]
        if sq:
            tr=group(cid,i,'target','original');tq=stable(tr) and all(qualified(r) for r in tr)
            if tq:
                transparent=True
                for side,base in [('source',sr[0]),('target',tr[0])]:
                    for mode in ['observe','reinject']:
                        rr=group(cid,i,side,mode)
                        transparent &= stable(rr) and all(r.get('native')==base['native'] and r.get('delivered')==base['native'] and r.get('assertion')=='accepted' for r in rr)
                if transparent:
                    for mode in ['wrong-shape','wrong-value']:
                        s=group(cid,i,'source',mode);t=group(cid,i,'target',mode)
                        assert stable(s) and stable(t)
                        expected=e.reshape((1,)+e.shape) if mode=='wrong-shape' else (e+(np.abs(e)*.2+10)).astype(e.dtype)
                        for r in s+t:
                            assert r['status']=='executed'
                            assert np.array_equal(arr(r['delivered']),expected) and arr(r['delivered']).shape==expected.shape
                            valid=expected.shape==e.shape and (cid=='E018' or np.allclose(expected,e,**p['tolerance']))
                            assert bool(valid)==r['valid_for_scope']
                            if r['assertion']=='rejected':
                                assert any(f['name']=='check' for f in r['assertion_frames']), 'rejection outside registered assertion'
                        assert s[0]['delivered']==t[0]['delivered']
                        if not s[0]['valid_for_scope'] and all(r['assertion']=='rejected' for r in s) and all(r['assertion']=='accepted' for r in t):witnesses.append(mode)
        assert (sq,tq,bool(transparent))==(gates[cid,i]['source_qualified'],gates[cid,i]['target_qualified'],gates[cid,i]['probe_gate'])
        outcomes.append({'case_id':cid,'input_index':i,'source_qualified':sq,'target_qualified':tq,'sensitivity_qualified':bool(transparent),'witnesses':witnesses})
    assert set(index)==expected_keys, 'extra or missing execution'
    return {'single_executions':len(rows),'inputs':len(outcomes),'source_qualified':sum(o['source_qualified'] for o in outcomes),
            'sensitivity_qualified':sum(o['sensitivity_qualified'] for o in outcomes),'intent_loss_witnesses':sum(len(o['witnesses']) for o in outcomes),
            'candidate_assertions_identical_by_construction':True,'evidence_grade':'protocol diagnostic only'}


def verify_retained():
    regs=load(ROOT/'retained/registration.json');hashes(ROOT/'retained',load(ROOT/'retained/SHA256.json'))
    data=load(ROOT/'retained-executions-v2.json');rows=data['records']
    ix=keyed(rows,['case_id','scenario','side','mode','repeat']);expected=set();matrix=[]
    for reg in regs:
        cid=reg['case_id']
        if reg['status']!='registered':matrix.append({'case_id':cid,'status':'unresolved-obligation','reason':reg['reason']});continue
        upstream=ast.parse((ROOT/reg['file']).read_text());cl=next(n for n in upstream.body if isinstance(n,ast.ClassDef) and n.name==reg['class'])
        source=ast.parse((ROOT/'retained'/(cid+'-source.py')).read_text());target=ast.parse((ROOT/'retained'/(cid+'-target.py')).read_text())
        for n in source.body[0].body:
            orig=copy.deepcopy(next(m for m in cl.body if isinstance(m,ast.FunctionDef) and m.name==n.name));orig.decorator_list=[]
            assert ast.dump(orig)==ast.dump(n), 'source method altered'
        class ExpectedMigration(ast.NodeTransformer):
            def visit_Call(self,n):
                self.generic_visit(n)
                if ast.unparse(n.func) in reg['paths']:n.func=ast.Name(id='_operation',ctx=ast.Load())
                elif isinstance(n.func,ast.Attribute) and 'METHOD:'+n.func.attr in reg['paths']:
                    n.args=[n.func.value]+n.args;n.func=ast.Name(id='_operation',ctx=ast.Load())
                return n
        assert ast.dump(ExpectedMigration().visit(copy.deepcopy(source)))==ast.dump(target),'unregistered candidate change'
        scenarios=[0,16] if int(cid[1:])<=16 else [None];scope=[]
        for scenario in scenarios:
            def group(side,mode):
                keys=[(cid,scenario,side,mode,i) for i in range(3)];expected.update(keys);return [ix[k] for k in keys]
            groups={(side,mode):group(side,mode) for side in ['source','target'] for mode in ['original','observe','reinject','wrong-shape','wrong-value']}
            for rs in groups.values():
                def signature(r):return [r[k] for k in ['status','phase','operation_count','first_observation','error']]
                assert all(signature(r)==signature(rs[0]) for r in rs), (cid,scenario,'unstable')
            baseline=all(r['status']=='passed' for (side,mode),rs in groups.items() if mode in ['original','observe','reinject'] for r in rs)
            transparent=baseline
            if baseline:
                for side in ['source','target']:
                    obs=groups[side,'observe'][0];rein=groups[side,'reinject'][0]
                    assert obs['operation_count']>0
                    transparent &= obs['first_observation']==rein['first_observation'] and obs['operation_count']==rein['operation_count']
                transparent &= groups['source','observe'][0]['first_observation']==groups['target','observe'][0]['first_observation']
            probes={}
            for mode in ['wrong-shape','wrong-value']:
                s=groups['source',mode][0];t=groups['target',mode][0]
                result='baseline-unqualified'
                if transparent:
                    if s['status']=='execution-error' or t['status']=='execution-error':result='probe-runtime-error'
                    elif not s['first_observation'] or not t['first_observation']:result='missing-observation'
                    else:
                        so=s['first_observation'][0];to=t['first_observation'][0]
                        a=arr(so['native']);z=arr(so['delivered'])
                        expected_z=a.reshape((1,)+a.shape) if mode=='wrong-shape' else (a+(np.abs(a)*.2+10)).astype(a.dtype) if a.dtype.kind in 'fiu' else np.logical_not(a)
                        assert np.array_equal(expected_z,z) and expected_z.shape==z.shape
                        if so!=to:result='unequal-observations'
                        elif s['status']=='assertion-rejected':
                            assert s['frames'] and any(f['file'].endswith(cid+'-target.py') for f in s['frames'])
                            result='rejection-retained' if t['status']=='assertion-rejected' else 'potential-loss-needs-obligation-review'
                        else:result='source-does-not-reject'
                probes[mode]=result
            failures=[{'side':side,'status':rs[0]['status'],'phase':rs[0]['phase'],'error':rs[0]['error']} for (side,mode),rs in groups.items() if mode=='original' and rs[0]['status']!='passed']
            scope.append({'scenario':scenario,'baseline_qualified':bool(baseline),'transparent':bool(transparent),'probes':probes,'baseline_failures':failures})
        matrix.append({'case_id':cid,'status':'checked-with-retained-bodies','kind':reg['kind'],'scenarios':scope,'human_review':'pending'})
    assert set(ix)==expected and len(rows)==1290
    return {'single_executions':len(rows),'registered_cases':27,'unresolved_cases':3,'matrix':matrix,
            'counts':dict(Counter(p for c in matrix for s in c.get('scenarios',[]) for p in s['probes'].values()))}


if __name__=='__main__':
    result={'diagnostic':verify_diagnostic(),'retained':verify_retained()}
    (ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'diagnostic':result['diagnostic'],'retained_counts':result['retained']['counts']},indent=2))
