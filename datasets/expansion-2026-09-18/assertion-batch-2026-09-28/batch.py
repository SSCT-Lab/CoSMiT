"""All-candidate assertion-interface diagnostic; not original-test intent gold.

Generated protocol assertions are deliberately identified as new, with upstream
anchors and excluded obligations. The legacy frozen expansion remains unchanged.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent
CASES=DATA/'candidates.json'
FROZEN=DATA/'runs/2026-09-20-dynamic-v3/inputs.freeze.json'


def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def anchor(file,cls,method):
    path=ROOT/'upstream'/file
    tree=ast.parse(path.read_text(encoding='utf-8'))
    c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    n=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==method)
    return {'file':'upstream/'+file,'class':cls,'method':method,'start':n.lineno,'end':n.end_lineno,
            'text':ast.get_source_segment(path.read_text(encoding='utf-8'),n),'sha256':sha(path)}


def build():
    assert not (ROOT/'manifest.json').exists(), 'Do not overwrite frozen build'
    rows=[]
    for c in load(CASES):
        cid=c['case_id'];f=c['family'];pt=c['source']['framework']=='pytorch'
        excluded=[]
        if pt:
            if f in ['add','subtract','multiply','divide','maximum','minimum','power','atan2']:
                a=anchor('pt_binary.py','TestBinaryUfuncs','assertEqualHelper')
                excluded=['full _test_reference_numerics input generator, promotion and scalar branches']
            elif f=='clip':
                a=anchor('pt_torch.py','TestDevicePrecision','test_clamp')
                excluded=['original random/noncontiguous input generation and complete broadcast paths']
            elif f in ['concat','stack']:
                a=anchor('pt_tensor.py','TestTensorCreation','test_stack' if f=='stack' else 'test_cat')
                excluded=['original per-input segment assertions, alias relations, device and dtype coverage']
            else:
                name={'reshape':'test_reshape','transpose':'test_transpose_vs_numpy','squeeze':'test_squeeze_view','expand_dims':'test_unsqueeze_view'}[f]
                cls='TestViewOps' if f in ['squeeze','expand_dims'] else 'TestOldViewOps'
                a=anchor('pt_view.py',cls,name)
                excluded=['view/storage aliasing, mutation propagation, contiguity and original input generation']
        else:
            if f in ['add','subtract','multiply','divide','maximum','minimum','power','atan2']:
                a=anchor('tf_binary.py','BinaryOpTest','_compareCpu');excluded=['NumPy/tensor mixed operands, Variable and gradient paths']
            elif f in ['squeeze','expand_dims']:
                a=anchor('tf_shape.py','ShapeOpsTest','_compareSqueeze' if f=='squeeze' else '_compareExpandDims')
            elif f=='transpose':
                a=anchor('tf_transpose.py','TransposeTest','_compareCpu');excluded=['gradient assertions and conjugate/complex paths']
            elif f=='clip': a=anchor('tf_clip.py','ClipTest','testClipByValue')
            elif f=='concat':
                a=anchor('tf_concat.py','ConcatOpTest','testHStack');excluded=['graph placeholders and individual segment assertions']
            elif f=='stack':
                a=anchor('tf_stack.py','StackOpTest','testSimple');excluded=['original dtype and axis enumeration']
            else:
                # Copy eligible pilot upstream source, not its generated results.
                pilot=DATA/'assertion-pilot-2026-09-28/upstream/reshape_op_test.py'
                dest=ROOT/'upstream/tf_reshape.py';dest.write_bytes(pilot.read_bytes())
                a=anchor('tf_reshape.py','ReshapeTest','_testReshape');excluded=['metadata/evaluation consistency assertion and graph/GPU variants']
        scope='shape-only' if cid=='E018' else 'value-and-shape'
        if scope=='shape-only': expr='self.assertEqual(expected.shape, actual.shape)'
        elif pt: expr='self.assertEqual(actual, expected)'
        elif f in ['reshape','transpose','squeeze','expand_dims','concat','stack']: expr='self.assertAllEqual(expected, actual)'
        else: expr='self.assertAllClose(expected, actual)'
        folder=ROOT/'registered-tests'/cid;folder.mkdir(parents=True)
        code='# New protocol assertion continuation; see registration.json.\ndef check(self, expected, actual):\n    '+expr+'\n'
        for side in ['source','target']: (folder/(side+'.py')).write_text(code,encoding='utf-8')
        for side in ['source','target']:
            src=DATA/c[side]['code_path'];assert sha(src)==c[side]['code_sha256']
            (folder/(side+'-function.py')).write_bytes(src.read_bytes())
        record={'case_id':cid,'family':f,'source_framework':c['source']['framework'],'scope':scope,
                'evidence_grade':'new-protocol-assertion-with-upstream-anchor; not original full test migration',
                'source_anchor':a,'assertion_expression':expr,'source_target_assertions_identical_by_construction':True,
                'excluded_obligations':excluded,'input_origin':'all 64 frozen expansion inputs; not upstream original test setup',
                'independent_human_review':False,'authentic_full_test_pair_available':False,
                'candidate_origin':'unchanged published counterpart in new generated assertion wrapper',
                'scope_gap':'all full-source-intent conclusions pending; excluded obligations are not assumed preserved'}
        save(folder/'registration.json',record);rows.append(record)
    save(ROOT/'intake.json',rows)
    freeze={'input_manifest_sha256':sha(FROZEN),'cases_sha256':sha(CASES),'candidate_count':30,'inputs':1920,'repeats':3,
            'modes':['original','observe','reinject','wrong-shape','wrong-value'],
            'sensitivity_gate':'both native source and target pass frozen reference and generated assertions in 3 stable runs',
            'wrong_shape':'prepend dimension 1 to the frozen expected array',
            'wrong_value':'expected + (abs(expected)*0.2 + 10) rounded to original dtype',
            'witness_rule':'invalid for registered scope, same delivered observation, source rejects, target accepts, baseline and transparency qualified',
            'prohibited_claims':['accuracy on authentic migrated tests','new intent-loss bug from cloned oracle success','full source intent retained'],
            'files':{p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and 'dependencies' not in p.parts and '__pycache__' not in p.parts}}
    save(ROOT/'manifest.json',freeze)
    print('Frozen 30 registrations, unchanged counterpart functions, and protocol assertion continuations')


def worker(output):
    os.environ.update(CUDA_VISIBLE_DEVICES='-1',TF_NUM_INTRAOP_THREADS='1',TF_NUM_INTEROP_THREADS='1',OMP_NUM_THREADS='1')
    sys.path.insert(0,str(ROOT/'dependencies'))
    import numpy as np
    import tensorflow as tf
    import torch
    from tensorflow.python.platform.test import TestCase as TFCase
    from torch.testing._internal.common_utils import TestCase as PTCase
    torch.set_num_threads(1)
    for f,h in load(ROOT/'manifest.json')['files'].items(): assert sha(ROOT/f)==h,f
    assert sha(FROZEN)==load(ROOT/'manifest.json')['input_manifest_sha256']
    cases=load(CASES);probes=load(FROZEN);registry={r['case_id']:r for r in load(ROOT/'intake.json')}
    testers={'pytorch':PTCase(),'tensorflow':TFCase()}
    def arr(v): return np.asarray(v['values'],dtype=v['dtype'])
    def tensor(v,fw):
        if v['kind']=='literal': return v['value']
        if v['kind']=='tensor-list': return [tensor(x,fw) for x in v['items']]
        return torch.tensor(arr(v)) if fw=='pytorch' else tf.constant(arr(v))
    def observation(a):return {'shape':list(a.shape),'dtype':str(a.dtype),'values':a.tolist()}
    def check_reference(a,p):
        e=arr(p['expected']);return a.shape==e.shape and a.dtype==e.dtype and bool(np.allclose(a,e,**p['tolerance']))
    rows=[];intakes=[]
    for c in cases:
        cid=c['case_id'];registration=registry[cid];folder=ROOT/'registered-tests'/cid
        functions={};checks={}
        for side in ['source','target']:
            env={'torch':torch,'tf':tf,'np':np}
            exec(compile((folder/(side+'-function.py')).read_text(),str(folder/(side+'-function.py')),'exec'),env)
            functions[side]=env[c[side]['entry']]
            scope={};exec(compile((folder/(side+'.py')).read_text(),str(folder/(side+'.py')),'exec'),scope);checks[side]=scope['check']
        tester=testers[c['source']['framework']]
        def run_one(p,side,mode,repeat):
            row={'case_id':cid,'input_index':p['input_index'],'side':side,'mode':mode,'repeat':repeat}
            try:
                fw=c[side]['framework'];result=functions[side](**{k:tensor(v,fw) for k,v in p['arguments'].items()})
                a=result.detach().cpu().numpy() if fw=='pytorch' else result.numpy()
                a=np.asarray(a);e=arr(p['expected']);row['native']=observation(a);row['reference_ok']=check_reference(a,p)
                delivered=a
                if mode=='reinject': delivered=a.copy()
                elif mode=='wrong-shape': delivered=e.reshape((1,)+e.shape)
                elif mode=='wrong-value': delivered=(e+(np.abs(e)*.2+10)).astype(e.dtype)
                row['delivered']=observation(delivered)
                row['valid_for_scope']=bool(delivered.shape==e.shape and (registration['scope']=='shape-only' or np.allclose(delivered,e,**p['tolerance'])))
                try:
                    checks[side](tester,e,delivered)
                    row['assertion']='accepted'
                except AssertionError as exc:
                    row['assertion']='rejected';row['assertion_error']=str(exc)[:1800]
                    row['assertion_frames']=[{'file':f.filename,'line':f.lineno,'name':f.name} for f in traceback.extract_tb(exc.__traceback__)]
                row['status']='executed'
            except Exception as exc:
                row['status']='execution-error';row['error']=type(exc).__name__;row['message']=str(exc)
            rows.append(row);return row
        def stable(rs):
            keys=['status','native','delivered','reference_ok','assertion','error','message']
            return all([r.get(k) for k in keys]==[rs[0].get(k) for k in keys] for r in rs)
        for p in [p for p in probes if p['case_id']==cid]:
            sr=[run_one(p,'source','original',i) for i in range(3)]
            sq=stable(sr) and all(r.get('reference_ok') and r.get('assertion')=='accepted' for r in sr)
            gate={'case_id':cid,'input_index':p['input_index'],'source_qualified':sq,'target_qualified':False,'probe_gate':False}
            if sq:
                tr=[run_one(p,'target','original',i) for i in range(3)]
                tq=stable(tr) and all(r.get('reference_ok') and r.get('assertion')=='accepted' for r in tr)
                gate['target_qualified']=tq
                if tq:
                    transparent=True
                    for side,baseline in [('source',sr[0]),('target',tr[0])]:
                        for mode in ['observe','reinject']:
                            rr=[run_one(p,side,mode,i) for i in range(3)]
                            transparent &= stable(rr) and all(r.get('native')==baseline.get('native') and r.get('delivered')==baseline.get('native') and r.get('assertion')=='accepted' for r in rr)
                    gate['probe_gate']=bool(transparent)
                    if transparent:
                        for mode in ['wrong-shape','wrong-value']:
                            for side in ['source','target']:
                                for i in range(3):run_one(p,side,mode,i)
            intakes.append(gate)
        print(cid,flush=True)
    save(output,{'versions':{'tensorflow':tf.__version__,'pytorch':torch.__version__,'numpy':np.__version__,'python':sys.version},'gates':intakes,'records':rows})


def run(python,out):
    out.mkdir(parents=True,exist_ok=False)
    cmd=[python,str(Path(__file__).resolve()),'worker','--output',str((out/'executions.json').resolve())]
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
    save(out/'process.json',{'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    if proc.returncode:raise RuntimeError('worker failure; see process.json')
    data=load(out/'executions.json');records=data['records'];gates=data['gates'];results=[]
    for c in load(CASES):
        cid=c['case_id'];gg=[g for g in gates if g['case_id']==cid];rr=[r for r in records if r['case_id']==cid]
        counts={}
        for mode in ['wrong-shape','wrong-value']:
            sample=[r for r in rr if r['mode']==mode]
            counts[mode]={k:sum(r.get('assertion')==k for r in sample) for k in ['accepted','rejected']}
        results.append({'case_id':cid,'family':c['family'],'source_qualified_inputs':sum(g['source_qualified'] for g in gg),
                        'target_qualified_inputs':sum(g['target_qualified'] for g in gg),'sensitivity_inputs':sum(g['probe_gate'] for g in gg),
                        'single_executions':len(rr),'probe_assertions':counts,'full_original_intent_status':'undetermined','human_review':'pending'})
    save(out/'case-results.json',results)
    save(out/'summary.json',{'candidates':30,'inputs':len(gates),'single_executions':len(records),
                            'source_qualified_inputs':sum(g['source_qualified'] for g in gates),
                            'sensitivity_inputs':sum(g['probe_gate'] for g in gates),
                            'full_original_intent_status':'undetermined for all 30; diagnostic protocol wrappers do not supply original migrated assertions',
                            'model_calls':0,'versions':data['versions']})
    save(out/'SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print((out/'summary.json').read_text())


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','worker','run']);p.add_argument('--python');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='build':build()
    elif a.action=='worker':worker(a.output)
    else:run(a.python,a.output)
