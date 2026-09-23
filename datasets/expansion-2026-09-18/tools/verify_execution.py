"""Read-only verification of identities, gates, observations and replay evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def sig(r):
    message=r.get("message")
    if message and " argument after *" in message:
        message=message[message.index(" argument after *")+1:]
    return [r.get(k) for k in ("status","value","shape","dtype","error")]+[message]


def verify(root,dataset):
    hashes=read(root/"SHA256.json")
    for rel,h in hashes.items():
        assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==h,rel
    inputs=read(root/"inputs.freeze.json")
    probes={(p["case_id"],p["input_index"]):p for p in inputs}
    assert len(probes)==len(inputs)==1920
    assert Counter(p["case_id"] for p in inputs)==Counter({f"E{i:03d}":64 for i in range(1,31)})
    for cid in {p["case_id"] for p in inputs}:
        assert len({json.dumps(p["arguments"],sort_keys=True) for p in inputs if p["case_id"]==cid})==64
    def domain(v):
        if v["kind"]=="literal":return
        if v["kind"]=="tensor-list":
            for x in v["items"]:domain(x)
            return
        a=np.asarray(v["values"],dtype=v["dtype"])
        assert v["dtype"] in {"float32","float64"} and a.ndim<=4 and a.size<=256 and np.isfinite(a).all()
    for p in inputs:
        for v in p["arguments"].values():domain(v)
    allrows={}
    versions={}
    for phase in ("source","target","transparency","witness-replay"):
        collected=[]
        for fw in ("pytorch","tensorflow"):
            path=root/f"{phase}-{fw}.json"
            if not path.exists():continue
            data=read(path);rows=data["records"];jobs=read(root/f"{phase}-{fw}-jobs.json")
            key=lambda x:(x["case_id"],x["input_index"],x["side"],x["repeat"],x["instrument"])
            assert len(rows)==len(jobs)==len({key(r) for r in rows})
            assert {key(r) for r in rows}=={key(j) for j in jobs}
            for j in jobs:assert j["arguments"]==probes[j["case_id"],j["input_index"]]["arguments"]
            collected+=rows;versions[fw]={k:data[k] for k in ("version","numpy","python")}
        allrows[phase]=collected
    sources={(r["case_id"],r["input_index"],r["repeat"]):r for r in allrows["source"]}
    targets={(r["case_id"],r["input_index"],r["repeat"]):r for r in allrows["target"]}
    qualified=set()
    for key,p in probes.items():
        rs=[sources[*key,i] for i in range(3)]
        assert sig(rs[0])==sig(rs[1])==sig(rs[2])
        exp=np.asarray(p["expected"]["values"],dtype=p["expected"]["dtype"])
        r=rs[0]
        ok=r["status"]=="ok" and r["shape"]==list(exp.shape) and r["dtype"]==str(exp.dtype) and np.allclose(r["value"],exp,**p["tolerance"])
        if ok:qualified.add(key)
    assert qualified=={(r["case_id"],r["input_index"]) for r in read(root/"source-qualification.json") if r["qualified"]}
    assert set(targets)=={(*key,i) for key in qualified for i in range(3)}
    computed={}
    for key in qualified:
        p=probes[key];s=sources[*key,0];rs=[targets[*key,i] for i in range(3)];t=rs[0]
        if not sig(rs[0])==sig(rs[1])==sig(rs[2]):status="undetermined"
        elif t["status"]=="error":status="target-exception"
        elif t["status"]=="ok":
            agrees=s["shape"]==t["shape"] and s["dtype"]==t["dtype"] and np.allclose(t["value"],s["value"],**p["tolerance"])
            status="behavior-difference" if not agrees else "supported" if t["calls"] else "unbound"
        else:status="undetermined"
        dllens=None
        if t["status"]==s["status"]=="ok":
            a,b=[np.asarray(r["value"],dtype=r["dtype"]).flatten() for r in (s,t)]
            dllens=bool(a.size==b.size and np.allclose(a,b,atol=.1,rtol=1e-5,equal_nan=True))
        computed[key]=(status,dllens)
    for r in read(root/"input-outcomes.json"):
        assert computed[r["case_id"],r["input_index"]]==(r["status"],r["dllens_dense_agrees"])
    witnesses={(w["case_id"],w["input_index"]):w for w in read(root/"counterexamples.json")}
    assert set(witnesses)=={key for key,(status,_) in computed.items() if status in {"target-exception","behavior-difference"}}
    assert len(allrows["witness-replay"])==6*len(witnesses)
    for phase in ("transparency","witness-replay"):
        for r in allrows[phase]:
            index=sources if r["side"]=="source" else targets
            assert not r["instrument"] and sig(r)==sig(index[r["case_id"],r["input_index"],r["repeat"]])
    for c in read(dataset/"candidates.json"):
        for side in ("source","target"):
            assert hashlib.sha256((dataset/c[side]["code_path"]).read_bytes()).hexdigest()==c[side]["code_sha256"]
    for r in read(root/"case-results.json"):
        counts=Counter(status for (cid,_),(status,_) in computed.items() if cid==r["case_id"])
        assert dict(counts)==r["outcomes"] and sum(counts.values())==r["qualified_inputs"]
    return {"integrity":"passed","job_identity_and_source_gate":"passed","repeat_stability_and_uninstrumented_replay":"passed",
            "input_outcomes_recomputed":"passed","cases":30,"qualified_inputs":len(qualified),"witness_inputs":len(witnesses),
            "dense_dllens_on_behavior_witnesses":dict(Counter(str(comp) for status,comp in computed.values() if status=="behavior-difference")),
            "versions":versions,"independent_human_gold":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("run",type=Path);p.add_argument("--dataset",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    print(json.dumps(verify(a.run,a.dataset),indent=2))
