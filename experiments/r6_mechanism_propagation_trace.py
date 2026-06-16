from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION = (
    "r6-mechanism-propagation-trace-v1"
)
DEFAULT_SOURCE_KEYS = [
    "htops_cost_pressure",
    "anes_health_heldout",
    "anes_climate_heldout",
]


def build_r6_mechanism_propagation_trace(
    artifact_id: str,
    run_id: str,
    public_outcome_proxies: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if public_outcome_proxies is None:
        proxies = _default_public_outcome_proxies(
            artifact_id=artifact_id,
            run_id=run_id,
        )
    else:
        proxies = public_outcome_proxies
    case_traces = [_build_case_trace(proxy) for proxy in proxies]
    dynamic_path_count = sum(len(trace["dynamic_paths"]) for trace in case_traces)
    report = {
        "schema_version": R6_MECHANISM_PROPAGATION_TRACE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "mechanism_propagation_trace_ready",
        "trace_summary": {
            "case_count": len(case_traces),
            "trace_round_count": 3,
            "exposure_graph_count": len(case_traces),
            "dynamic_path_count": dynamic_path_count,
            "distinct_from_static_prior_path_count": sum(
                1
                for trace in case_traces
                if any(
                    not path["static_prior_can_express_path"]
                    for path in trace["dynamic_paths"]
                )
            ),
            "field_outcome_validated": False,
        },
        "acceptance_gates": {
            "mechanism_trace_present": bool(case_traces),
            "dynamic_path_distinct_from_static_prior": all(
                not path["static_prior_can_express_path"]
                for trace in case_traces
                for path in trace["dynamic_paths"]
            ),
            "field_outcome_validated": False,
            "product_guard_required": True,
        },
        "case_traces": case_traces,
        "source_refs": _source_refs(case_traces),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Mechanism propagation trace is a diagnostic mechanism artifact; "
                "it does not validate field outcomes or enable Product runtime "
                "default behavior."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "mechanism_trace_not_field_validation",
            "dynamic_path_requires_holdout_validation",
        ],
        "blocking_gaps": [
            "needs_mechanism_ablation_validation",
            "needs_operator_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_mechanism_propagation_trace(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_mechanism_propagation_trace(**kwargs),
    )


def _default_public_outcome_proxies(
    *,
    artifact_id: str,
    run_id: str,
) -> list[dict[str, Any]]:
    return [
        build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-{source_key}-proxy",
            run_id=run_id,
            source_key=source_key,
        )
        for source_key in DEFAULT_SOURCE_KEYS
    ]


def _build_case_trace(proxy: dict[str, Any]) -> dict[str, Any]:
    template = get_r6_case_template(proxy["target_case_id"])
    exposure_graph = _build_exposure_graph(template["prior_segments"])
    propagation_rounds = _build_propagation_rounds(
        template=template,
        exposure_graph=exposure_graph,
    )
    dynamic_paths = _build_dynamic_paths(
        template=template,
        exposure_graph=exposure_graph,
    )
    return {
        "source_key": proxy["source_key"],
        "source_public_outcome_proxy_id": proxy["artifact_id"],
        "case_id": template["case_id"],
        "case_type": template["case_type"],
        "target_case_type": proxy.get("target_case_type", template["case_type"]),
        "exposure_graph": exposure_graph,
        "propagation_rounds": propagation_rounds,
        "dynamic_paths": dynamic_paths,
        "proxy_summary": {
            "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
            "row_count": proxy["metrics"]["row_count"],
            "outcome_source_level": proxy["outcome_override"][
                "outcome_source_level"
            ],
        },
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "mechanism_trace_not_field_validation",
            "dynamic_path_requires_holdout_validation",
        ],
    }


def _build_exposure_graph(prior_segments: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [_segment_node(segment) for segment in prior_segments]
    high_sensitivity_low_trust = [
        node
        for node in nodes
        if node["sensitivity"] == "high" and node["trust"] == "low"
    ]
    medium_segments = [
        node
        for node in nodes
        if node["sensitivity"] == "medium" or node["trust"] == "medium"
    ]
    official_high_trust = [node for node in nodes if node["trust"] == "high"]
    low_trust_segments = [node for node in nodes if node["trust"] == "low"]
    edges = []
    for source in high_sensitivity_low_trust:
        for target in medium_segments:
            if source["segment_id"] != target["segment_id"]:
                edges.append(
                    {
                        "source_segment_id": source["segment_id"],
                        "target_segment_id": target["segment_id"],
                        "channel": "peer_discussion",
                        "mechanism": "risk_salience_amplification",
                        "direction": "risk_diffusion",
                    }
                )
    for source in official_high_trust:
        for target in low_trust_segments:
            if source["segment_id"] != target["segment_id"]:
                edges.append(
                    {
                        "source_segment_id": source["segment_id"],
                        "target_segment_id": target["segment_id"],
                        "channel": "official_exposure",
                        "mechanism": "trust_buffer_contrast",
                        "direction": "official_to_low_trust",
                    }
                )
    return {
        "nodes": nodes,
        "edges": edges,
    }


def _segment_node(segment: dict[str, Any]) -> dict[str, Any]:
    traits = segment["static_traits"]
    return {
        "segment_id": segment["segment_id"],
        "weight": segment["weight"],
        "trust": traits["trust"],
        "sensitivity": traits["sensitivity"],
        "static_reject_prior": segment["static_response_prior"]["reject"],
    }


def _build_propagation_rounds(
    *,
    template: dict[str, Any],
    exposure_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = exposure_graph["nodes"]
    low_trust = _first_node(nodes, trust="low")
    medium = _first_node(nodes, trust="medium") or _first_node(
        nodes,
        sensitivity="medium",
    )
    high_trust = _first_node(nodes, trust="high")
    return [
        {
            "round": 1,
            "phase": "official_exposure",
            "source": template["scenario"]["communication_plan"]["source"],
            "mechanism": "official_exposure",
            "activated_segment_ids": [
                node["segment_id"] for node in [high_trust, low_trust] if node
            ],
        },
        {
            "round": 2,
            "phase": "peer_or_community_amplification",
            "source": "peer_or_community_discussion",
            "mechanism": "peer_amplified_risk_diffusion",
            "activated_segment_ids": [
                node["segment_id"] for node in [low_trust, medium] if node
            ],
        },
        {
            "round": 3,
            "phase": "memory_accumulation_and_risk_activation",
            "source": "accumulated_exposure_memory",
            "mechanism": "memory_threshold_activation",
            "activated_segment_ids": [
                node["segment_id"] for node in [low_trust, medium] if node
            ],
        },
    ]


def _build_dynamic_paths(
    *,
    template: dict[str, Any],
    exposure_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = exposure_graph["nodes"]
    low_trust = _first_node(nodes, trust="low")
    medium = _first_node(nodes, trust="medium") or _first_node(
        nodes,
        sensitivity="medium",
    )
    high_trust = _first_node(nodes, trust="high")
    return [
        {
            "path_type": "peer_amplified_risk_diffusion",
            "rounds": [1, 2],
            "source_segment_id": (
                low_trust["segment_id"] if low_trust else "unknown_low_trust"
            ),
            "target_segment_id": (
                medium["segment_id"] if medium else "unknown_medium_segment"
            ),
            "mechanism_sequence": [
                "official_exposure",
                "peer_or_community_amplification",
            ],
            "scenario_impact_dimensions": template["scenario"][
                "impact_dimensions"
            ],
            "static_prior_can_express_path": False,
            "why_static_prior_cannot_express_path": (
                "Static prior stores segment-level response propensity but not "
                "cross-segment exposure, ordering, or peer amplification."
            ),
        },
        {
            "path_type": "memory_threshold_activation",
            "rounds": [1, 2, 3],
            "source_segment_id": (
                high_trust["segment_id"] if high_trust else "unknown_high_trust"
            ),
            "target_segment_id": (
                low_trust["segment_id"] if low_trust else "unknown_low_trust"
            ),
            "mechanism_sequence": [
                "official_exposure",
                "peer_or_community_amplification",
                "memory_accumulation_and_risk_activation",
            ],
            "scenario_impact_dimensions": template["scenario"][
                "impact_dimensions"
            ],
            "static_prior_can_express_path": False,
            "why_static_prior_cannot_express_path": (
                "Static prior has no stateful memory threshold or repeated "
                "exposure accumulation operator."
            ),
        },
    ]


def _first_node(
    nodes: list[dict[str, Any]],
    *,
    trust: str | None = None,
    sensitivity: str | None = None,
) -> dict[str, Any] | None:
    for node in nodes:
        if trust is not None and node["trust"] != trust:
            continue
        if sensitivity is not None and node["sensitivity"] != sensitivity:
            continue
        return node
    return None


def _source_refs(case_traces: list[dict[str, Any]]) -> list[str]:
    refs = [trace["source_public_outcome_proxy_id"] for trace in case_traces]
    refs.extend(trace["case_id"] for trace in case_traces)
    return list(dict.fromkeys(refs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_mechanism_propagation_trace(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "dynamic_path_count": report["trace_summary"][
                    "dynamic_path_count"
                ],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
