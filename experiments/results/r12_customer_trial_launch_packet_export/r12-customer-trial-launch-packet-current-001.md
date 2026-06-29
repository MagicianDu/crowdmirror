# 客户试运行数据回流请求

- request_id: r12_customer_field_slice_submission_request
- minimum_case_count: 10
- required_fields: case_id, segment_id, scenario_id, prediction_share_or_score, observed_outcome, outcome_timestamp, customer_approval_reference

## 字段模板

- template_path: experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-template-current-001.csv

## 审批与隐私边界

- approval_reference_required: True
- direct_personal_identifiers_allowed: False
- manual_approval_points:
- customer_approval_reference_required_before_intake
- governed_review_required_after_holdout_review

## 提交后操作步骤

- first_operator_step: intake_validation
- first_operator_command: .venv/bin/python experiments/r12_customer_field_slice_intake_validation.py --customer-field-slice-path <customer-slice.csv>
- operator_step_ids:
- intake_validation
- field_revalidation
- feedback_update_candidate
- shadow_replay
- holdout_review

## 阻断声明

- field validation 尚未完成
- customer field validation passed 不能声明
- Product default 和 runtime default 仍保持关闭
