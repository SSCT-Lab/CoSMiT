#!/usr/bin/env python3
"""Validate the frozen CoSMiT pilot sampling and blind-review contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "sampling-manifest.yaml"
ASSIGNMENT = ROOT / "review" / "assignment.yaml"
PROPERTIES = ROOT / "properties.yaml"
SEED_PROPERTIES = ROOT / "properties-seed-v0.2.yaml"
CASES = ROOT / "candidate-cases.yaml"
SEED_CASES = ROOT / "candidate-cases-seed-v0.2.yaml"
EVIDENCE = ROOT / "evidence.yaml"
FEASIBILITY_EVIDENCE = ROOT.parent / "feasibility" / "evidence.yaml"
TRACE = ROOT / "sampling-trace.json"
FEASIBILITY_TRACE = ROOT.parent / "feasibility" / "dynamic-trace.json"


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def main() -> None:
    manifest = load_yaml(MANIFEST)
    assignment = load_yaml(ASSIGNMENT)
    properties = load_yaml(PROPERTIES)
    seed_properties = load_yaml(SEED_PROPERTIES)
    cases = load_yaml(CASES)
    seed_cases = load_yaml(SEED_CASES)
    evidence = load_yaml(EVIDENCE)
    feasibility_evidence = load_yaml(FEASIBILITY_EVIDENCE)
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    feasibility_trace = json.loads(FEASIBILITY_TRACE.read_text(encoding="utf-8"))
    groups = manifest["groups"]
    slots = [slot for group in groups for slot in group["slots"]]

    assert len(groups) == manifest["design"]["api_groups"] == 15
    assert sum(group["split"] == "development" for group in groups) == 12
    assert sum(group["split"] == "evaluation-holdout" for group in groups) == 3
    assert all(len(group["slots"]) == 3 for group in groups)
    assert len(slots) == manifest["design"]["atomic_property_slots"] == 45

    group_ids = [group["group_id"] for group in groups]
    property_ids = [slot["property_id"] for slot in slots]
    assert len(group_ids) == len(set(group_ids)), "duplicate group_id"
    assert len(property_ids) == len(set(property_ids)), "duplicate property_id"

    sealed = [slot for slot in slots if slot.get("annotation_status") == "holdout-sealed"]
    assert len(sealed) == manifest["design"]["sealed_holdout_slots"] == 9
    assert all(slot["focus"] == slot["primary_oracle"] == "sealed" for slot in sealed)
    for group in groups:
        if group["split"] == "evaluation-holdout":
            assert all(slot in sealed for slot in group["slots"])

    disallowed_compound_oracles = {
        "shape-and-value",
        "exact-value-and-dtype",
        "exact-shape-and-value",
        "value-or-exception",
        "loss-or-exception",
        "gradient-value-or-availability",
        "nan-or-zero",
        "probability-value-and-axis-sum",
        "value-and-output-dtype",
    }
    assert not {
        slot["primary_oracle"] for slot in slots if slot not in sealed
    } & disallowed_compound_oracles, "development slots must use one primary oracle"

    development_dimensions = {
        slot["dimension"]
        for group in groups
        if group["split"] == "development"
        for slot in group["slots"]
    }
    assert set(manifest["required_semantic_dimensions"]) <= development_dimensions

    base_ids = assignment["base_property_ids"]
    assert len(base_ids) == manifest["design"]["independent_review_base_sample"] == 12
    assert len(base_ids) == len(set(base_ids))
    assert set(base_ids) <= set(property_ids)
    selected_groups = {
        group["group_id"]
        for group in groups
        if any(slot["property_id"] in base_ids for slot in group["slots"])
    }
    assert len(selected_groups) == 12
    assert all(
        any(slot["property_id"] in base_ids for slot in group["slots"])
        for group in groups
        if group["split"] == "development"
    )

    fraction = len(base_ids) / len(property_ids)
    assert 0.20 <= fraction <= 0.30
    assert abs(fraction - assignment["base_sample_fraction"]) < 0.001

    forbidden = set(assignment["forbidden_fields"])
    required_forbidden = {
        "annotation",
        "gold_adapter",
        "gold_counterexamples",
        "cosmit_output",
        "probe_trace",
        "suggested_condition",
    }
    assert required_forbidden <= forbidden

    property_records = seed_properties["records"] + properties["records"]
    annotated_property_ids = [record["property_id"] for record in property_records]
    assert len(annotated_property_ids) == len(set(annotated_property_ids))
    assert set(annotated_property_ids) <= set(property_ids)
    slot_by_id = {slot["property_id"]: slot for slot in slots}
    for record in property_records:
        assert record["property"]["oracle"]["type"] == slot_by_id[record["property_id"]][
            "primary_oracle"
        ]

    evidence_ids = {
        record["evidence_id"]
        for ledger in (evidence, feasibility_evidence)
        for record in ledger["records"]
    }
    for record in property_records:
        referenced = set(record["property"]["provenance"])
        assert referenced <= evidence_ids

    allowed_relations = {
        "identity-transport",
        "adapted-transport",
        "divergent-by-design",
        "library-unsupported",
        "relation-undetermined",
    }
    allowed_states = {"supported-within-scope", "refuted", "undetermined"}
    case_ids = []
    case_records = seed_cases["records"] + cases["records"]
    for record in case_records:
        case_ids.append(record["case_id"])
        assert record["property_id"] in annotated_property_ids
        assert record["annotation"]["semantic_relation"] in allowed_relations
        assert record["annotation"]["evidence_state"] in allowed_states
        if record["candidate"]["origin"] == "researcher-mutant":
            assert record["annotation"]["evidence_state"] == "refuted"
            assert record.get("counterexample")
        if record["candidate"]["origin"] == "evidence-derived-reference":
            assert record["annotation"]["evidence_state"] == "supported-within-scope"
    assert len(case_ids) == len(set(case_ids))
    cases_by_property: dict[str, list[dict]] = {}
    for record in case_records:
        cases_by_property.setdefault(record["property_id"], []).append(record)
    assert set(cases_by_property) == set(annotated_property_ids)
    for property_id, property_cases in cases_by_property.items():
        assert len(property_cases) == 2, f"{property_id} must have one reference and one mutant"
        origins = {record["candidate"]["origin"] for record in property_cases}
        assert origins == {"evidence-derived-reference", "researcher-mutant"}

    trace_ids = {probe["property_id"] for probe in trace["probes"]}
    legacy_mapping = properties["legacy_seed_mapping"]["mappings"]
    legacy_trace_ids = {
        legacy_mapping[legacy_id] for legacy_id in feasibility_trace["records"]
    }
    assert set(annotated_property_ids) <= trace_ids | legacy_trace_ids
    assert all(not probe["naive_preserves"] for probe in trace["probes"])
    assert all(probe["adapted_preserves"] for probe in trace["probes"])

    digest_input = re.sub(
        r"manifest_sha256: [0-9a-z-]+",
        "manifest_sha256: <normalized>",
        MANIFEST.read_text(encoding="utf-8"),
    )
    digest = hashlib.sha256(digest_input.encode()).hexdigest()
    print(f"groups={len(groups)} development=12 holdout=3")
    print(f"slots={len(slots)} concrete=36 sealed=9")
    print(f"review_base={len(base_ids)}/{len(property_ids)} ({fraction:.1%})")
    print(f"pilot_properties={len(property_records)} candidate_cases={len(case_ids)}")
    print(f"manifest_sha256={digest}")
    print("pilot validation: PASS")


if __name__ == "__main__":
    main()
