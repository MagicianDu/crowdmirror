import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_field_slice_intake_preview_accepts_valid_csv_and_jsonl(tmp_path):
    script = _node_harness(
        """
        const csv = [
          "case_id,segment_id,scenario_id,prediction_share_or_score,observed_outcome,outcome_timestamp,customer_approval_reference",
          ...Array.from({ length: 10 }, (_, idx) =>
            `case-${idx},segment-${idx % 3},scenario-001,0.${idx + 1},0.${idx + 2},2026-07-15T00:00:00Z,approval-2026-06-27`
          ),
        ].join("\\n");
        const csvPreview = validateCustomerFieldSliceText(csv, "customer-slice.csv");
        assert.equal(csvPreview.status, "customer_field_slice_intake_preview_ready_for_revalidation");
        assert.equal(csvPreview.acceptance_gates.ready_for_revalidation, true);
        assert.equal(csvPreview.acceptance_gates.metrics_computed, false);
        assert.equal(csvPreview.acceptance_gates.field_outcome_validated, false);
        assert.equal(csvPreview.acceptance_gates.product_default_allowed, false);
        assert.equal(csvPreview.acceptance_gates.runtime_default_allowed, false);
        assert.equal(csvPreview.validation_summary.case_count, 10);
        assert.deepEqual(csvPreview.validation_summary.missing_required_fields, []);
        assert.deepEqual(csvPreview.validation_errors, []);
        assert.equal(
          csvPreview.next_required_artifact,
          "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice",
        );
        const handoffHtml = renderCustomerFieldSliceRevalidationHandoff(csvPreview);
        assert.ok(handoffHtml.includes("r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice"));
        assert.ok(handoffHtml.includes("operator_command"));
        assert.ok(handoffHtml.includes("experiments/r12_customer_field_slice_intake_validation.py"));
        assert.ok(handoffHtml.includes("CUSTOMER_FIELD_SLICE_PATH"));
        assert.ok(handoffHtml.includes("r12-customer-field-slice-handoff-package-current-001.json"));
        assert.ok(handoffHtml.includes("r12-customer-field-slice-intake-validation-customer-001.json"));
        assert.ok(handoffHtml.includes("metrics_computed=false"));
        assert.ok(handoffHtml.includes("field_outcome_validated=false"));
        assert.ok(handoffHtml.includes("runtime_default_allowed=false"));

        const jsonl = Array.from({ length: 10 }, (_, idx) =>
          JSON.stringify({
            case_id: `jsonl-case-${idx}`,
            segment_id: `segment-${idx % 2}`,
            scenario_id: "scenario-001",
            prediction_share_or_score: `0.${idx + 1}`,
            observed_outcome: `0.${idx + 2}`,
            outcome_timestamp: "2026-07-15T00:00:00Z",
            customer_approval_reference: "approval-2026-06-27",
          })
        ).join("\\n");
        const jsonlPreview = validateCustomerFieldSliceText(jsonl, "customer-slice.jsonl");
        assert.equal(jsonlPreview.acceptance_gates.ready_for_revalidation, true);
        assert.equal(jsonlPreview.validation_summary.case_count, 10);
        """
    )
    _run_node(script, tmp_path)


def test_frontend_field_slice_intake_preview_blocks_contract_privacy_and_parse_errors(
    tmp_path,
):
    script = _node_harness(
        """
        const csv = [
          "case_id,segment_id,scenario_id,prediction_share_or_score,outcome_timestamp,customer_approval_reference,email",
          ...Array.from({ length: 10 }, (_, idx) => {
            const caseId = idx === 1 ? "case-0" : `case-${idx}`;
            const prediction = idx === 2 ? "not-a-number" : `0.${idx + 1}`;
            const timestamp = idx === 3 ? "not-a-timestamp" : "2026-07-15T00:00:00Z";
            const approval = idx === 4 ? "" : "approval-2026-06-27";
            return `${caseId},segment-${idx % 3},scenario-001,${prediction},${timestamp},${approval},user-${idx}@example.com`;
          }),
        ].join("\\n");
        const preview = validateCustomerFieldSliceText(csv, "customer-slice.csv");
        assert.equal(preview.status, "customer_field_slice_intake_preview_blocked_contract_or_privacy");
        assert.equal(preview.acceptance_gates.ready_for_revalidation, false);
        assert.equal(preview.acceptance_gates.privacy_valid, false);
        assert.equal(preview.acceptance_gates.numeric_fields_valid, false);
        assert.equal(preview.acceptance_gates.timestamps_valid, false);
        assert.equal(preview.acceptance_gates.duplicate_case_ids_absent, false);
        assert.equal(preview.acceptance_gates.customer_approval_present, false);
        assert.equal(preview.acceptance_gates.product_default_allowed, false);
        assert.equal(preview.acceptance_gates.runtime_default_allowed, false);
        assert.deepEqual(preview.validation_summary.missing_required_fields, ["observed_outcome"]);
        assert.deepEqual(preview.validation_summary.direct_pii_columns, ["email"]);
        assert.deepEqual(preview.validation_summary.duplicate_case_ids, ["case-0"]);
        const codes = new Set(preview.validation_errors.map((error) => error.code));
        assert.ok(codes.has("missing_required_fields"));
        assert.ok(codes.has("customer_approval_reference_missing"));
        assert.ok(codes.has("direct_pii_columns_present"));
        assert.ok(codes.has("direct_pii_values_present"));
        assert.ok(codes.has("numeric_field_parse_failed"));
        assert.ok(codes.has("timestamp_parse_failed"));
        assert.ok(codes.has("duplicate_case_id"));
        assert.equal(preview.next_required_artifact, "corrected_customer_field_slice");
        """
    )
    _run_node(script, tmp_path)


def _node_harness(assertions: str) -> str:
    app_path = ROOT / "demo" / "app.js"
    return f"""
    const assert = require("assert");
    const fs = require("fs");
    const vm = require("vm");
    const context = {{
      console,
      document: {{ getElementById: () => ({{ innerHTML: "" }}) }},
      window: {{ addEventListener: () => {{}} }},
      fetch: async () => {{ throw new Error("fetch not expected"); }},
    }};
    vm.createContext(context);
    vm.runInContext(fs.readFileSync({str(app_path)!r}, "utf8"), context);
    assert.equal(typeof context.validateCustomerFieldSliceText, "function");
    assert.equal(typeof context.renderCustomerFieldSliceRevalidationHandoff, "function");
    const validateCustomerFieldSliceText = context.validateCustomerFieldSliceText;
    const renderCustomerFieldSliceRevalidationHandoff = context.renderCustomerFieldSliceRevalidationHandoff;
    {assertions}
    """


def _run_node(script: str, tmp_path: Path) -> None:
    script_path = tmp_path / "field-slice-intake-check.js"
    script_path.write_text(script)
    completed = subprocess.run(
        ["node", str(script_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
