"""Frozen-input dynamic expansion campaign, isolated framework workers, no LLM."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tensor(a):
    return {"kind": "tensor", "dtype": str(a.dtype), "values": a.tolist()}


def literal(v):
    return {"kind": "literal", "value": v}


def generate(case):
    import numpy as np
    f, pt = case["family"], case["source"]["framework"] == "pytorch"
    records = []
    for dtype in ("float32", "float64"):
        for s in range(4):
            for v in range(8):
                rng = np.random.default_rng(20260918 + len(records))
                def a(shape, shift=0):
                    n = math.prod(shape)
                    values = (np.zeros(n) if v == 0 else np.ones(n) if v == 1 else -np.ones(n) if v == 2
                              else (np.arange(n)%7-3)/2+.25 if v == 3 else rng.uniform(-3,3,n))
                    return np.asarray(values+shift, dtype=dtype).reshape(shape)
                if f in {"add","subtract","multiply","divide","maximum","minimum","power","atan2"}:
                    xs,ys = [([2,3],[2,3]),([],[2,3]),([2,1],[1,3]),([1,2,1],[3,1,4])][s]
                    x,y = a(xs), a(ys,.5)
                    if f == "divide": y = np.where(y<0,-1,1)*np.maximum(np.abs(y),.25)
                    if f == "power": x,y = np.abs(x)+.25, np.clip(y,-3,3)
                    if f == "atan2": y = np.where(y==0,.5,y)
                    args = [tensor(x),tensor(y.astype(dtype))]
                    bx,by = np.broadcast_arrays(x,y)
                    ops = {"add":lambda x,y:x+y,"subtract":lambda x,y:x-y,"multiply":lambda x,y:x*y,
                           "divide":lambda x,y:x/y,"maximum":max,"minimum":min,"power":math.pow,"atan2":math.atan2}
                    expected = np.asarray([ops[f](float(x),float(y)) for x,y in zip(bx.flat,by.flat)],dtype=dtype).reshape(bx.shape)
                elif f == "reshape":
                    shape,new = [([2,3],[3,2]),([2,3,4],[4,6]),([2,3],[-1]),([2,3,4],[2,-1,2])][s]
                    x=a(shape);args=[tensor(x),literal(new)];expected=x.reshape(new)
                elif f == "transpose":
                    shape = [2,3] if s==0 else [2,3,4]
                    x=a(shape)
                    if pt:
                        d0,d1=[(0,1),(0,2),(-1,-2),(1,1)][s]
                        perm=list(range(x.ndim));perm[d0],perm[d1]=perm[d1],perm[d0]
                        args=[tensor(x),literal(d0),literal(d1)]
                    else:
                        perm=[[1,0],[1,2,0],[2,0,1],None][s]
                        args=[tensor(x),literal(perm),literal(False)]
                    expected=np.transpose(x,perm)
                elif f == "squeeze":
                    shape,axis=[([1,2,3],0),([2,1,3],1),([1,2,1,3],None),([2,3],1) if pt else ([1,2,1,3],[0,2])][s]
                    x=a(shape);args=[tensor(x),literal(axis)]
                    expected=x if pt and axis is not None and x.shape[axis]!=1 else np.squeeze(x,axis=tuple(axis) if isinstance(axis,list) else axis)
                elif f == "expand_dims":
                    shape,axis=[([],0),([3],-1),([2,3],1),([2,3,4],-2)][s]
                    x=a(shape);args=[tensor(x),literal(axis)];expected=np.expand_dims(x,axis)
                elif f in {"concat","stack"}:
                    if f=="concat": shapes,axis=[([[1,3],[1,3]],0),([[2,1],[2,2]],1),([[1,2,3],[2,2,3],[3,2,3]],0),([[2,1],[2,2]],-1)][s]
                    else: shapes,axis=[([[],[]],0),([[3],[3]],0),([[2,3]]*3,1),([[2,3,2]]*3,-1)][s]
                    xs=[a(sh,i*.25) for i,sh in enumerate(shapes)]
                    args=[{"kind":"tensor-list","items":[tensor(x) for x in xs]},literal(axis)]
                    expected=np.concatenate(xs,axis=axis) if f=="concat" else np.stack(xs,axis=axis)
                elif f == "clip":
                    shape=[[],[2,3],[1,2,3],[2,3]][s];x=a(shape)
                    lo,hi=(-1.,1.) if s!=2 else (.5,.5)
                    if s==3 and not pt: lo,hi=float(x.min()),float(x.max())
                    if s==3 and pt:
                        if v%2: lo=None
                        else: hi=None
                    args=[tensor(x),literal(None) if lo is None else tensor(np.asarray(lo,dtype=dtype)),literal(None) if hi is None else tensor(np.asarray(hi,dtype=dtype))]
                    expected=np.asarray([min(max(float(z),lo if lo is not None else -math.inf),hi if hi is not None else math.inf) for z in x.flat],dtype=dtype).reshape(x.shape)
                else: raise ValueError(f)
                assert len(args)==len(case["argument_names"])
                records.append({"case_id":case["case_id"],"input_index":len(records),"stratum":s,"pattern":v,
                                "arguments":dict(zip(case["argument_names"],args)),"expected":tensor(expected),
                                "tolerance":{"atol":0.,"rtol":0.} if f in {"reshape","transpose","squeeze","expand_dims","concat","stack"} else
                                {"atol":1e-6 if dtype=="float32" else 1e-12,"rtol":1e-5 if dtype=="float32" else 1e-12}})
    assert len(records)==64
    assert len({json.dumps(r["arguments"],sort_keys=True) for r in records})==64,case["case_id"]
    return records


def signature(r):
    result={k:r.get(k) for k in ("status","value","dtype","shape","error","message")}
    # Python names the callee in this argument-unpacking error. A spy changes
    # that name, but not the error class or the rejected None operand.
    if result["message"] and " argument after *" in result["message"]:
        result["message"]="argument after *"+result["message"].split(" argument after *",1)[1]
    return result


def worker(args):
    import numpy as np
    fw=__import__("torch" if args.framework=="pytorch" else "tensorflow")
    if args.framework=="pytorch": fw.set_num_threads(1)
    else:
        fw.config.threading.set_inter_op_parallelism_threads(1);fw.config.threading.set_intra_op_parallelism_threads(1)
    cases={c["case_id"]:c for c in read(args.dataset/"candidates.json")}
    def convert(v):
        if v["kind"]=="literal":return v["value"]
        if v["kind"]=="tensor-list":return [convert(x) for x in v["items"]]
        a=np.asarray(v["values"],dtype=v["dtype"])
        return fw.tensor(a) if args.framework=="pytorch" else fw.constant(a)
    rows=[]
    for job in read(args.jobs):
        c=cases[job["case_id"]];spec=c[job["side"]];path=args.dataset/spec["code_path"]
        assert sha(path)==spec["code_sha256"]
        env={"np":np,"torch" if args.framework=="pytorch" else "tf":fw}
        calls,patches=[],[]
        try:
            if job["instrument"]:
                apis=[]
                for name in spec["syntactic_calls"]:
                    if name.startswith(("torch.","tf.")):apis.append(name)
                    elif "." in name and args.framework=="pytorch":apis.append("torch.Tensor."+name.split(".")[-1])
                for api in sorted(set(apis)):
                    owner=fw
                    for part in api.split(".")[1:-1]:owner=getattr(owner,part)
                    attr=api.split(".")[-1];original=getattr(owner,attr)
                    def wrap(*a,_api=api,_fn=original,**kw):
                        calls.append(_api);return _fn(*a,**kw)
                    setattr(owner,attr,wrap);patches.append((owner,attr,original))
            exec(compile(path.read_text(encoding="utf-8"),str(path),"exec"),env)
            result=env[spec["entry"]](**{k:convert(v) for k,v in job["arguments"].items()})
            a=result.detach().numpy() if args.framework=="pytorch" else result.numpy()
            r={"status":"ok","value":a.tolist(),"dtype":str(a.dtype),"shape":list(a.shape)}
            if not np.isfinite(a).all():r={"status":"nonfinite-output"}
        except Exception as e:
            r={"status":"error","error":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
        finally:
            for owner,attr,original in reversed(patches):setattr(owner,attr,original)
        rows.append({**{k:job[k] for k in ("case_id","input_index","side","repeat","instrument")},**r,"calls":calls})
    specifications={}
    for c in cases.values():
        if c["source"]["framework"]!=args.framework:continue
        api=c["source_api"];obj=fw
        for part in api.split(".")[1:]:obj=getattr(obj,part)
        specifications[api]=obj.__doc__
    if args.framework=="pytorch":specifications["torch.clamp"]=fw.clamp.__doc__
    save(args.output,{"framework":args.framework,"version":fw.__version__,"numpy":np.__version__,"python":sys.version,"source_specifications":specifications,"records":rows})


def run(args):
    import numpy as np
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    cases=read(args.dataset/"candidates.json")
    for rel,h in read(args.dataset/"SHA256.json").items():
        assert sha(args.dataset/rel)==h,rel
    probes=[p for c in cases for p in generate(c)]
    save(out/"inputs.freeze.json",probes)
    save(out/"protocol.freeze.json",{"candidates":30,"inputs":1920,"repetitions":3,"model_calls":0,
        "selection_sha256":sha(args.dataset/"candidates.json"),"inputs_sha256":sha(out/"inputs.freeze.json"),
        "script_sha256":sha(Path(__file__)),"scope":"source-qualified finite domain; source failures retained; no full-API equivalence",
        "source_first":True,"source_reference":"Python scalar arithmetic / NumPy shape index operations; no target observations",
        "domain_clarification":"rank up to 4 for the explicitly planned squeeze [1,2,1,3] stratum; otherwise rank <=3; no gradients/nonfinite/sparse/mixed dtype",
        "target_exceptions":"stable exceptions are candidate discrepancy evidence, infrastructure errors remain undetermined"})
    cmap={c["case_id"]:c for c in cases}
    def batch(name,jobs):
        result=[]
        for fw,python in (("pytorch",args.pytorch_python),("tensorflow",args.tensorflow_python)):
            subset=[j for j in jobs if cmap[j["case_id"]][j["side"]]["framework"]==fw]
            if not subset:continue
            jobfile=out/(name+"-"+fw+"-jobs.json");output=out/(name+"-"+fw+".json");save(jobfile,subset)
            cmd=[str(python),str(Path(__file__).resolve()),"--worker","--framework",fw,"--dataset",str(args.dataset.resolve()),"--jobs",str(jobfile.resolve()),"--output",str(output.resolve())]
            proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=180,
                                env=dict(os.environ,CUDA_VISIBLE_DEVICES="-1",TF_CPP_MIN_LOG_LEVEL="3",OMP_NUM_THREADS="1"))
            save(out/(name+"-"+fw+"-process.json"),{"command":cmd,"returncode":proc.returncode,"stderr":proc.stderr})
            assert proc.returncode==0,proc.stderr
            records=read(output)["records"];assert len(records)==len(subset)
            result.extend(records)
        print(name,len(result),"single executions",flush=True)
        return result
    def jobs(side,selected,instrument=True):
        return [{**{k:p[k] for k in ("case_id","input_index","arguments")},"side":side,"repeat":r,"instrument":instrument} for p in selected for r in range(3)]
    def idx(rows):return {(r["case_id"],r["input_index"],r["repeat"]):r for r in rows}
    def stable(rs):return all(signature(r)==signature(rs[0]) for r in rs)
    def check(r,p):
        if r["status"]!="ok":return False
        expected=np.asarray(p["expected"]["values"],dtype=p["expected"]["dtype"])
        actual=np.asarray(r["value"])
        return r["shape"]==list(expected.shape) and r["dtype"]==str(expected.dtype) and bool(np.allclose(actual,expected,**p["tolerance"]))
    source=batch("source",jobs("source",probes));si=idx(source)
    valid=[];qual=[]
    for p in probes:
        rs=[si[p["case_id"],p["input_index"],i] for i in range(3)]
        ok=stable(rs) and all(check(r,p) for r in rs)
        qual.append({"case_id":p["case_id"],"input_index":p["input_index"],"qualified":ok,"source_status":rs[0]["status"],"source_error":rs[0].get("error")})
        if ok:valid.append(p)
    save(out/"source-qualification.json",qual)
    target=batch("target",jobs("target",valid));ti=idx(target)
    # Uninstrumented smoke observations on every candidate's first qualified input.
    first=[]
    for c in cases:
        ps=[p for p in valid if p["case_id"]==c["case_id"]]
        if ps:first.append(ps[0])
    raw=batch("transparency",jobs("source",first,False)+jobs("target",first,False))
    assert all(signature(r)==signature((si if r["side"]=="source" else ti)[r["case_id"],r["input_index"],r["repeat"]]) for r in raw)
    witnesses=[];outcomes=[]
    for p in valid:
        key=p["case_id"],p["input_index"];ss=si[*key,0];rs=[ti[*key,i] for i in range(3)];t=rs[0]
        status="undetermined"
        if stable(rs):
            if t["status"]=="error":status="target-exception"
            elif t["status"]=="ok":
                same_shape=ss["shape"]==t["shape"];same_dtype=ss["dtype"]==t["dtype"]
                # Compare structure as well as values; no broadcasting in oracle.
                value=same_shape and bool(np.allclose(t["value"],ss["value"],**p["tolerance"]))
                status="behavior-difference" if not (same_shape and same_dtype and value) else "supported" if t["calls"] else "unbound"
        dllens=None
        if t["status"]==ss["status"]=="ok":
            a,b=[np.asarray(r["value"],dtype=r["dtype"]).squeeze().flatten() for r in (ss,t)]
            dllens=bool(a.size==b.size and np.allclose(a,b,atol=.1,rtol=1e-5,equal_nan=True))
        outcomes.append({"case_id":key[0],"input_index":key[1],"status":status,"dllens_dense_agrees":dllens})
        if status in {"target-exception","behavior-difference"}:witnesses.append(p)
    if witnesses:
        replay=batch("witness-replay",jobs("source",witnesses,False)+jobs("target",witnesses,False))
        assert all(signature(r)==signature((si if r["side"]=="source" else ti)[r["case_id"],r["input_index"],r["repeat"]]) for r in replay)
    results=[]
    for c in cases:
        cid=c["case_id"];oset=[r for r in outcomes if r["case_id"]==cid];counts=Counter(r["status"] for r in oset)
        status="discrepancy-replayed" if counts["target-exception"]+counts["behavior-difference"] else "undetermined-binding" if counts["unbound"] else "supported-on-qualified-inputs" if len(oset) and counts["supported"]==len(oset) else "undetermined"
        results.append({"case_id":cid,"family":c["family"],"status":status,"qualified_inputs":len(oset),"source_unqualified_inputs":64-len(oset),"outcomes":dict(counts)})
    save(out/"input-outcomes.json",outcomes);save(out/"case-results.json",results)
    save(out/"counterexamples.json",[{"case_id":p["case_id"],"input_index":p["input_index"],"arguments":p["arguments"],
        "source":si[p["case_id"],p["input_index"],0],"target":ti[p["case_id"],p["input_index"],0],"raw_replay_matches":True,"minimality":"not minimized"} for p in witnesses])
    summary={"candidates":30,"source_inputs":len(probes),"qualified_inputs":len(valid),"source_unqualified_inputs":len(probes)-len(valid),
             "main_source_executions":len(source),"main_target_executions":len(target),"completed_pairs":len(target),
             "transparency_single_executions":len(raw),"witness_replay_single_executions":len(witnesses)*6,
             "witness_inputs":len(witnesses),"case_statuses":dict(Counter(r["status"] for r in results)),"model_calls":0}
    save(out/"summary.json",summary)
    save(out/"SHA256.json",{p.relative_to(out).as_posix():sha(p) for p in out.rglob("*") if p.is_file()})
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--dataset",type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--pytorch-python",type=Path);p.add_argument("--tensorflow-python",type=Path);p.add_argument("--worker",action="store_true");p.add_argument("--framework");p.add_argument("--jobs",type=Path)
    args=p.parse_args()
    worker(args) if args.worker else run(args)
