# R6 Dual-Line Trend Interval Risk Strengthening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补强 Research 与 Product 两条线，使 Research 明确支撑 Product 的核心价值：趋势方向、可信数值区间、风险分布、异常群体、机制解释和 outcome feedback learning。

**Architecture:** Research 先新增可计算 artifact，负责把现有 R6 ablation / interaction / outcome proxy 结果转成趋势、区间、排序、异常群体和误报控制指标。Product 再消费这些 artifact，更新 story package、decision report、API manifest 和 readiness index，确保客户可见输出不再停留在泛泛叙事，而是绑定 Research 证据。

**Tech Stack:** Python 3、pytest、JSON artifact contracts、现有 `experiments/r6_*.py` artifact builder、`experiments/r6_contracts.py` 校验工具。

---

## 当前判断

这轮不是继续追求“精准预测系统”，也不是继续把 `beat static prior` 当主目标。目标是让项目能回答：

1. Research 是否能支撑 Product 的核心价值？
2. Product 是否能把 Research 证据转成客户可理解、可审计、可复盘的输出？
3. 如果 Research 证据不足，Product 是否能明确展示 blocked claims，而不是包装成已验证能力？

## 文件结构

新增：

- `experiments/r6_trend_interval_risk_metrics.py`：Research 主指标 artifact，计算趋势方向、区间覆盖、风险排序、异常群体召回和 false-alarm control。
- `tests/test_r6_trend_interval_risk_metrics.py`：覆盖指标计算、失败边界和 CLI 输出。
- `experiments/r6_research_product_value_support.py`：Research -> Product 价值支撑报告，明确每项 Research 证据支撑哪个 Product 核心能力。
- `tests/test_r6_research_product_value_support.py`：验证映射完整、缺口 fail-closed、危险 claim 被阻断。
- `experiments/r6_product_customer_value_report.py`：Product 客户价值报告 artifact，消费 story / decision / trend metrics / value support。
- `tests/test_r6_product_customer_value_report.py`：验证客户可见报告包含趋势、区间、风险分布、异常群体、机制解释、证据来源和 blocked claims。

修改：

- `experiments/r6_product_story_package.py`：增加 Product 新定位下的必要 section 和 source registry。
- `tests/test_r6_product_story_package.py`：要求 story package 暴露 trend / interval / abnormal segment contract。
- `experiments/r6_product_decision_report.py`：增加客户可见 section：trend direction、risk interval、risk distribution、abnormal segments。
- `tests/test_r6_product_decision_report.py`：验证 decision report 不再只有旧的 risk shift 文案合同。
- `experiments/r6_product_api_manifest.py`：增加 customer value report endpoint 和 source registry。
- `tests/test_r6_product_api_manifest.py`：验证 API manifest 解析新 artifact，且所有 source refs 可解析。
- `experiments/r6_product_readiness_index.py`：增加 trend/interval/risk section readiness gate。
- `tests/test_r6_product_readiness_index.py`：验证 readiness 关闭旧 gap，保留 field outcome 和 runtime default gap。
- `docs/CURRENT_STATE.md`：记录计划执行后的 artifact 状态和仍未解决 gap。

## 双线目标

### Research 线

目标：把 Research 从“点预测 accuracy 诊断”升级为 Product 价值支撑层。

Research 必须给出：

1. `trend_direction_accuracy`：趋势方向是否与 outcome/proxy 一致。
2. `interval_coverage`：可信区间是否覆盖 outcome/proxy。
3. `interval_width`：区间是否过宽，避免“永远覆盖”的伪安全。
4. `risk_ranking_quality`：交互仿真给出的风险排序是否有决策价值。
5. `abnormal_segment_recall`：是否识别静态平均先验容易掩盖的异常群体。
6. `false_alarm_control_status`：误报是否可控，若不可控必须 blocked。
7. `product_value_support_map`：每项证据支撑 Product 哪个核心能力。

验收标准：

- 指标可计算，不允许只有自然语言判断。
- 当前 mixed evidence 可以继续是 partial / blocked，但必须结构化报告原因。
- 不能出现 `field_validated=true`、`runtime_default_allowed=true` 或 `accuracy superiority established`。

### Product 线

目标：把 Product 从“可审计证据链”升级为“客户能看懂、能用于发布前决策的趋势与风险区间报告”。

Product 必须给出：

1. 静态先验基线。
2. 交互仿真趋势方向。
3. 风险数值区间。
4. 风险分布和高风险群体排序。
5. 异常群体列表。
6. 机制解释路径。
7. Research 支撑证据卡。
8. blocked claims。
9. outcome review 入口。

验收标准：

- 所有客户可见字段都有 source artifact。
- 没有静态 fallback 文案。
- 没有精准单点预测承诺。
- Product readiness 从 `needs_customer_facing_ui_integration` 前进一步，至少形成客户报告/API artifact；真正 UI 可作为下一阶段。

---

### Task 1: Research 趋势、区间、风险指标 artifact

**Files:**
- Create: `experiments/r6_trend_interval_risk_metrics.py`
- Create: `tests/test_r6_trend_interval_risk_metrics.py`
- Read: `experiments/r6_decision_value_metrics.py`
- Read: `experiments/r6_ablation_report.py`
- Read: `experiments/r6_public_outcome_proxy.py`

- [ ] **Step 1: Write failing tests for Research metric contract**

Create `tests/test_r6_trend_interval_risk_metrics.py`:

```python
import json
import subprocess
import sys

from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


def test_r6_trend_interval_risk_metrics_reports_product_relevant_research_gates():
    report = build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-test",
        run_id="r6-trend-interval-risk-run",
    )

    assert report["schema_version"] == "r6-trend-interval-risk-metrics-v1"
    assert report["status"] == "trend_interval_risk_partial_high_false_alarm"
    assert report["research_supports_product_core_value"] is False
    assert report["summary"]["case_count"] == 3
    assert report["summary"]["trend_direction_accuracy"] == 0.667
    assert report["summary"]["interval_coverage"] == 0.667
    assert report["summary"]["risk_ranking_quality"] == 0.333
    assert report["summary"]["false_alarm_rate"] == 0.667
    assert report["acceptance_gates"] == {
        "trend_direction_metric_present": True,
        "interval_coverage_metric_present": True,
        "risk_ranking_metric_present": True,
        "abnormal_segment_metric_present": True,
        "trend_direction_passed": False,
        "interval_coverage_passed": False,
        "risk_ranking_passed": False,
        "false_alarm_control_passed": False,
        "research_supports_product_core_value": False,
    }
    assert "needs_lower_false_alarm_rate" in report["blocking_gaps"]
    assert "needs_independent_or_field_outcome_support" in report["blocking_gaps"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "field validation 已完成" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r6_trend_interval_risk_metrics_case_results_include_intervals_and_segments():
    report = build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-test",
        run_id="r6-trend-interval-risk-run",
    )

    by_source = {case["source_key"]: case for case in report["case_results"]}
    htops = by_source["htops_cost_pressure"]
    assert htops["trend_direction"] == "risk_up"
    assert htops["trend_direction_matches_outcome"] is True
    assert htops["risk_interval"]["lower"] <= htops["observed_reject_proxy"]
    assert htops["risk_interval"]["upper"] >= htops["observed_reject_proxy"]
    assert htops["top_abnormal_segments"][0]["segment_id"]
    assert htops["top_abnormal_segments"][0]["delta_reject"] > 0


def test_r6_trend_interval_risk_metrics_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-trend-interval-risk-metrics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_trend_interval_risk_metrics.py",
            "--artifact-id",
            "r6-trend-interval-risk-metrics-cli",
            "--run-id",
            "r6-trend-interval-risk-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-trend-interval-risk-metrics-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-trend-interval-risk-metrics-cli",
        "output": str(output),
        "status": "trend_interval_risk_partial_high_false_alarm",
        "research_supports_product_core_value": False,
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r6_trend_interval_risk_metrics.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'experiments.r6_trend_interval_risk_metrics'
```

- [ ] **Step 3: Implement metric builder**

Create `experiments/r6_trend_interval_risk_metrics.py` with these responsibilities:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_decision_value_metrics import (
    DEFAULT_SOURCE_KEYS,
    build_r6_decision_value_metrics,
)
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION = (
    "r6-trend-interval-risk-metrics-v1"
)


def build_r6_trend_interval_risk_metrics(
    *,
    artifact_id: str,
    run_id: str,
    source_keys: list[str] | None = None,
    ablation_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    reports = ablation_reports or _build_default_ablation_reports(
        artifact_id=artifact_id,
        run_id=run_id,
        source_keys=source_keys or DEFAULT_SOURCE_KEYS,
    )
    decision_value = build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value",
        run_id=run_id,
        ablation_reports=reports,
    )
    case_results = [
        _case_metrics(report, decision_case)
        for report, decision_case in zip(reports, decision_value["case_results"])
    ]
    summary = _summary(case_results, decision_value["summary"])
    supports_product = (
        summary["trend_direction_accuracy"] >= 0.80
        and summary["interval_coverage"] >= 0.80
        and summary["risk_ranking_quality"] >= 0.50
        and summary["false_alarm_rate"] <= 0.50
    )
    status = (
        "trend_interval_risk_supported"
        if supports_product
        else "trend_interval_risk_partial_high_false_alarm"
    )
    report = {
        "schema_version": R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "research_supports_product_core_value": supports_product,
        "metric_definition": {
            "trend_direction_accuracy": "Share of cases where interaction direction matches observed/proxy direction relative to static prior.",
            "interval_coverage": "Share of cases where observed/proxy reject rate falls inside the interaction risk interval.",
            "risk_ranking_quality": "Share of interaction-flagged high-risk cases that are observed/proxy high risk.",
            "abnormal_segment_recall": "Share of cases with at least one positive-delta segment surfaced as an abnormal segment.",
            "false_alarm_rate": "Share of interaction-flagged cases that are not observed/proxy high risk.",
        },
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "trend_direction_metric_present": True,
            "interval_coverage_metric_present": True,
            "risk_ranking_metric_present": True,
            "abnormal_segment_metric_present": True,
            "trend_direction_passed": summary["trend_direction_accuracy"] >= 0.80,
            "interval_coverage_passed": summary["interval_coverage"] >= 0.80,
            "risk_ranking_passed": summary["risk_ranking_quality"] >= 0.50,
            "false_alarm_control_passed": summary["false_alarm_rate"] <= 0.50,
            "research_supports_product_core_value": supports_product,
        },
        "source_refs": [case["source_ablation_artifact_id"] for case in case_results],
        "allowed_claims": [
            "Research can report trend direction, risk interval, risk ranking, abnormal segments, and false-alarm status as auditable metrics.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "系统可以精确预测单点结果",
            "field validation 已完成",
            "runtime default 可以开启",
            "accuracy superiority established",
        ],
        "blocking_gaps": []
        if supports_product
        else [
            "needs_lower_false_alarm_rate",
            "needs_independent_or_field_outcome_support",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report
```

Add helper functions in the same file:

```python
def _build_default_ablation_reports(
    *,
    artifact_id: str,
    run_id: str,
    source_keys: list[str],
) -> list[dict[str, Any]]:
    reports = []
    for source_key in source_keys:
        proxy = build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-{source_key}-proxy",
            run_id=run_id,
            source_key=source_key,
        )
        reports.append(
            build_r6_ablation_report(
                artifact_id=f"{artifact_id}-{source_key}-ablation",
                run_id=run_id,
                public_outcome_proxy=proxy,
            )
        )
    return reports


def _case_metrics(
    ablation: dict[str, Any],
    decision_case: dict[str, Any],
) -> dict[str, Any]:
    source_key = decision_case["source_key"]
    static = decision_case["static_prior_prediction"]
    interaction = decision_case["interaction_prediction"]
    observed = decision_case["observed_reject_proxy"]
    delta = round(interaction - static, 3)
    trend_direction = "risk_up" if delta > 0 else "risk_down" if delta < 0 else "flat"
    outcome_direction = (
        "risk_up"
        if observed - static > 0
        else "risk_down"
        if observed - static < 0
        else "flat"
    )
    interval_half_width = max(0.05, abs(delta))
    lower = round(max(0.0, interaction - interval_half_width), 3)
    upper = round(min(1.0, interaction + interval_half_width), 3)
    top_segments = _top_abnormal_segments(ablation)
    return {
        "source_ablation_artifact_id": ablation["artifact_id"],
        "source_key": source_key,
        "target_case_id": decision_case["target_case_id"],
        "static_prior_prediction": static,
        "interaction_prediction": interaction,
        "observed_reject_proxy": observed,
        "trend_direction": trend_direction,
        "outcome_direction": outcome_direction,
        "trend_direction_matches_outcome": trend_direction == outcome_direction,
        "risk_interval": {
            "lower": lower,
            "upper": upper,
            "width": round(upper - lower, 3),
            "contains_observed": lower <= observed <= upper,
        },
        "risk_ranking_hit": (
            decision_case["interaction_flags_new_risk"]
            and decision_case["observed_high_risk"]
        ),
        "interaction_false_alarm": decision_case["interaction_false_alarm"],
        "top_abnormal_segments": top_segments,
        "abnormal_segment_detected": bool(top_segments),
    }


def _top_abnormal_segments(ablation: dict[str, Any]) -> list[dict[str, Any]]:
    risk_shift = ablation.get("source_risk_shift_report", {})
    segments = risk_shift.get("top_risk_segments", [])
    normalized = [
        {
            "segment_id": segment["segment_id"],
            "delta_reject": float(segment["delta_reject"]),
            "mechanisms": list(segment.get("mechanisms", [])),
        }
        for segment in segments
        if float(segment.get("delta_reject", 0.0)) > 0
    ]
    return sorted(normalized, key=lambda item: item["delta_reject"], reverse=True)[:3]


def _summary(
    case_results: list[dict[str, Any]],
    decision_summary: dict[str, Any],
) -> dict[str, Any]:
    case_count = len(case_results)
    trend_matches = sum(
        1 for case in case_results if case["trend_direction_matches_outcome"]
    )
    interval_hits = sum(
        1 for case in case_results if case["risk_interval"]["contains_observed"]
    )
    abnormal_hits = sum(
        1 for case in case_results if case["abnormal_segment_detected"]
    )
    return {
        "case_count": case_count,
        "trend_direction_accuracy": round(trend_matches / case_count, 3),
        "interval_coverage": round(interval_hits / case_count, 3),
        "mean_interval_width": round(
            sum(case["risk_interval"]["width"] for case in case_results) / case_count,
            3,
        ),
        "risk_ranking_quality": decision_summary["top_k_risk_hit_rate"],
        "abnormal_segment_recall": round(abnormal_hits / case_count, 3),
        "false_alarm_rate": decision_summary["false_alarm_rate"],
        "decision_regret_reduction": decision_summary["decision_regret_reduction"],
    }
```

Add CLI:

```python
def write_r6_trend_interval_risk_metrics(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_trend_interval_risk_metrics(**kwargs))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = write_r6_trend_interval_risk_metrics(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output),
                "status": report["status"],
                "research_supports_product_core_value": report[
                    "research_supports_product_core_value"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run metric tests**

Run:

```bash
python -m pytest tests/test_r6_trend_interval_risk_metrics.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit Research metric artifact**

```bash
git add experiments/r6_trend_interval_risk_metrics.py tests/test_r6_trend_interval_risk_metrics.py
git commit -m "feat: add R6 trend interval risk metrics"
```

---

### Task 2: Research -> Product 价值支撑报告

**Files:**
- Create: `experiments/r6_research_product_value_support.py`
- Create: `tests/test_r6_research_product_value_support.py`
- Read: `experiments/r6_trend_interval_risk_metrics.py`
- Read: `experiments/r6_mechanism_research_readiness_report.py`

- [ ] **Step 1: Write failing tests for support mapping**

Create `tests/test_r6_research_product_value_support.py`:

```python
import json
import subprocess
import sys

import pytest

from experiments.r6_research_product_value_support import (
    build_r6_research_product_value_support,
)


def test_r6_research_product_value_support_maps_research_to_product_values():
    report = build_r6_research_product_value_support(
        artifact_id="r6-research-product-value-support-test",
        run_id="r6-product-value-run",
    )

    assert report["schema_version"] == "r6-research-product-value-support-v1"
    assert report["status"] == "product_value_support_partial"
    assert report["overall_product_core_value_supported"] is False
    support = {
        item["product_value"]: item["support_status"]
        for item in report["support_matrix"]
    }
    assert support == {
        "trend_direction": "partial_current_proxy",
        "risk_interval": "partial_current_proxy",
        "risk_distribution": "partial_high_false_alarm",
        "abnormal_segments": "diagnostic_only",
        "mechanism_explanation": "diagnostic_only",
        "outcome_feedback_learning": "blocked_until_holdout_or_field_outcome",
    }
    assert "needs_trend_interval_holdout_support" in report["blocking_gaps"]
    assert "needs_false_alarm_control" in report["blocking_gaps"]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
    assert "精准预测系统" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r6_research_product_value_support_rejects_unknown_metric_status():
    metrics = {
        "schema_version": "r6-trend-interval-risk-metrics-v1",
        "artifact_id": "bad-metrics",
        "status": "unsupported_status",
        "summary": {},
        "source_refs": ["source"],
        "blocking_gaps": [],
    }

    with pytest.raises(ValueError, match="trend_interval_risk_metrics.status"):
        build_r6_research_product_value_support(
            artifact_id="r6-research-product-value-support-bad",
            run_id="r6-product-value-run",
            trend_interval_risk_metrics=metrics,
        )


def test_r6_research_product_value_support_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-research-product-value-support.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_research_product_value_support.py",
            "--artifact-id",
            "r6-research-product-value-support-cli",
            "--run-id",
            "r6-product-value-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-research-product-value-support-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-research-product-value-support-cli",
        "output": str(output),
        "status": "product_value_support_partial",
        "overall_product_core_value_supported": False,
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r6_research_product_value_support.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'experiments.r6_research_product_value_support'
```

- [ ] **Step 3: Implement support report**

Create `experiments/r6_research_product_value_support.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_trend_interval_risk_metrics import (
    R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION,
    build_r6_trend_interval_risk_metrics,
)


R6_RESEARCH_PRODUCT_VALUE_SUPPORT_SCHEMA_VERSION = (
    "r6-research-product-value-support-v1"
)
SUPPORTED_TREND_METRIC_STATUSES = {
    "trend_interval_risk_supported",
    "trend_interval_risk_partial_high_false_alarm",
}


def build_r6_research_product_value_support(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    mechanism_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    mechanism = mechanism_readiness or build_r6_mechanism_research_readiness_report(
        artifact_id="r6-mechanism-research-readiness-report-current-001",
        run_id=run_id,
    )
    _validate_metrics(metrics)
    summary = metrics["summary"]
    support_matrix = [
        {
            "product_value": "trend_direction",
            "support_status": _threshold_support(
                summary["trend_direction_accuracy"],
                pass_threshold=0.80,
            ),
            "source_metric": "trend_direction_accuracy",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "risk_interval",
            "support_status": _threshold_support(
                summary["interval_coverage"],
                pass_threshold=0.80,
            ),
            "source_metric": "interval_coverage",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "risk_distribution",
            "support_status": "partial_high_false_alarm"
            if summary["false_alarm_rate"] > 0.50
            else "supported_current_proxy",
            "source_metric": "risk_ranking_quality",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "abnormal_segments",
            "support_status": "diagnostic_only",
            "source_metric": "abnormal_segment_recall",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "mechanism_explanation",
            "support_status": "diagnostic_only",
            "source_metric": "mechanism_research_status",
            "source_artifact_ids": [mechanism["artifact_id"]],
        },
        {
            "product_value": "outcome_feedback_learning",
            "support_status": "blocked_until_holdout_or_field_outcome",
            "source_metric": "runtime_default_allowed",
            "source_artifact_ids": [mechanism["artifact_id"]],
        },
    ]
    overall_supported = all(
        item["support_status"].startswith("supported")
        for item in support_matrix
    )
    report = {
        "schema_version": R6_RESEARCH_PRODUCT_VALUE_SUPPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_value_support_ready"
        if overall_supported
        else "product_value_support_partial",
        "overall_product_core_value_supported": overall_supported,
        "support_matrix": support_matrix,
        "source_refs": [metrics["artifact_id"], mechanism["artifact_id"]],
        "allowed_claims": [
            "Research evidence can support guarded trend and interval reporting.",
            "Risk distribution, abnormal segments, mechanism explanation, and outcome feedback remain guarded until false-alarm and holdout gaps close.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "系统可以精确预测单点结果",
            "field validation 已完成",
            "runtime default 可以开启",
            "Research 已完整支撑 Product 全部核心价值",
        ],
        "blocking_gaps": []
        if overall_supported
        else [
            "needs_false_alarm_control",
            "needs_field_outcome_validation",
            "needs_runtime_default_holdout_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report
```

Add validation and CLI:

```python
def _validate_metrics(metrics: dict[str, Any]) -> None:
    if metrics.get("schema_version") != R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION:
        raise ValueError("trend_interval_risk_metrics.schema_version is invalid")
    status = metrics.get("status")
    if status not in SUPPORTED_TREND_METRIC_STATUSES:
        raise ValueError("trend_interval_risk_metrics.status is invalid")
    if not isinstance(metrics.get("summary"), dict):
        raise ValueError("trend_interval_risk_metrics.summary must be an object")
    non_empty_string(metrics.get("artifact_id"), field="trend_interval_risk_metrics.artifact_id")


def _threshold_support(value: float, *, pass_threshold: float) -> str:
    if value >= pass_threshold:
        return "supported_current_proxy"
    if value > 0:
        return "partial_current_proxy"
    return "blocked"


def write_r6_research_product_value_support(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_research_product_value_support(**kwargs))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = write_r6_research_product_value_support(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output),
                "status": report["status"],
                "overall_product_core_value_supported": report[
                    "overall_product_core_value_supported"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run support report tests**

Run:

```bash
python -m pytest tests/test_r6_research_product_value_support.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit support report**

```bash
git add experiments/r6_research_product_value_support.py tests/test_r6_research_product_value_support.py
git commit -m "feat: map R6 research evidence to product value"
```

---

### Task 3: Product 客户价值报告 artifact

**Files:**
- Create: `experiments/r6_product_customer_value_report.py`
- Create: `tests/test_r6_product_customer_value_report.py`
- Read: `experiments/r6_product_decision_report.py`
- Read: `experiments/r6_research_product_value_support.py`

- [ ] **Step 1: Write failing tests for customer value report**

Create `tests/test_r6_product_customer_value_report.py`:

```python
import json
import subprocess
import sys

from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)


def test_r6_product_customer_value_report_contains_trend_interval_risk_sections():
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-test",
        run_id="r6-customer-value-run",
    )

    assert report["schema_version"] == "r6-product-customer-value-report-v1"
    assert report["status"] == "customer_value_report_ready_guarded"
    assert report["positioning"] == "人群反应趋势与风险区间模拟器"
    assert report["report_contract"]["precise_point_prediction_allowed"] is False
    assert report["customer_sections"] == [
        "static_prior_baseline",
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "evidence_and_blocked_claims",
        "outcome_review_plan",
    ]
    assert "trend_direction" in report["display_payload"]
    assert "risk_interval" in report["display_payload"]
    assert "risk_distribution" in report["display_payload"]
    assert "abnormal_segments" in report["display_payload"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "r6-research-product-value-support-current-001" in report["source_refs"]
    json.dumps(report, allow_nan=False)


def test_r6_product_customer_value_report_sources_are_resolvable():
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-test",
        run_id="r6-customer-value-run",
    )

    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    for source_ref in report["source_refs"]:
        assert source_ref in registry_ids or source_ref == report["artifact_id"]
    for section in report["section_contracts"]:
        assert section["source_artifact_ids"]
        for source_artifact_id in section["source_artifact_ids"]:
            assert source_artifact_id in registry_ids


def test_r6_product_customer_value_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-product-customer-value-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_customer_value_report.py",
            "--artifact-id",
            "r6-product-customer-value-report-cli",
            "--run-id",
            "r6-customer-value-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-product-customer-value-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-customer-value-report-cli",
        "output": str(output),
        "status": "customer_value_report_ready_guarded",
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_r6_product_customer_value_report.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'experiments.r6_product_customer_value_report'
```

- [ ] **Step 3: Implement customer value report**

Create `experiments/r6_product_customer_value_report.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_product_decision_report import build_r6_product_decision_report
from experiments.r6_research_product_value_support import (
    build_r6_research_product_value_support,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION = (
    "r6-product-customer-value-report-v1"
)
R6_PRODUCT_CUSTOMER_VALUE_SECTIONS = [
    "static_prior_baseline",
    "trend_direction",
    "risk_interval",
    "risk_distribution",
    "abnormal_segments",
    "mechanism_explanation",
    "evidence_and_blocked_claims",
    "outcome_review_plan",
]


def build_r6_product_customer_value_report(
    *,
    artifact_id: str,
    run_id: str,
    decision_report: dict[str, Any] | None = None,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    value_support: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision = decision_report or build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-current-001",
        run_id=run_id,
    )
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    support = value_support or build_r6_research_product_value_support(
        artifact_id="r6-research-product-value-support-current-001",
        run_id=run_id,
        trend_interval_risk_metrics=metrics,
    )
    source_registry = _source_registry(decision, metrics, support)
    report = {
        "schema_version": R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "customer_value_report_ready_guarded",
        "positioning": "人群反应趋势与风险区间模拟器",
        "customer_sections": R6_PRODUCT_CUSTOMER_VALUE_SECTIONS,
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "precise_point_prediction_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "display_payload": _display_payload(metrics, support),
        "section_contracts": _section_contracts(decision, metrics, support),
        "source_registry": source_registry,
        "source_refs": [entry["artifact_id"] for entry in source_registry],
        "blocked_claims": _unique_strings(
            [
                *decision.get("blocked_claims", []),
                *support.get("blocked_claims", []),
                "精准预测系统",
                "系统可以精确预测单点结果",
            ]
        ),
        "allowed_claims": [
            "Product can display trend, interval, distribution, abnormal segments, and mechanism explanation from source-backed artifacts.",
            "Current output is guarded and does not claim field validation or precise point prediction.",
        ],
        "blocking_gaps": [
            "needs_customer_facing_ui_integration",
            "needs_field_outcome_validation",
            "needs_runtime_default_holdout_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report
```

Add helper functions:

```python
def _display_payload(
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> dict[str, Any]:
    cases = metrics["case_results"]
    return {
        "trend_direction": {
            "summary_metric": metrics["summary"]["trend_direction_accuracy"],
            "cases": [
                {
                    "source_key": case["source_key"],
                    "trend_direction": case["trend_direction"],
                    "outcome_direction": case["outcome_direction"],
                    "matches_outcome": case["trend_direction_matches_outcome"],
                }
                for case in cases
            ],
        },
        "risk_interval": {
            "summary_metric": metrics["summary"]["interval_coverage"],
            "cases": [
                {
                    "source_key": case["source_key"],
                    "risk_interval": case["risk_interval"],
                    "observed_reject_proxy": case["observed_reject_proxy"],
                }
                for case in cases
            ],
        },
        "risk_distribution": {
            "risk_ranking_quality": metrics["summary"]["risk_ranking_quality"],
            "false_alarm_rate": metrics["summary"]["false_alarm_rate"],
        },
        "abnormal_segments": [
            {
                "source_key": case["source_key"],
                "segments": case["top_abnormal_segments"],
            }
            for case in cases
        ],
        "mechanism_explanation": {
            "support_status": _support_status(support, "mechanism_explanation"),
            "claim_status": "diagnostic_only",
        },
    }


def _section_contracts(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "section_id": "static_prior_baseline",
            "source_artifact_ids": [decision["artifact_id"]],
        },
        {
            "section_id": "trend_direction",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_interval",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_distribution",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "abnormal_segments",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "mechanism_explanation",
            "source_artifact_ids": [support["artifact_id"]],
        },
        {
            "section_id": "evidence_and_blocked_claims",
            "source_artifact_ids": [decision["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "outcome_review_plan",
            "source_artifact_ids": [decision["artifact_id"]],
        },
    ]


def _source_registry(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "artifact_id": decision["artifact_id"],
            "path": "experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json",
        },
        {
            "artifact_id": metrics["artifact_id"],
            "path": "experiments/results/r6_trend_interval_risk_metrics/r6-trend-interval-risk-metrics-current-001.json",
        },
        {
            "artifact_id": support["artifact_id"],
            "path": "experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json",
        },
    ]


def _support_status(support: dict[str, Any], product_value: str) -> str:
    for item in support["support_matrix"]:
        if item["product_value"] == product_value:
            return item["support_status"]
    raise ValueError(f"missing support_matrix item: {product_value}")


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
```

Add CLI like previous builders:

```python
def write_r6_product_customer_value_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_customer_value_report(**kwargs))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = write_r6_product_customer_value_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output),
                "status": report["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run customer value report tests**

Run:

```bash
python -m pytest tests/test_r6_product_customer_value_report.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit customer value report**

```bash
git add experiments/r6_product_customer_value_report.py tests/test_r6_product_customer_value_report.py
git commit -m "feat: add R6 product customer value report"
```

---

### Task 4: Product story / decision / API 合同接入

**Files:**
- Modify: `experiments/r6_product_story_package.py`
- Modify: `tests/test_r6_product_story_package.py`
- Modify: `experiments/r6_product_decision_report.py`
- Modify: `tests/test_r6_product_decision_report.py`
- Modify: `experiments/r6_product_api_manifest.py`
- Modify: `tests/test_r6_product_api_manifest.py`

- [ ] **Step 1: Update story package tests**

In `tests/test_r6_product_story_package.py`, extend `test_r6_product_story_package_is_artifact_backed_and_no_static_fallback`:

```python
    assert "trend_direction" in package["sections"]
    assert "risk_interval" in package["sections"]
    assert "risk_distribution" in package["sections"]
    assert "abnormal_segments" in package["sections"]
    assert "r6-product-customer-value-report-current-001" in package["source_refs"]
```

- [ ] **Step 2: Update story package implementation**

In `experiments/r6_product_story_package.py`:

1. Do not import `build_r6_product_customer_value_report` into story package. Story package only declares the customer value report source artifact id to avoid a `story_package -> customer_value_report -> decision_report -> story_package` cycle.
2. Add `R6_PRODUCT_STORY_PACKAGE_SECTIONS` entries:

```python
"trend_direction",
"risk_interval",
"risk_distribution",
"abnormal_segments",
```

3. Add canonical source registry entry:

```python
{
    "artifact_id": "r6-product-customer-value-report-current-001",
    "path": (
        "experiments/results/r6_product_customer_value_report/"
        "r6-product-customer-value-report-current-001.json"
    ),
}
```

4. Add the artifact id to `artifact_refs`, `source_refs`, and section contracts without building the artifact in this module.

- [ ] **Step 3: Update decision report tests**

In `tests/test_r6_product_decision_report.py`, extend expected `customer_sections`:

```python
assert "trend_direction" in report["customer_sections"]
assert "risk_interval" in report["customer_sections"]
assert "risk_distribution" in report["customer_sections"]
assert "abnormal_segments" in report["customer_sections"]
```

Also assert:

```python
assert report["report_contract"]["precise_point_prediction_allowed"] is False
assert "r6-product-customer-value-report-current-001" in report["source_refs"]
```

- [ ] **Step 4: Update decision report implementation**

In `experiments/r6_product_decision_report.py`:

1. Extend `R6_PRODUCT_DECISION_REPORT_CUSTOMER_SECTIONS`:

```python
"trend_direction",
"risk_interval",
"risk_distribution",
"abnormal_segments",
```

2. Add report contract flag:

```python
"precise_point_prediction_allowed": False,
```

3. Add display sources:

```python
"trend_direction": "story_package.section_contracts[trend_direction]",
"risk_interval": "story_package.section_contracts[risk_interval]",
"risk_distribution": "story_package.section_contracts[risk_distribution]",
"abnormal_segments": "story_package.section_contracts[abnormal_segments]",
```

- [ ] **Step 5: Update API manifest tests**

In `tests/test_r6_product_api_manifest.py`, update endpoint set:

```python
assert "customer_value_report" in endpoint_ids
```

Add source resolvability assertion:

```python
assert "r6-product-customer-value-report-current-001" in manifest["source_refs"]
```

- [ ] **Step 6: Update API manifest implementation**

In `experiments/r6_product_api_manifest.py`:

1. Add default artifact path key:

```python
"customer_value_report": (
    "experiments/results/r6_product_customer_value_report/"
    "r6-product-customer-value-report-current-001.json"
),
```

2. Add required artifact tuple:

```python
"customer_value_report": (
    "r6-product-customer-value-report-v1",
    "customer_value_report_ready_guarded",
),
```

3. Add endpoint:

```python
{
    "endpoint_id": "customer_value_report",
    "path": "/r6/product/customer-value-report",
    "method": "GET",
    "source_artifact_ids": [artifact_refs["customer_value_report"]],
}
```

4. Add display contract section requirements for trend/interval/risk/abnormal segments.

- [ ] **Step 7: Run product contract tests**

Run:

```bash
python -m pytest \
  tests/test_r6_product_story_package.py \
  tests/test_r6_product_decision_report.py \
  tests/test_r6_product_api_manifest.py \
  -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 8: Commit Product contract integration**

```bash
git add \
  experiments/r6_product_story_package.py \
  tests/test_r6_product_story_package.py \
  experiments/r6_product_decision_report.py \
  tests/test_r6_product_decision_report.py \
  experiments/r6_product_api_manifest.py \
  tests/test_r6_product_api_manifest.py
git commit -m "feat: expose R6 trend interval risk product contract"
```

---

### Task 5: Readiness index 与 current artifacts 回填

**Files:**
- Modify: `experiments/r6_product_readiness_index.py`
- Modify: `tests/test_r6_product_readiness_index.py`
- Create generated: `experiments/results/r6_trend_interval_risk_metrics/r6-trend-interval-risk-metrics-current-001.json`
- Create generated: `experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json`
- Create generated: `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- Modify generated: `experiments/results/r6_product_story_package/r6-product-story-package-current-001.json`
- Modify generated: `experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json`
- Modify generated: `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- Modify generated: `experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json`

- [ ] **Step 1: Update readiness tests**

In `tests/test_r6_product_readiness_index.py`, assert:

```python
assert index["readiness_gates"]["trend_interval_risk_metrics_ready"] is True
assert index["readiness_gates"]["customer_value_report_ready"] is True
assert "needs_customer_facing_ui_integration" in index["blocking_gaps"]
assert "needs_field_outcome_validation" in index["blocking_gaps"]
assert "精准预测系统" in index["blocked_claims"]
```

- [ ] **Step 2: Update readiness implementation**

In `experiments/r6_product_readiness_index.py`, add:

```python
"trend_interval_risk_metrics_ready": True,
"research_product_value_support_ready": True,
"customer_value_report_ready": True,
```

Keep:

```python
"field_outcome_validated": False,
"runtime_default_allowed": False,
```

Do not remove `needs_customer_facing_ui_integration` unless a real UI consumes the API.

- [ ] **Step 3: Run readiness tests**

Run:

```bash
python -m pytest tests/test_r6_product_readiness_index.py -q
```

Expected:

```text
selected readiness tests passed
```

- [ ] **Step 4: Generate current Research artifacts**

Run:

```bash
python experiments/r6_trend_interval_risk_metrics.py \
  --artifact-id r6-trend-interval-risk-metrics-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_trend_interval_risk_metrics/r6-trend-interval-risk-metrics-current-001.json

python experiments/r6_research_product_value_support.py \
  --artifact-id r6-research-product-value-support-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json
```

Expected stdout statuses:

```text
trend_interval_risk_partial_high_false_alarm
product_value_support_partial
```

- [ ] **Step 5: Generate current Product artifacts**

Run:

```bash
python experiments/r6_product_customer_value_report.py \
  --artifact-id r6-product-customer-value-report-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json

python experiments/r6_product_story_package.py \
  --artifact-id r6-product-story-package-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_product_story_package/r6-product-story-package-current-001.json

python experiments/r6_product_decision_report.py \
  --artifact-id r6-product-decision-report-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json

python experiments/r6_product_readiness_index.py \
  --artifact-id r6-product-readiness-index-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json

python experiments/r6_product_api_manifest.py \
  --artifact-id r6-product-api-manifest-current-001 \
  --run-id r6-product-value-current-001 \
  --output experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json
```

Expected statuses:

```text
customer_value_report_ready_guarded
product_story_package_ready_guarded
decision_report_ready_guarded
product_first_readiness_partial
product_api_manifest_ready_guarded
```

- [ ] **Step 6: Run targeted and full R6 tests**

Run:

```bash
python -m pytest \
  tests/test_r6_trend_interval_risk_metrics.py \
  tests/test_r6_research_product_value_support.py \
  tests/test_r6_product_customer_value_report.py \
  tests/test_r6_product_story_package.py \
  tests/test_r6_product_decision_report.py \
  tests/test_r6_product_api_manifest.py \
  tests/test_r6_product_readiness_index.py \
  -q

python -m pytest tests/test_r6_*.py -q
```

Expected:

```text
all selected tests passed
all R6 tests passed
```

- [ ] **Step 7: Commit readiness and current artifacts**

Because `experiments/results` is ignored, use `git add -f` for generated JSON:

```bash
git add experiments/r6_product_readiness_index.py tests/test_r6_product_readiness_index.py
git add -f \
  experiments/results/r6_trend_interval_risk_metrics/r6-trend-interval-risk-metrics-current-001.json \
  experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json \
  experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json \
  experiments/results/r6_product_story_package/r6-product-story-package-current-001.json \
  experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json \
  experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json \
  experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json
git commit -m "data: refresh R6 trend interval product artifacts"
```

---

### Task 6: 状态文档与验收结论

**Files:**
- Modify: `docs/CURRENT_STATE.md`
- Optionally modify: `docs/active-spec.md`

- [ ] **Step 1: Update current state**

Append to `docs/CURRENT_STATE.md` under 已确认结论:

```markdown
50. Research/Product 双线补强已进入趋势与风险区间目标：Research 新增趋势方向、区间覆盖、风险排序、异常群体和 false-alarm control 指标；Product 新增 customer value report，用于把 Research 证据转成客户可见的趋势、区间、风险分布、异常群体和机制解释。当前结论若仍为 partial/high false alarm，Product 必须保留 blocked claims，不能声明精准预测、field validation 或 runtime default。
```

- [ ] **Step 2: Run docs grep**

Run:

```bash
rg -n "精准预测系统|精确预测单点|点预测 beat 静态先验|人群反应趋势与风险区间模拟器|trend_interval_risk|customer_value_report" \
  AGENTS.md docs/active-spec.md docs/CURRENT_STATE.md docs/superpowers/specs docs/superpowers/plans
```

Expected:

```text
new positioning appears in active files
old precise-prediction terms only appear as blocked/deprecated claims
```

- [ ] **Step 3: Run final verification**

Run:

```bash
python -m pytest tests/test_r6_*.py -q
python -m pytest -q
python -m py_compile \
  experiments/r6_trend_interval_risk_metrics.py \
  experiments/r6_research_product_value_support.py \
  experiments/r6_product_customer_value_report.py
git diff --check
```

Expected:

```text
R6 tests pass
full test suite passes or only known unrelated warnings appear
py_compile passes
git diff --check produces no output
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/CURRENT_STATE.md docs/active-spec.md
git commit -m "docs: record R6 trend interval product value plan"
```

---

## 并行方式

可并行：

- Task 1 和 Task 2 可以由 Research 线先后完成；Task 2 依赖 Task 1 的 schema。
- Task 3 可以在 Task 1 schema 固定后与 Task 2 并行。
- Task 4 依赖 Task 3 的 customer value report schema。
- Task 5 依赖 Task 1-4。
- Task 6 收尾。

建议执行顺序：

1. Research-A：Task 1。
2. Research-B：Task 2。
3. Product-A：Task 3。
4. Product-B：Task 4。
5. Integration：Task 5。
6. State：Task 6。

## 验收口径

成功不是“证明系统精准预测”。成功是：

1. Research 产出可计算指标，明确当前支持和不支持 Product 哪些价值。
2. Product 客户报告能展示趋势、区间、风险分布、异常群体和机制解释。
3. 当前 false alarm / holdout / field outcome gap 被明确展示，而不是隐藏。
4. 所有客户可见字段都有 source artifact。
5. 新增能力不破坏 existing R6 guard：不允许 field validation、runtime default、accuracy superiority 的过度声明。

如果 Task 1 的结果仍是 `partial_high_false_alarm`，这不是失败；它说明 Product 可以展示 guarded trend/interval 能力，但 Research 仍未完整支撑风险排序和异常群体泛化。这正是下一阶段是否继续方法创新或引入真实 field outcome 的决策依据。

## 自检

- Spec coverage：覆盖 `2026-06-19-r6-trend-interval-risk-positioning.md` 中的趋势方向、可信数值区间、风险分布、异常群体、机制解释、outcome feedback learning。
- Placeholder scan：无 `TBD`、无“稍后实现”、无未定义任务。
- Type consistency：新增 schema 分别为 `r6-trend-interval-risk-metrics-v1`、`r6-research-product-value-support-v1`、`r6-product-customer-value-report-v1`；artifact id 与 current paths 一致。
