import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def test_r6_product_frontend_assets_exist_and_bind_current_artifacts():
    html = (DEMO / "index.html").read_text()
    js = (DEMO / "app.js").read_text()

    assert 'id="app"' in html
    assert "styles.css" in html
    assert "app.js" in html

    expected_artifact_paths = [
        (
            "../experiments/results/r6_product_customer_value_report/"
            "r6-product-customer-value-report-current-001.json"
        ),
        (
            "../experiments/results/r6_research_product_value_support/"
            "r6-research-product-value-support-current-001.json"
        ),
        (
            "../experiments/results/r6_product_readiness_index/"
            "r6-product-readiness-index-current-001.json"
        ),
        (
            "../experiments/results/r6_product_api_manifest/"
            "r6-product-api-manifest-current-001.json"
        ),
    ]
    for path in expected_artifact_paths:
        assert path in js

    expected_sections = [
        "趋势方向",
        "风险区间",
        "风险分布",
        "异常群体",
        "机制解释",
        "研究支撑",
        "试运行工作台",
        "客户 field slice 校验",
        "客户试运行",
        "R12 迁移验证",
        "证据边界",
        "阻断声明",
        "数据来源",
    ]
    for section in expected_sections:
        assert section in js


def test_r6_product_promo_page_explains_public_data_trial_scope():
    html = (DEMO / "promo.html").read_text()
    js = (DEMO / "promo.js").read_text()
    css = (DEMO / "styles.css").read_text()

    assert "人群反应趋势与风险区间模拟器" in html
    assert "公开数据验证版企业试用" in html
    assert "promo-evidence-map.png" in html
    assert "打开产品 demo" in html
    assert "查看证据 JSON" in html

    assert "../experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json" in js
    assert "../experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json" in js
    assert 'href="../experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json"' in html
    assert 'href="../experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json"' in html
    assert "public_data_effectiveness_claim_allowed" in js
    assert "tested_effective_on_public_data_guarded" in js
    assert "离线校准与自优化候选" in js
    assert "人工确认后进入试用流程" in js
    assert "runtime_default_allowed" in js

    assert ".promo-hero" in css
    assert "promo-evidence-map.png" in css
    assert ".promo-capability-grid" in css
    assert ".promo-workflow" in css

    assert "精准预测系统" not in html
    assert "自动上线校准更新" not in html


def test_github_pages_public_links_and_relative_artifact_paths():
    readme = (ROOT / "README.md").read_text()
    root_index = ROOT / "index.html"
    nojekyll = ROOT / ".nojekyll"
    app_js = (DEMO / "app.js").read_text()
    promo_js = (DEMO / "promo.js").read_text()
    promo_html = (DEMO / "promo.html").read_text()

    assert root_index.exists()
    assert nojekyll.exists()
    assert "https://magiciandu.github.io/crowdmirror/demo/promo.html" in readme
    assert "https://magiciandu.github.io/crowdmirror/demo/" in readme
    assert not re.search(r"\]\(http://127\.0\.0\.1:8088/demo/promo\.html\)", readme)
    assert not re.search(r"\]\(http://127\.0\.0\.1:8088/demo/\)", readme)

    assert '"/experiments/' not in app_js
    assert '"/experiments/' not in promo_js
    assert 'href="/experiments/' not in promo_html
    assert "../experiments/results/" in app_js
    assert "../experiments/results/" in promo_js
    assert "../experiments/results/" in promo_html


def test_r6_product_frontend_is_source_backed_and_fail_closed():
    html = (DEMO / "index.html").read_text()
    js = (DEMO / "app.js").read_text()

    assert "static_narrative_fallback_allowed" in js
    assert "renderLoadError" in js
    assert "不展示静态兜底结论" in js
    assert "sourceRefs" in js
    assert "blockedClaims" in js
    assert "supportGapLedger" in js
    assert "researchNextTasks" in js
    assert "r12_transfer_evidence" in js
    assert "public_data_validation_scope" in js
    assert "public_data_effectiveness_claim_allowed" in js
    assert "customer_field_validation_required_for_current_stage" in js
    assert "tested_effective_on_public_data_guarded" in js
    assert "本阶段验证范围" in js
    assert "公开数据有效声明" in js
    assert "renderCustomerWorkflowWorkbench(r12TransferEvidence, apiManifest)" in js
    assert "customer-workflow-panel" in js
    assert "试运行工作台" in js
    assert "场景输入" in js
    assert "群体与先验" in js
    assert "运行闸门" in js
    assert "报告导出" in js
    assert "outcome review" in js
    assert "scenario_intake_status" in js
    assert "population_prior_status" in js
    assert "simulation_run_gate_status" in js
    assert "report_export_status" in js
    assert "outcome_review_status" in js
    assert "customer_field_slice_template_generated" in js
    assert "launch_packet_export_ready" in js
    assert "field_or_pre_outcome_revalidation_ready" in js
    assert "primary_decision_source" in js
    assert "renderCustomerFieldSliceIntakePanel(r12TransferEvidence)" in js
    assert "field-slice-intake-panel" in js
    assert "客户 field slice 校验" in js
    assert "customer-field-slice-input" in js
    assert "validateCustomerFieldSliceText" in js
    assert "customer_field_slice_intake_preview_ready_for_revalidation" in js
    assert "customer_field_slice_intake_preview_blocked_contract_or_privacy" in js
    assert "direct_pii_columns_present" in js
    assert "duplicate_case_id" in js
    assert "numeric_field_parse_failed" in js
    assert "timestamp_parse_failed" in js
    assert "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice" in js
    assert "customer-field-slice-revalidation-handoff" in js
    assert "customer-field-slice-handoff-output" in js
    assert "renderCustomerFieldSliceRevalidationHandoff" in js
    assert "revalidation_handoff_status" in js
    assert "operator_command" in js
    assert "customerFieldSliceOperatorCommand" in js
    assert "experiments/r12_customer_field_slice_intake_validation.py" in js
    assert "CUSTOMER_FIELD_SLICE_PATH" in js
    assert "CUSTOMER_FIELD_SLICE_INTAKE_TIMESTAMP" in js
    assert "blocked_until_valid_customer_slice" in js
    assert "ready_for_operator_review" in js
    assert "触发 revalidation handoff" in js
    assert "renderCustomerTrialActionPanel(r12TransferEvidence)" in js
    assert "customer-trial-action-panel" in js
    assert "客户下一步" in js
    assert "collect_customer_field_slice_or_wait_for_target_outcome" in js
    assert "update_transfer_gain" in js
    assert "extended_product_metric_support_level" in js
    assert "static_prior_miss_recovery_holdout_covered" in js
    assert "high_risk_holdout_boundary" in js
    assert "research_recoverable_static_prior_miss_count" in js
    assert "product_default_low_sensitive_high_risk_holdout_present" in js
    assert "research_only_until_low_sensitive_or_customer_approved_holdout" in js
    assert "high_risk_replay_boundary" in js
    assert "mean_absolute_error_delta" in js
    assert "static_prior_miss_recovery_delta" in js
    assert "abnormal_segment_recall_delta" in js
    assert "r12_high_risk_replay_mae_positive_recall_flat_research_only" in js
    assert "recall_oriented_update_boundary" in js
    assert "recommended_activation_margin" in js
    assert "false_alarm_rate_delta" in js
    assert "precision_delta" in js
    assert "r12_recall_update_holdout_false_alarm_stress_test" in js
    assert "recall_false_alarm_stress_boundary" in js
    assert "dominant_false_alarm_segment_column" in js
    assert "protected_sensitive_false_alarm_rate_delta" in js
    assert "low_sensitive_recall_evaluable" in js
    assert "r12_recall_false_alarm_mitigation_candidate" in js
    assert "recall_false_alarm_mitigation_boundary" in js
    assert "mitigated_false_alarm_rate_delta" in js
    assert "l7_recall_gain_retained" in js
    assert "high_current_false_alarm_band_derived" in js
    assert "r12_recall_mitigation_holdout_validation" in js
    assert "recall_mitigation_holdout_validation_boundary" in js
    assert "leave_one_pass_rate" in js
    assert "endpoint_holdout_failure_count" in js
    assert "r12_recall_mitigation_independent_holdout_data" in js
    assert "recall_mitigation_independent_holdout_data_boundary" in js
    assert "same_dataset_non_derivation_recall_candidate_count" in js
    assert "external_registry_candidate_count" in js
    assert "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice" in js
    assert (
        "recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary"
        in js
    )
    assert "preferred_external_source_id" in js
    assert "raw_external_or_customer_slice_present" in js
    assert "r12_external_or_customer_holdout_raw_slice" in js
    assert "external_or_customer_holdout_raw_slice_boundary" in js
    assert "actual_public_data_ingested" in js
    assert "total_observed_complaint_cases" in js
    assert "r12_recall_mitigation_external_holdout_revalidation" in js
    assert "recall_mitigation_external_holdout_revalidation_boundary" in js
    assert "external_holdout_revalidation_passed" in js
    assert "same_table_prediction_leakage_risk" in js
    assert "risk_ranking_quality_delta" in js
    assert "r12_pre_outcome_or_independent_prediction_packet" in js
    assert "pre_outcome_or_independent_prediction_packet_boundary" in js
    assert "hindcast_independent_revalidation_ready" in js
    assert "prediction_lock_timestamp_pre_target_outcome" in js
    assert "r12_independent_hindcast_revalidation" in js
    assert "independent_hindcast_revalidation_boundary" in js
    assert "hindcast_independent_revalidation_passed" in js
    assert "decision_value_delta" in js
    assert "r12_pre_outcome_prediction_trial_or_customer_field_revalidation" in js
    assert (
        "pre_outcome_prediction_trial_or_customer_field_revalidation_boundary"
        in js
    )
    assert "prediction_lock_timestamp_pre_target_outcome" in js
    assert "target_outcome_artifact_present" in js
    assert "r12_pre_outcome_or_customer_field_outcome_ingestion" in js
    assert "pre_outcome_or_customer_field_outcome_ingestion_boundary" in js
    assert "target_public_outcome_available" in js
    assert "field_or_pre_outcome_revalidation_ready" in js
    assert "r12_pre_outcome_or_customer_field_outcome_revalidation" in js
    assert "pre_outcome_or_customer_field_outcome_revalidation_boundary" in js
    assert "field_or_pre_outcome_revalidation_passed" in js
    assert "metrics_computed" in js
    assert "r12_target_outcome_or_customer_field_slice_arrival" in js
    assert "target_outcome_or_customer_field_slice_arrival_boundary" in js
    assert "outcome_source_arrived" in js
    assert "r12_customer_field_slice_handoff_package" in js
    assert "customer_field_slice_handoff_package_boundary" in js
    assert "customer_data_request_ready" in js
    assert "r12-customer-field-slice-template-current-001.csv" in js
    assert "r12_customer_field_slice_intake_validation" in js
    assert "customer_field_slice_intake_validation_boundary" in js
    assert "ready_for_revalidation" in js
    assert "privacy_valid" in js
    assert "r12_customer_field_slice_revalidation" in js
    assert "customer_field_slice_revalidation_boundary" in js
    assert "field_outcome_validated" in js
    assert "mean_absolute_error" in js
    assert "r12_customer_field_outcome_feedback_update" in js
    assert "customer_field_outcome_feedback_update_boundary" in js
    assert "candidate_count" in js
    assert "prompt_or_persona_manual_patch_allowed" in js
    assert "r12_customer_feedback_update_shadow_replay" in js
    assert "customer_feedback_update_shadow_replay_boundary" in js
    assert "shadow_replay_executed" in js
    assert "accepted_candidate_count" in js
    assert "r12_customer_feedback_shadow_replay_holdout_review" in js
    assert "customer_feedback_shadow_replay_holdout_review_boundary" in js
    assert "holdout_review_executed" in js
    assert "independent_holdout_case_count" in js
    assert "r12_customer_validation_workflow_status" in js
    assert "customer_validation_workflow_status_boundary" in js
    assert "current_stage" in js
    assert "next_action" in js
    assert "source_arrived" in js
    assert "r12_customer_trial_readiness_package" in js
    assert "customer_trial_readiness_package_boundary" in js
    assert "trial_package_status" in js
    assert "template_output_path" in js
    assert "minimum_case_count" in js
    assert "r12_customer_trial_operational_check" in js
    assert "customer_trial_operational_check_boundary" in js
    assert "operational_check_status" in js
    assert "customer_trial_request_operationally_ready" in js
    assert "source_registry_resolvable" in js
    assert "operator_runbook_declared" in js
    assert "r12_customer_trial_launch_handoff_package" in js
    assert "customer_trial_launch_handoff_package_boundary" in js
    assert "launch_package_status" in js
    assert "launch_handoff_ready" in js
    assert "r12_customer_trial_launch_packet_export" in js
    assert "customer_trial_launch_packet_export_boundary" in js
    assert "packet_export_status" in js
    assert "markdown_export_written" in js
    assert "markdown_output_path" in js
    assert "artifactPathToHref(customerTrialPacketExport.markdown_output_path)" in js
    assert "打开 launch packet" in js
    assert "r12_customer_trial_launch_bundle_verification" in js
    assert "customer_trial_launch_bundle_verification_boundary" in js
    assert "bundle_verification_status" in js
    assert "launch_bundle_verified" in js
    assert "resolved_required_item_count" in js
    assert "r12_customer_field_slice_operator_rehearsal" in js
    assert "customer_field_slice_operator_rehearsal_boundary" in js
    assert "operator_rehearsal_status" in js
    assert "operator_command_rehearsed" in js
    assert "sample_slice_ready_for_revalidation" in js
    assert "real_customer_field_slice_submitted" in js
    assert "r12_customer_feedback_loop_operator_rehearsal" in js
    assert "customer_feedback_loop_operator_rehearsal_boundary" in js
    assert "feedback_loop_rehearsal_status" in js
    assert "l22_intake_validator_executed" in js
    assert "l23_field_revalidation_executed" in js
    assert "l24_feedback_candidates_generated" in js
    assert "l25_shadow_replay_executed" in js
    assert "l26_synthetic_holdout_review_executed" in js
    assert "r12_customer_trial_evidence_ledger" in js
    assert "customer_trial_evidence_ledger_boundary" in js
    assert "ledger_status" in js
    assert "customer_visible_readiness_evidence_count" in js
    assert "operator_only_rehearsal_evidence_count" in js
    assert "blocking_gap_count" in js
    assert "customer_trial_evidence_ledger_ready" in js
    assert "secondary_transfer_evidence_card_only" in js
    assert "/r6/product/r12-transfer-evidence" in js

    assert "精准预测系统" not in html
    assert "系统可以精确预测单点结果" not in html
    assert "field validation 已完成" not in html
    assert "runtime default 可以开启" not in html


def test_r6_product_frontend_css_is_responsive_and_stable():
    css = (DEMO / "styles.css").read_text()

    assert "@media (max-width:" in css
    assert "grid-template-columns" in css
    assert "minmax(" in css
    assert re.search(r"border-radius:\s*(6|8)px", css)
    assert not re.search(r"font-size:\s*[^;]*vw", css)
    assert not re.search(r"letter-spacing:\s*-\d", css)
