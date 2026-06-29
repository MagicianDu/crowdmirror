# R6 Product-first Solid Next Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 R6 从 research artifact chain 推进成 Product-first 的可用产品闭环，同时保留 Research 的理论、证据和 claim boundary 支撑。

**Architecture:** 新增 Product readiness、scenario intake、story package、decision report 和 outcome review 五个 artifact/API contract。Research 输出只通过 evidence cards、gap closure summary、claim boundaries 和 remaining gaps 进入 Product，不允许 UI 或报告自己生成未绑定 artifact 的结论。

**Tech Stack:** Python 标准库、现有 `experiments/r6_contracts.py`、现有 R6 Product/evidence modules、pytest、JSON artifacts。

---

## 文件结构

- Modify: `docs/active-spec.md`
  - 固化 Product-first 目标和 Research 降级边界。
- Modify: `docs/CURRENT_STATE.md`
  - 记录当前目标调整、后续 Product-first 工作顺序和验收边界。
- Create: `experiments/r6_product_readiness_index.py`
  - 汇总 Product 是否可用于客户评估、哪些能力 ready、哪些能力 blocked。
- Create: `tests/test_r6_product_readiness_index.py`
  - 验证 readiness index 不把 diagnostic evidence 包装成 runtime-ready。
- Create: `experiments/r6_product_scenario_intake.py`
  - 将客户场景输入规范化为 Product 可运行的 R6 scenario contract。
- Create: `tests/test_r6_product_scenario_intake.py`
  - 验证航空票价/燃油费等场景不会过拟合成垂直方法，只作为 case input。
- Create: `experiments/r6_product_story_package.py`
  - 汇总 scenario、static prior、interaction shift、evidence cards、gap summary，供 UI/demo/report 消费。
- Create: `tests/test_r6_product_story_package.py`
  - 验证 story package 只消费 artifact 字段，不允许静态 narrative fallback。
- Create: `experiments/r6_product_decision_report.py`
  - 生成客户可读但 artifact-backed 的发布前决策报告 JSON。
- Create: `tests/test_r6_product_decision_report.py`
  - 验证报告包含风险摘要、证据边界、blocked claims 和下一步监测建议。
- Create: `experiments/r6_product_outcome_review.py`
  - 定义发布后 outcome 回流复盘 contract。
- Create: `tests/test_r6_product_outcome_review.py`
  - 验证 outcome 回流只生成误差归因和候选更新，不打开 runtime default。

---

### Task 1: Product Readiness Index

**Files:**
- Create: `experiments/r6_product_readiness_index.py`
- Create: `tests/test_r6_product_readiness_index.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_r6_product_readiness_index.py`:

```python
import json

from experiments.r6_product_readiness_index import build_r6_product_readiness_index


def test_r6_product_readiness_index_prioritizes_product_without_overclaiming():
    report = build_r6_product_readiness_index(
        artifact_id="r6-product-readiness-index-test",
        run_id="r6-product-first-run",
    )

    assert report["schema_version"] == "r6-product-readiness-index-v1"
    assert report["status"] == "product_first_readiness_partial"
    assert report["product_goal"] == {
        "primary": "usable_pre_release_risk_assessment_product",
        "research_role": "theory_and_evidence_boundary_support",
        "not_default_goal": "ccf_a_main_contribution",
    }
    assert report["readiness_gates"]["scenario_intake_ready"] is False
    assert report["readiness_gates"]["evidence_cards_ready"] is True
    assert report["readiness_gates"]["decision_report_ready"] is False
    assert report["readiness_gates"]["static_narrative_fallback_allowed"] is False
    assert report["readiness_gates"]["field_outcome_validated"] is False
    assert report["readiness_gates"]["runtime_default_allowed"] is False
    assert "needs_product_scenario_intake" in report["blocking_gaps"]
    assert "needs_customer_decision_report" in report["blocking_gaps"]
    assert "field validation 已完成" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_readiness_index.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_product_readiness_index'`.

- [ ] **Step 3: Implement minimal readiness index**

Create `experiments/r6_product_readiness_index.py` with:

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
from experiments.r6_evidence_report import build_r6_evidence_report


R6_PRODUCT_READINESS_INDEX_SCHEMA_VERSION = "r6-product-readiness-index-v1"


def build_r6_product_readiness_index(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    evidence_report = build_r6_evidence_report(
        artifact_id=f"{artifact_id}-evidence-report",
        run_id=run_id,
    )
    report = {
        "schema_version": R6_PRODUCT_READINESS_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_first_readiness_partial",
        "product_goal": {
            "primary": "usable_pre_release_risk_assessment_product",
            "research_role": "theory_and_evidence_boundary_support",
            "not_default_goal": "ccf_a_main_contribution",
        },
        "readiness_gates": {
            "scenario_intake_ready": False,
            "evidence_cards_ready": evidence_report["acceptance_gates"]["product_evidence_cards_present"],
            "decision_report_ready": False,
            "outcome_review_ready": False,
            "static_narrative_fallback_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "blocking_gaps": [
            "needs_product_scenario_intake",
            "needs_customer_decision_report",
            "needs_outcome_review_contract",
            "needs_product_ui_or_api_contract",
        ],
        "allowed_claims": [
            "R6 can support bounded pre-release risk discussion.",
            "R6 evidence cards are available as customer-facing claim boundaries.",
        ],
        "blocked_claims": [
            "field validation 已完成",
            "runtime default 可以开启",
            "R6 已达到 CCF-A 主贡献",
            "交互仿真稳定比静态先验更准",
        ],
        "source_refs": [evidence_report["artifact_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_readiness_index(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_readiness_index(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_readiness_index(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(json.dumps({"artifact_id": report["artifact_id"], "output": str(output_path), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_readiness_index.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add experiments/r6_product_readiness_index.py tests/test_r6_product_readiness_index.py
git commit -m "feat: add R6 product readiness index"
```

---

### Task 2: Product Scenario Intake

**Files:**
- Create: `experiments/r6_product_scenario_intake.py`
- Create: `tests/test_r6_product_scenario_intake.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_r6_product_scenario_intake.py`:

```python
import json

import pytest

from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake


def test_r6_product_scenario_intake_accepts_airline_fee_case_without_vertical_overfit():
    report = build_r6_product_scenario_intake(
        artifact_id="r6-product-scenario-intake-test",
        run_id="r6-product-first-run",
        scenario={
            "scenario_id": "airline-fuel-fee-001",
            "change_type": "price",
            "target_population": "existing_route_customers",
            "impact_dimensions": ["price_sensitivity", "fairness_concern", "churn_risk"],
            "communication_plan": "announce_fee_with_service_reason",
            "alternative_scenarios": ["no_fee", "smaller_fee", "loyalty_credit"],
            "decision_question": "Will the fee create unacceptable churn risk?",
            "assumptions": ["route has alternatives", "customers observe total price"],
        },
    )

    assert report["schema_version"] == "r6-product-scenario-intake-v1"
    assert report["status"] == "scenario_intake_ready"
    assert report["scenario"]["scenario_id"] == "airline-fuel-fee-001"
    assert report["scenario"]["domain_binding"] == "case_input_not_method_definition"
    assert report["scenario"]["method_family"] == "price_or_rule_change_reaction"
    assert report["product_contract"]["can_drive_product_story_package"] is True
    assert report["product_contract"]["vertical_overfit_allowed"] is False
    assert "case_specific_input_not_research_method" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_product_scenario_intake_rejects_missing_decision_question():
    with pytest.raises(ValueError, match="decision_question"):
        build_r6_product_scenario_intake(
            artifact_id="r6-product-scenario-intake-test",
            run_id="r6-product-first-run",
            scenario={
                "scenario_id": "bad-scenario",
                "change_type": "price",
                "target_population": "customers",
                "impact_dimensions": ["price_sensitivity"],
                "communication_plan": "announce",
                "alternative_scenarios": ["no_change"],
                "assumptions": ["customers see the total price before purchase"],
            },
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_scenario_intake.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_product_scenario_intake'`.

- [ ] **Step 3: Implement scenario intake**

Create `experiments/r6_product_scenario_intake.py`:

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


R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION = "r6-product-scenario-intake-v1"


def build_r6_product_scenario_intake(
    *,
    artifact_id: str,
    run_id: str,
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    scenario_payload = scenario or _default_scenario()
    normalized = {
        "scenario_id": non_empty_string(
            scenario_payload.get("scenario_id"), field="scenario.scenario_id"
        ),
        "change_type": non_empty_string(
            scenario_payload.get("change_type"), field="scenario.change_type"
        ),
        "target_population": non_empty_string(
            scenario_payload.get("target_population"),
            field="scenario.target_population",
        ),
        "impact_dimensions": _string_list(
            scenario_payload.get("impact_dimensions"),
            field="scenario.impact_dimensions",
        ),
        "communication_plan": non_empty_string(
            scenario_payload.get("communication_plan"),
            field="scenario.communication_plan",
        ),
        "alternative_scenarios": _string_list(
            scenario_payload.get("alternative_scenarios"),
            field="scenario.alternative_scenarios",
        ),
        "decision_question": non_empty_string(
            scenario_payload.get("decision_question"),
            field="scenario.decision_question",
        ),
        "assumptions": _string_list(
            scenario_payload.get("assumptions"),
            field="scenario.assumptions",
        ),
        "domain_binding": "case_input_not_method_definition",
        "method_family": _method_family(scenario_payload.get("change_type")),
    }
    report = {
        "schema_version": R6_PRODUCT_SCENARIO_INTAKE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "scenario_intake_ready",
        "scenario": normalized,
        "product_contract": {
            "can_drive_product_story_package": True,
            "vertical_overfit_allowed": False,
            "requires_static_prior_baseline": True,
            "requires_evidence_cards": True,
        },
        "risk_flags": [
            "case_specific_input_not_research_method",
            "scenario_assumptions_require_customer_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_scenario_intake(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_scenario_intake(**kwargs))


def _default_scenario() -> dict[str, Any]:
    return {
        "scenario_id": "generic-price-or-rule-change-001",
        "change_type": "price",
        "target_population": "affected_customers_or_public",
        "impact_dimensions": ["price_sensitivity", "fairness_concern", "churn_risk"],
        "communication_plan": "announce_change_with_reason",
        "alternative_scenarios": ["no_change", "phased_release", "support_credit"],
        "decision_question": "Which population segments need risk review before release?",
        "assumptions": ["static prior is available", "interaction risk is diagnostic"],
    }


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    items = [non_empty_string(item, field=f"{field}[{index}]") for index, item in enumerate(value)]
    if not items:
        raise ValueError(f"{field} must contain at least one item")
    return items


def _method_family(change_type: Any) -> str:
    normalized = non_empty_string(change_type, field="scenario.change_type")
    if normalized in {"price", "fee", "fare", "charge"}:
        return "price_or_rule_change_reaction"
    if normalized in {"rule", "policy", "rights", "service"}:
        return "price_or_rule_change_reaction"
    return "general_change_reaction"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_scenario_intake(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(json.dumps({"artifact_id": report["artifact_id"], "output": str(output_path), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_scenario_intake.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add experiments/r6_product_scenario_intake.py tests/test_r6_product_scenario_intake.py
git commit -m "feat: add R6 product scenario intake"
```

---

### Task 3: Product Story Package

**Files:**
- Create: `experiments/r6_product_story_package.py`
- Create: `tests/test_r6_product_story_package.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_r6_product_story_package.py`:

```python
import json

from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake
from experiments.r6_product_story_package import build_r6_product_story_package


def test_r6_product_story_package_is_artifact_backed_and_no_static_fallback():
    intake = build_r6_product_scenario_intake(
        artifact_id="r6-story-intake-test",
        run_id="r6-product-first-run",
    )
    package = build_r6_product_story_package(
        artifact_id="r6-product-story-package-test",
        run_id="r6-product-first-run",
        scenario_intake=intake,
    )

    assert package["schema_version"] == "r6-product-story-package-v1"
    assert package["status"] == "product_story_package_ready_guarded"
    assert package["sections"] == [
        "scenario",
        "static_prior_baseline",
        "interaction_risk_shift",
        "evidence_cards",
        "gap_closure",
        "blocked_claims",
        "next_measurement_plan",
    ]
    assert package["ui_contract"]["static_narrative_fallback_allowed"] is False
    assert package["ui_contract"]["all_customer_visible_claims_require_source_artifact"] is True
    assert "r6-gap-closure-status" in package["evidence_card_ids"]
    assert package["source_refs"]
    json.dumps(package, allow_nan=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_story_package.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_product_story_package'`.

- [ ] **Step 3: Implement story package**

Create `experiments/r6_product_story_package.py`:

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
from experiments.r6_evidence_report import build_r6_evidence_report
from experiments.r6_gap_closure_report import build_r6_gap_closure_report
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake


R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION = "r6-product-story-package-v1"


def build_r6_product_story_package(
    *,
    artifact_id: str,
    run_id: str,
    scenario_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    scenario_intake = scenario_intake or build_r6_product_scenario_intake(
        artifact_id=f"{artifact_id}-scenario-intake",
        run_id=run_id,
    )
    _validate_scenario_intake(scenario_intake)
    gap_closure = build_r6_gap_closure_report(
        artifact_id=f"{artifact_id}-gap-closure-report",
        run_id=run_id,
    )
    evidence_cards = build_r6_product_evidence_cards(
        artifact_id=f"{artifact_id}-product-evidence-cards",
        run_id=run_id,
        gap_closure_report=gap_closure,
    )
    evidence_report = build_r6_evidence_report(
        artifact_id=f"{artifact_id}-evidence-report",
        run_id=run_id,
    )
    card_ids = [card["card_id"] for card in evidence_cards["cards"]]
    report = {
        "schema_version": R6_PRODUCT_STORY_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "product_story_package_ready_guarded",
        "sections": [
            "scenario",
            "static_prior_baseline",
            "interaction_risk_shift",
            "evidence_cards",
            "gap_closure",
            "blocked_claims",
            "next_measurement_plan",
        ],
        "scenario_summary": {
            "scenario_id": scenario_intake["scenario"]["scenario_id"],
            "decision_question": scenario_intake["scenario"]["decision_question"],
            "domain_binding": scenario_intake["scenario"]["domain_binding"],
        },
        "evidence_card_ids": card_ids,
        "ui_contract": {
            "static_narrative_fallback_allowed": False,
            "all_customer_visible_claims_require_source_artifact": True,
            "render_only_declared_display_fields": True,
        },
        "blocked_claims": sorted(
            {
                claim
                for card in evidence_cards["cards"]
                for claim in card["blocked_claims"]
            }
        ),
        "source_refs": [
            scenario_intake["artifact_id"],
            evidence_cards["artifact_id"],
            evidence_report["artifact_id"],
            gap_closure["artifact_id"],
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_story_package(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_story_package(**kwargs))


def _validate_scenario_intake(report: dict[str, Any]) -> None:
    if report.get("schema_version") != "r6-product-scenario-intake-v1":
        raise ValueError("scenario_intake.schema_version must be r6-product-scenario-intake-v1")
    if report.get("status") != "scenario_intake_ready":
        raise ValueError("scenario_intake.status must be scenario_intake_ready")
    non_empty_string(report.get("artifact_id"), field="scenario_intake.artifact_id")
    scenario = report.get("scenario")
    if not isinstance(scenario, dict):
        raise ValueError("scenario_intake.scenario must be an object")
    non_empty_string(scenario.get("decision_question"), field="scenario.decision_question")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_story_package(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(json.dumps({"artifact_id": report["artifact_id"], "output": str(output_path), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_story_package.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add experiments/r6_product_story_package.py tests/test_r6_product_story_package.py
git commit -m "feat: add R6 product story package"
```

---

### Task 4: Customer Decision Report

**Files:**
- Create: `experiments/r6_product_decision_report.py`
- Create: `tests/test_r6_product_decision_report.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_r6_product_decision_report.py`:

```python
import json

from experiments.r6_product_decision_report import build_r6_product_decision_report


def test_r6_product_decision_report_exports_customer_readable_guarded_report():
    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
    )

    assert report["schema_version"] == "r6-product-decision-report-v1"
    assert report["status"] == "decision_report_ready_guarded"
    assert report["customer_sections"] == [
        "what_changed",
        "who_is_at_risk",
        "why_risk_moved",
        "what_is_supported_by_evidence",
        "what_is_blocked",
        "what_to_measure_next",
    ]
    assert report["report_contract"]["source_backed_only"] is True
    assert report["report_contract"]["static_narrative_fallback_allowed"] is False
    assert "field validation 已完成" in report["blocked_claims"]
    assert "runtime default 可以开启" in report["blocked_claims"]
    assert report["next_measurement_plan"]
    json.dumps(report, allow_nan=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_decision_report.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_product_decision_report'`.

- [ ] **Step 3: Implement decision report**

Create `experiments/r6_product_decision_report.py`:

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
from experiments.r6_product_story_package import build_r6_product_story_package


R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION = "r6-product-decision-report-v1"


def build_r6_product_decision_report(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    story_package = build_r6_product_story_package(
        artifact_id=f"{artifact_id}-story-package",
        run_id=run_id,
    )
    report = {
        "schema_version": R6_PRODUCT_DECISION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "decision_report_ready_guarded",
        "customer_sections": [
            "what_changed",
            "who_is_at_risk",
            "why_risk_moved",
            "what_is_supported_by_evidence",
            "what_is_blocked",
            "what_to_measure_next",
        ],
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "customer_visible_claims_require_source_artifact": True,
        },
        "display_sources": {
            "scenario": "story_package.scenario_summary",
            "evidence_cards": "story_package.evidence_card_ids",
            "blocked_claims": "story_package.blocked_claims",
        },
        "blocked_claims": story_package["blocked_claims"],
        "next_measurement_plan": [
            "define release measurement window",
            "collect segment-level outcome proxy",
            "compare static prior, interaction shift, and observed outcome",
            "run outcome review before accepting updates",
        ],
        "source_refs": [story_package["artifact_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_decision_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_decision_report(**kwargs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_decision_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(json.dumps({"artifact_id": report["artifact_id"], "output": str(output_path), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify Task 4**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_decision_report.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit Task 4**

Run:

```bash
git add experiments/r6_product_decision_report.py tests/test_r6_product_decision_report.py
git commit -m "feat: add R6 product decision report"
```

---

### Task 5: Outcome Review Contract

**Files:**
- Create: `experiments/r6_product_outcome_review.py`
- Create: `tests/test_r6_product_outcome_review.py`

- [ ] **Step 1: Write the failing test**

Add `tests/test_r6_product_outcome_review.py`:

```python
import json

from experiments.r6_product_outcome_review import build_r6_product_outcome_review


def test_r6_product_outcome_review_keeps_learning_bounded():
    review = build_r6_product_outcome_review(
        artifact_id="r6-product-outcome-review-test",
        run_id="r6-product-first-run",
        observed_outcome={
            "outcome_id": "airline-fee-outcome-001",
            "measurement_window": "post_release_30d",
            "observed_signal": "churn_risk_higher_than_static_prior",
            "source_level": "field_proxy",
        },
    )

    assert review["schema_version"] == "r6-product-outcome-review-v1"
    assert review["status"] == "outcome_review_ready_update_blocked"
    assert review["review_outputs"] == [
        "static_prior_error",
        "interaction_error",
        "risk_signal_classification",
        "error_attribution",
        "candidate_update",
        "update_gate",
    ]
    assert review["update_gate"]["candidate_update_generated"] is True
    assert review["update_gate"]["runtime_default_allowed"] is False
    assert review["update_gate"]["requires_holdout_before_default"] is True
    assert "same_outcome_review_not_global_validation" in review["risk_flags"]
    json.dumps(review, allow_nan=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_outcome_review.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'experiments.r6_product_outcome_review'`.

- [ ] **Step 3: Implement outcome review**

Create `experiments/r6_product_outcome_review.py`:

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


R6_PRODUCT_OUTCOME_REVIEW_SCHEMA_VERSION = "r6-product-outcome-review-v1"


def build_r6_product_outcome_review(
    *,
    artifact_id: str,
    run_id: str,
    observed_outcome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    outcome = _normalize_outcome(observed_outcome or _default_observed_outcome())
    report = {
        "schema_version": R6_PRODUCT_OUTCOME_REVIEW_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "outcome_review_ready_update_blocked",
        "observed_outcome": outcome,
        "review_outputs": [
            "static_prior_error",
            "interaction_error",
            "risk_signal_classification",
            "error_attribution",
            "candidate_update",
            "update_gate",
        ],
        "error_attribution": {
            "static_prior_miss": "requires_metric_computation",
            "interaction_over_amplification": "requires_segment_outcome",
            "outcome_mapping_noise": "requires_source_review",
        },
        "update_gate": {
            "candidate_update_generated": True,
            "runtime_default_allowed": False,
            "requires_holdout_before_default": True,
        },
        "risk_flags": [
            "same_outcome_review_not_global_validation",
            "field_or_proxy_source_requires_audit",
        ],
        "source_refs": [outcome["outcome_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_outcome_review(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_outcome_review(**kwargs))


def _default_observed_outcome() -> dict[str, Any]:
    return {
        "outcome_id": "generic-outcome-review-001",
        "measurement_window": "post_release_30d",
        "observed_signal": "risk_signal_requires_review",
        "source_level": "field_proxy",
    }


def _normalize_outcome(outcome: dict[str, Any]) -> dict[str, str]:
    if not isinstance(outcome, dict):
        raise ValueError("observed_outcome must be an object")
    return {
        "outcome_id": non_empty_string(outcome.get("outcome_id"), field="observed_outcome.outcome_id"),
        "measurement_window": non_empty_string(outcome.get("measurement_window"), field="observed_outcome.measurement_window"),
        "observed_signal": non_empty_string(outcome.get("observed_signal"), field="observed_outcome.observed_signal"),
        "source_level": non_empty_string(outcome.get("source_level"), field="observed_outcome.source_level"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r6_product_outcome_review(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(json.dumps({"artifact_id": report["artifact_id"], "output": str(output_path), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify Task 5**

Run:

```bash
.venv/bin/python -m pytest tests/test_r6_product_outcome_review.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
git add experiments/r6_product_outcome_review.py tests/test_r6_product_outcome_review.py
git commit -m "feat: add R6 product outcome review"
```

---

### Task 6: Current Artifacts and State Update

**Files:**
- Create artifacts under `experiments/results/r6_product_readiness_index/`
- Create artifacts under `experiments/results/r6_product_scenario_intake/`
- Create artifacts under `experiments/results/r6_product_story_package/`
- Create artifacts under `experiments/results/r6_product_decision_report/`
- Create artifacts under `experiments/results/r6_product_outcome_review/`
- Modify: `docs/CURRENT_STATE.md`

- [ ] **Step 1: Generate current artifacts**

Run:

```bash
mkdir -p experiments/results/r6_product_readiness_index experiments/results/r6_product_scenario_intake experiments/results/r6_product_story_package experiments/results/r6_product_decision_report experiments/results/r6_product_outcome_review
.venv/bin/python experiments/r6_product_readiness_index.py --artifact-id r6-product-readiness-index-current-001 --run-id r6-product-first-current-001 --output experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json
.venv/bin/python experiments/r6_product_scenario_intake.py --artifact-id r6-product-scenario-intake-current-001 --run-id r6-product-first-current-001 --output experiments/results/r6_product_scenario_intake/r6-product-scenario-intake-current-001.json
.venv/bin/python experiments/r6_product_story_package.py --artifact-id r6-product-story-package-current-001 --run-id r6-product-first-current-001 --output experiments/results/r6_product_story_package/r6-product-story-package-current-001.json
.venv/bin/python experiments/r6_product_decision_report.py --artifact-id r6-product-decision-report-current-001 --run-id r6-product-first-current-001 --output experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json
.venv/bin/python experiments/r6_product_outcome_review.py --artifact-id r6-product-outcome-review-current-001 --run-id r6-product-first-current-001 --output experiments/results/r6_product_outcome_review/r6-product-outcome-review-current-001.json
```

Expected: each command prints JSON with `output` and `status`.

- [ ] **Step 2: Update current state**

Append to `docs/CURRENT_STATE.md`:

```markdown
43. 项目目标已调整为 Product-first：Research 不再默认冲 CCF-A 主贡献，而是作为理论、证据边界、误差归因和方法护栏；Product 是主交付目标，后续必须补齐 scenario intake、story package、decision report 和 outcome review 闭环。
44. Product 下一阶段验收不是 demo 文案，而是 source-backed artifact/API contract：所有客户可见 claim 必须绑定 source artifact，`static_narrative_fallback_allowed=false` 继续保持。
```

- [ ] **Step 3: Verify all Product-first work**

Run:

```bash
.venv/bin/python -m py_compile experiments/r6_product_readiness_index.py experiments/r6_product_scenario_intake.py experiments/r6_product_story_package.py experiments/r6_product_decision_report.py experiments/r6_product_outcome_review.py
.venv/bin/python -m pytest tests/test_r6_product_readiness_index.py tests/test_r6_product_scenario_intake.py tests/test_r6_product_story_package.py tests/test_r6_product_decision_report.py tests/test_r6_product_outcome_review.py -q
.venv/bin/python -m pytest tests/test_r6_*.py -q
git diff --check
```

Expected:

- py_compile exits 0.
- new Product-first tests pass.
- all R6 tests pass.
- git diff check has no output.

- [ ] **Step 4: Commit Task 6**

Run:

```bash
git add docs/CURRENT_STATE.md
git add -f experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json experiments/results/r6_product_scenario_intake/r6-product-scenario-intake-current-001.json experiments/results/r6_product_story_package/r6-product-story-package-current-001.json experiments/results/r6_product_decision_report/r6-product-decision-report-current-001.json experiments/results/r6_product_outcome_review/r6-product-outcome-review-current-001.json
git commit -m "data: add R6 product-first current artifacts"
```

---

## 验收标准

完成本计划后，项目必须满足：

1. Product 有结构化 scenario intake，不依赖固定 demo。
2. Product 有 story package，UI/报告可直接消费。
3. Product 有客户决策报告 contract，不靠自由文案补结论。
4. Product 有 outcome review contract，真实结果回流后能复盘并生成 bounded update。
5. Research 继续保留理论与 gate 价值，但不再以 CCF-A readiness 作为默认目标。
6. 所有客户可见结论继续绑定 artifact source、claim boundary 和 blocked claims。
