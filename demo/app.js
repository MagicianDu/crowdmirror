const ARTIFACTS = {
  customerValueReport:
    "../experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json",
  valueSupport:
    "../experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json",
  readinessIndex:
    "../experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json",
  apiManifest:
    "../experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json",
};

const SECTION_LABELS = [
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
];

const CASE_NAMES = {
  htops_cost_pressure: "HTOPS 成本压力",
  anes_health_heldout: "ANES 医疗政策 holdout",
  anes_climate_heldout: "ANES 气候政策 holdout",
};

const SUPPORT_LABELS = {
  customer_value_report_ready_guarded: "有护栏可展示",
  product_first_readiness_partial: "产品就绪度部分通过",
  product_value_support_partial: "研究支撑部分成立",
  product_api_manifest_ready_guarded: "API 合同有护栏",
  partial_current_proxy: "公共 proxy 部分支持",
  partial_high_false_alarm: "部分支持但误报高",
  diagnostic_only: "仅诊断",
  blocked_until_holdout_or_field_outcome: "等待 holdout 或真实 outcome",
  guarded_transfer_positive_secondary_evidence: "迁移信号有护栏",
  product_secondary_evidence_only: "仅次级证据",
};

const CUSTOMER_FIELD_SLICE_REQUIRED_FIELDS = [
  "case_id",
  "segment_id",
  "scenario_id",
  "prediction_share_or_score",
  "observed_outcome",
  "outcome_timestamp",
  "customer_approval_reference",
];

const CUSTOMER_FIELD_SLICE_MINIMUM_CASE_COUNT = 10;
const CUSTOMER_FIELD_SLICE_DIRECT_PII_COLUMNS = new Set([
  "address",
  "email",
  "full_name",
  "id_card",
  "name",
  "passport",
  "phone",
  "ssn",
]);
const CUSTOMER_FIELD_SLICE_EMAIL_PATTERN = /[^@\s]+@[^@\s]+\.[^@\s]+/;

const app = document.getElementById("app");

window.addEventListener("DOMContentLoaded", () => {
  loadArtifacts()
    .then(renderApp)
    .catch((error) => renderLoadError(error));
});

async function loadArtifacts() {
  const entries = await Promise.all(
    Object.entries(ARTIFACTS).map(async ([key, path]) => {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${key} artifact 加载失败: ${response.status}`);
      }
      return [key, await response.json()];
    }),
  );
  const artifacts = Object.fromEntries(entries);
  validateSourceBackedContract(artifacts.customerValueReport);
  return artifacts;
}

function validateSourceBackedContract(report) {
  const contract = report.report_contract || {};
  if (contract.static_narrative_fallback_allowed !== false) {
    throw new Error("static_narrative_fallback_allowed 必须为 false");
  }
  if (contract.source_backed_only !== true) {
    throw new Error("source_backed_only 必须为 true");
  }
  if (contract.precise_point_prediction_allowed !== false) {
    throw new Error("precise_point_prediction_allowed 必须为 false");
  }
}

function artifactPathToHref(path) {
  if (typeof path !== "string") return "#";
  const trimmed = path.trim();
  if (!trimmed || trimmed.includes("..") || /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) {
    return "#";
  }
  return `../${trimmed.replace(/^\/+/, "")}`;
}

function renderApp({ customerValueReport, valueSupport, readinessIndex, apiManifest }) {
  const display = customerValueReport.display_payload || {};
  const trend = display.trend_direction || {};
  const interval = display.risk_interval || {};
  const distribution = display.risk_distribution || {};
  const abnormal = display.abnormal_segments || [];
  const researchSupport = display.research_support || valueSupport || {};
  const supportGapLedger =
    researchSupport.support_gap_ledger || valueSupport.support_gap_ledger || [];
  const researchNextTasks =
    researchSupport.research_next_tasks || valueSupport.research_next_tasks || [];
  const r12TransferEvidence = display.r12_transfer_evidence || null;
  const sourceRefs = customerValueReport.source_refs || [];
  const blockedClaims = uniqueItems([
    ...(customerValueReport.blocked_claims || []),
    ...(readinessIndex.blocked_claims || []),
    ...(apiManifest.blocked_claims || []),
  ]);

  app.innerHTML = `
    <section class="report-header">
      <div class="title-block">
        <p class="eyebrow">R6 Product Contract</p>
        <h1>${escapeHtml(customerValueReport.positioning)}</h1>
        <p class="claim-boundary">${escapeHtml(customerValueReport.claim_boundary)}</p>
      </div>
      <div class="status-stack" aria-label="当前状态">
        ${statusPill("报告", customerValueReport.status)}
        ${statusPill("研究支撑", valueSupport.status)}
        ${statusPill("产品就绪", readinessIndex.status)}
        ${statusPill("API", apiManifest.status)}
      </div>
    </section>

    <section class="metric-grid" aria-label="核心指标">
      ${metricCard("趋势方向", formatPercent(trend.summary_metric), trend.support_status, "当前 public proxy 中方向判断命中比例")}
      ${metricCard("风险区间", formatPercent(interval.summary_metric), interval.support_status, "真实 proxy 是否落入模拟区间")}
      ${metricCard("风险排序", formatPercent(distribution.risk_ranking_quality), distribution.support_status, "高风险 case 排序质量")}
      ${metricCard("误报率", formatPercent(distribution.false_alarm_rate), distribution.support_status, "当前外部验证暴露的 false alarm")}
    </section>

    <section class="workbench-grid">
      <article class="panel panel-wide">
        <div class="panel-heading">
          <p class="eyebrow">Decision Signals</p>
          <h2>趋势方向与风险区间</h2>
        </div>
        <div class="case-rows">
          ${(trend.cases || []).map((caseItem) => renderCaseRow(caseItem, interval.cases || [])).join("")}
        </div>
      </article>

      <article class="panel">
        <div class="panel-heading">
          <p class="eyebrow">Risk Distribution</p>
          <h2>风险分布</h2>
        </div>
        ${renderDistribution(distribution)}
      </article>

      <article class="panel panel-wide">
        <div class="panel-heading">
          <p class="eyebrow">Segments</p>
          <h2>异常群体</h2>
        </div>
        <div class="segment-grid">
          ${abnormal.map(renderSegmentGroup).join("")}
        </div>
      </article>

      <article class="panel">
        <div class="panel-heading">
          <p class="eyebrow">Mechanism</p>
          <h2>机制解释</h2>
        </div>
        ${renderMechanism(display.mechanism_explanation)}
      </article>

      <article class="panel panel-wide">
        <div class="panel-heading">
          <p class="eyebrow">Research Support</p>
          <h2>研究支撑</h2>
        </div>
        ${renderResearchSupport(researchSupport, supportGapLedger, researchNextTasks)}
      </article>

      ${renderCustomerWorkflowWorkbench(r12TransferEvidence, apiManifest)}

      ${renderCustomerFieldSliceIntakePanel(r12TransferEvidence)}

      ${renderCustomerTrialActionPanel(r12TransferEvidence)}

      ${renderR12TransferEvidence(r12TransferEvidence)}

      <article class="panel panel-wide">
        <div class="panel-heading">
          <p class="eyebrow">Evidence Boundary</p>
          <h2>证据边界</h2>
        </div>
        ${renderReadiness(readinessIndex.readiness_gates || {})}
      </article>

      <article class="panel">
        <div class="panel-heading">
          <p class="eyebrow">Blocked</p>
          <h2>阻断声明</h2>
        </div>
        ${renderBlockedClaims(blockedClaims)}
      </article>

      <article class="panel panel-wide">
        <div class="panel-heading">
          <p class="eyebrow">Sources</p>
          <h2>数据来源</h2>
        </div>
        ${renderSources(sourceRefs, customerValueReport.source_registry || [], apiManifest.endpoints || [])}
      </article>
    </section>
  `;
  bindCustomerFieldSliceIntakeControls();
}

function renderCustomerFieldSliceIntakePanel(evidence) {
  if (!evidence) return "";
  const summary = evidence.evidence_summary || {};
  const handoff = summary.customer_field_slice_handoff_package_boundary || {};
  const intake = summary.customer_field_slice_intake_validation_boundary || {};
  const operatorRehearsal =
    summary.customer_field_slice_operator_rehearsal_boundary || {};
  const feedbackLoopRehearsal =
    summary.customer_feedback_loop_operator_rehearsal_boundary || {};
  const templatePath =
    handoff.template_output_path || "experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-template-current-001.csv";
  const templateHref = artifactPathToHref(templatePath);
  return `
    <article class="panel panel-wide field-slice-intake-panel">
      <div class="panel-heading">
        <p class="eyebrow">Field Slice Intake</p>
        <h2>客户 field slice 校验</h2>
      </div>
      <div class="field-slice-layout">
        <div class="field-slice-contract">
          <dl>
            <div>
              <dt>minimum_case_count</dt>
              <dd>${formatCount(handoff.minimum_case_count || intake.minimum_case_count || 10)}</dd>
            </div>
            <div>
              <dt>required_fields</dt>
              <dd>${escapeHtml(CUSTOMER_FIELD_SLICE_REQUIRED_FIELDS.join(" / "))}</dd>
            </div>
            <div>
              <dt>template_output_path</dt>
              <dd><a class="artifact-link" href="${escapeHtml(templateHref)}" target="_blank" rel="noopener">打开字段模板</a></dd>
            </div>
            <div>
              <dt>current_intake_status</dt>
              <dd>${escapeHtml(intake.intake_status || "customer_field_slice_intake_validation_pending_no_slice")}</dd>
            </div>
            <div>
              <dt>operator_rehearsal_status</dt>
              <dd>${escapeHtml(operatorRehearsal.operator_rehearsal_status || "r12_customer_field_slice_operator_rehearsal 未提供")}</dd>
            </div>
            <div>
              <dt>operator_command_rehearsed</dt>
              <dd>${formatBooleanGate(operatorRehearsal.operator_command_rehearsed, "operator_command_rehearsed")}</dd>
            </div>
            <div>
              <dt>feedback_loop_rehearsal_status</dt>
              <dd>${escapeHtml(feedbackLoopRehearsal.feedback_loop_rehearsal_status || "r12_customer_feedback_loop_operator_rehearsal 未提供")}</dd>
            </div>
            <div>
              <dt>l22_to_l26_rehearsed</dt>
              <dd>${formatBooleanGate(feedbackLoopRehearsal.l26_synthetic_holdout_review_executed, "l26_synthetic_holdout_review_executed")}</dd>
            </div>
          </dl>
        </div>
        <div class="field-slice-uploader">
          <label class="file-picker">
            <input id="customer-field-slice-input" type="file" accept=".csv,.jsonl,text/csv,application/jsonl" />
            <span>选择客户 field slice</span>
          </label>
          <div id="customer-field-slice-intake-output" class="intake-preview">
            ${renderCustomerFieldSliceIntakePreview(emptyCustomerFieldSlicePreview())}
          </div>
          <button id="customer-field-slice-revalidation-handoff" class="handoff-button" type="button" disabled>
            触发 revalidation handoff
          </button>
          <div id="customer-field-slice-handoff-output" class="handoff-preview">
            ${renderCustomerFieldSliceRevalidationHandoff(emptyCustomerFieldSlicePreview())}
          </div>
        </div>
      </div>
    </article>
  `;
}

function bindCustomerFieldSliceIntakeControls() {
  const input = document.getElementById("customer-field-slice-input");
  const output = document.getElementById("customer-field-slice-intake-output");
  const handoffButton = document.getElementById("customer-field-slice-revalidation-handoff");
  const handoffOutput = document.getElementById("customer-field-slice-handoff-output");
  let latestPreview = emptyCustomerFieldSlicePreview();
  if (!input || !output || !handoffButton || !handoffOutput) return;
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) {
      latestPreview = emptyCustomerFieldSlicePreview();
      output.innerHTML = renderCustomerFieldSliceIntakePreview(latestPreview);
      handoffOutput.innerHTML = renderCustomerFieldSliceRevalidationHandoff(latestPreview);
      handoffButton.disabled = true;
      return;
    }
    try {
      latestPreview = validateCustomerFieldSliceText(await file.text(), file.name);
      output.innerHTML = renderCustomerFieldSliceIntakePreview(latestPreview);
      handoffOutput.innerHTML = renderCustomerFieldSliceRevalidationHandoff(latestPreview);
      handoffButton.disabled = latestPreview.acceptance_gates.ready_for_revalidation !== true;
      handoffButton.dataset.nextRequiredArtifact = latestPreview.next_required_artifact;
    } catch (error) {
      latestPreview = customerFieldSlicePreviewError(error);
      output.innerHTML = renderCustomerFieldSliceIntakePreview(latestPreview);
      handoffOutput.innerHTML = renderCustomerFieldSliceRevalidationHandoff(latestPreview);
      handoffButton.disabled = true;
    }
  });
  handoffButton.addEventListener("click", () => {
    handoffOutput.innerHTML = renderCustomerFieldSliceRevalidationHandoff(latestPreview);
  });
}

function renderCustomerFieldSliceIntakePreview(preview) {
  const gates = preview.acceptance_gates || {};
  const summary = preview.validation_summary || {};
  const errors = preview.validation_errors || [];
  return `
    <div class="intake-status-row">
      <strong>${escapeHtml(preview.status)}</strong>
      <span>${formatBooleanGate(gates.ready_for_revalidation, "ready_for_revalidation")}</span>
    </div>
    <div class="intake-gate-grid">
      ${intakeGate("case_count", `${formatCount(summary.case_count)} / ${formatCount(summary.minimum_case_count || CUSTOMER_FIELD_SLICE_MINIMUM_CASE_COUNT)}`, gates.minimum_case_count_met)}
      ${intakeGate("schema_valid", formatList(summary.missing_required_fields), gates.schema_valid)}
      ${intakeGate("customer_approval_present", String(gates.customer_approval_present === true), gates.customer_approval_present)}
      ${intakeGate("privacy_valid", formatList(summary.direct_pii_columns), gates.privacy_valid)}
      ${intakeGate("numeric_fields_valid", String(gates.numeric_fields_valid === true), gates.numeric_fields_valid)}
      ${intakeGate("timestamps_valid", String(gates.timestamps_valid === true), gates.timestamps_valid)}
      ${intakeGate("duplicate_case_ids_absent", formatList(summary.duplicate_case_ids), gates.duplicate_case_ids_absent)}
      ${intakeGate("runtime_default_allowed", String(gates.runtime_default_allowed === true), gates.runtime_default_allowed)}
    </div>
    <div class="intake-next">
      <span>next_required_artifact</span>
      <strong>${escapeHtml(preview.next_required_artifact)}</strong>
    </div>
    <ul class="intake-errors">
      ${errors.map((error) => `<li>${escapeHtml(error.code)}</li>`).join("") || "<li>validation_errors: 无</li>"}
    </ul>
  `;
}

function intakeGate(label, value, gate) {
  return `
    <div class="intake-gate ${gate ? "intake-gate-pass" : "intake-gate-blocked"}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `;
}

function renderCustomerFieldSliceRevalidationHandoff(preview) {
  const gates = preview.acceptance_gates || {};
  const ready = gates.ready_for_revalidation === true;
  const operatorCommand = customerFieldSliceOperatorCommand(preview);
  return `
    <div class="handoff-card ${ready ? "handoff-card-ready" : "handoff-card-blocked"}">
      <div>
        <span>revalidation_handoff_status</span>
        <strong>${ready ? "ready_for_operator_review" : "blocked_until_valid_customer_slice"}</strong>
      </div>
      <div>
        <span>next_required_artifact</span>
        <strong>${escapeHtml(preview.next_required_artifact)}</strong>
      </div>
      <div>
        <span>claim boundary</span>
        <strong>metrics_computed=false / field_outcome_validated=false / runtime_default_allowed=false</strong>
      </div>
      <div class="handoff-command-block">
        <span>operator_command</span>
        <code>${escapeHtml(operatorCommand)}</code>
      </div>
    </div>
  `;
}

function customerFieldSliceOperatorCommand(preview) {
  if ((preview.acceptance_gates || {}).ready_for_revalidation !== true) {
    return "blocked_until_valid_customer_slice";
  }
  return [
    ".venv/bin/python",
    "experiments/r12_customer_field_slice_intake_validation.py",
    "--artifact-id",
    "r12-customer-field-slice-intake-validation-customer-001",
    "--run-id",
    "r12-customer-field-slice-intake-customer-001",
    "--r12-customer-field-slice-handoff-package-path",
    "experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-handoff-package-current-001.json",
    "--intake-checked-at",
    "CUSTOMER_FIELD_SLICE_INTAKE_TIMESTAMP",
    "--customer-field-slice-path",
    "CUSTOMER_FIELD_SLICE_PATH",
    "--output",
    "experiments/results/r12_customer_field_slice_intake_validation/r12-customer-field-slice-intake-validation-customer-001.json",
  ].join(" ");
}

function validateCustomerFieldSliceText(rawText, fileName) {
  const rows = parseCustomerFieldSliceText(rawText, fileName);
  const presentFields = rows.length > 0 ? Object.keys(rows[0]).sort() : [];
  const presentFieldSet = new Set(presentFields);
  const missingRequiredFields = CUSTOMER_FIELD_SLICE_REQUIRED_FIELDS.filter(
    (field) => !presentFieldSet.has(field),
  );
  const duplicateCaseIds = duplicateCaseIdsFromRows(rows);
  const directPiiColumns = presentFields.filter((field) =>
    CUSTOMER_FIELD_SLICE_DIRECT_PII_COLUMNS.has(field.toLowerCase()),
  );
  const directPiiValueHits = directPiiValueHitsFromRows(rows);
  const numericParseErrors = numericParseErrorsFromRows(rows);
  const timestampParseErrors = timestampParseErrorsFromRows(rows);
  const customerApprovalPresent =
    rows.length > 0
    && rows.every((row) =>
      String(row.customer_approval_reference || "").trim().length > 0,
    );
  const minimumCaseCountMet =
    rows.length >= CUSTOMER_FIELD_SLICE_MINIMUM_CASE_COUNT;
  const validationErrors = customerFieldSliceValidationErrors({
    caseCount: rows.length,
    minimumCaseCount: CUSTOMER_FIELD_SLICE_MINIMUM_CASE_COUNT,
    missingRequiredFields,
    customerApprovalPresent,
    directPiiColumns,
    directPiiValueHits,
    numericParseErrors,
    timestampParseErrors,
    duplicateCaseIds,
  });
  const readyForRevalidation =
    rows.length > 0
    && missingRequiredFields.length === 0
    && minimumCaseCountMet
    && customerApprovalPresent
    && directPiiColumns.length === 0
    && directPiiValueHits.length === 0
    && numericParseErrors.length === 0
    && timestampParseErrors.length === 0
    && duplicateCaseIds.length === 0;

  return customerFieldSlicePreview({
    status: readyForRevalidation
      ? "customer_field_slice_intake_preview_ready_for_revalidation"
      : "customer_field_slice_intake_preview_blocked_contract_or_privacy",
    caseCount: rows.length,
    presentFields,
    missingRequiredFields,
    minimumCaseCountMet,
    customerApprovalPresent,
    directPiiColumns,
    directPiiValueHits,
    numericParseErrors,
    timestampParseErrors,
    duplicateCaseIds,
    validationErrors,
    readyForRevalidation,
    nextRequiredArtifact: readyForRevalidation
      ? "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice"
      : "corrected_customer_field_slice",
  });
}

function emptyCustomerFieldSlicePreview() {
  return customerFieldSlicePreview({
    status: "customer_field_slice_intake_preview_pending_no_slice",
    caseCount: 0,
    presentFields: [],
    missingRequiredFields: CUSTOMER_FIELD_SLICE_REQUIRED_FIELDS,
    minimumCaseCountMet: false,
    customerApprovalPresent: false,
    directPiiColumns: [],
    directPiiValueHits: [],
    numericParseErrors: [],
    timestampParseErrors: [],
    duplicateCaseIds: [],
    validationErrors: [
      { code: "customer_field_slice_not_submitted" },
    ],
    readyForRevalidation: false,
    nextRequiredArtifact: "customer_field_slice_submission",
  });
}

function customerFieldSlicePreviewError(error) {
  return customerFieldSlicePreview({
    status: "customer_field_slice_intake_preview_blocked_parse_error",
    caseCount: 0,
    presentFields: [],
    missingRequiredFields: CUSTOMER_FIELD_SLICE_REQUIRED_FIELDS,
    minimumCaseCountMet: false,
    customerApprovalPresent: false,
    directPiiColumns: [],
    directPiiValueHits: [],
    numericParseErrors: [],
    timestampParseErrors: [],
    duplicateCaseIds: [],
    validationErrors: [
      { code: "field_slice_parse_error", message: String(error.message || error) },
    ],
    readyForRevalidation: false,
    nextRequiredArtifact: "corrected_customer_field_slice",
  });
}

function customerFieldSlicePreview({
  status,
  caseCount,
  presentFields,
  missingRequiredFields,
  minimumCaseCountMet,
  customerApprovalPresent,
  directPiiColumns,
  directPiiValueHits,
  numericParseErrors,
  timestampParseErrors,
  duplicateCaseIds,
  validationErrors,
  readyForRevalidation,
  nextRequiredArtifact,
}) {
  return {
    status,
    claim_level: readyForRevalidation
      ? "customer_field_slice_intake_preview_ready_no_metric_claim"
      : "customer_field_slice_intake_preview_blocked_or_pending",
    validation_summary: {
      case_count: caseCount,
      minimum_case_count: CUSTOMER_FIELD_SLICE_MINIMUM_CASE_COUNT,
      present_fields: presentFields,
      missing_required_fields: missingRequiredFields,
      required_fields_present: missingRequiredFields.length === 0,
      minimum_case_count_met: minimumCaseCountMet,
      customer_approval_present: customerApprovalPresent,
      direct_pii_detected: directPiiColumns.length > 0 || directPiiValueHits.length > 0,
      direct_pii_columns: directPiiColumns,
      direct_pii_value_hits: directPiiValueHits,
      numeric_fields_valid: numericParseErrors.length === 0,
      numeric_parse_errors: numericParseErrors,
      timestamps_valid: timestampParseErrors.length === 0,
      timestamp_parse_errors: timestampParseErrors,
      duplicate_case_ids: duplicateCaseIds,
    },
    validation_errors: validationErrors,
    acceptance_gates: {
      customer_field_slice_submitted: caseCount > 0,
      schema_valid: missingRequiredFields.length === 0,
      minimum_case_count_met: minimumCaseCountMet,
      customer_approval_present: customerApprovalPresent,
      privacy_valid: directPiiColumns.length === 0 && directPiiValueHits.length === 0,
      numeric_fields_valid: numericParseErrors.length === 0,
      timestamps_valid: timestampParseErrors.length === 0,
      duplicate_case_ids_absent: duplicateCaseIds.length === 0,
      ready_for_revalidation: readyForRevalidation,
      metrics_computed: false,
      field_outcome_validated: false,
      product_default_allowed: false,
      runtime_default_allowed: false,
    },
    next_required_artifact: nextRequiredArtifact,
    blocked_claims: [
      "metrics_computed=true",
      "field_or_pre_outcome_revalidation_passed=true",
      "field_outcome_validated=true",
      "Product default can use customer field slice by default",
      "runtime_default_allowed=true",
    ],
  };
}

function parseCustomerFieldSliceText(rawText, fileName) {
  const text = String(rawText || "").trim();
  if (!text) return [];
  const lowerName = String(fileName || "").toLowerCase();
  if (lowerName.endsWith(".jsonl")) {
    return text
      .split(/\r?\n/)
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line));
  }
  if (lowerName.endsWith(".csv")) {
    return parseCustomerFieldSliceCsv(text);
  }
  throw new Error("customer field slice must be csv or jsonl");
}

function parseCustomerFieldSliceCsv(text) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length === 0) return [];
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return Object.fromEntries(
      headers.map((header, index) => [header, values[index] ?? ""]),
    );
  });
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells.map((cell) => cell.trim());
}

function duplicateCaseIdsFromRows(rows) {
  const seen = new Set();
  const duplicates = new Set();
  rows.forEach((row) => {
    const caseId = String(row.case_id || "").trim();
    if (!caseId) return;
    if (seen.has(caseId)) duplicates.add(caseId);
    seen.add(caseId);
  });
  return [...duplicates].sort();
}

function directPiiValueHitsFromRows(rows) {
  const hits = [];
  rows.forEach((row, rowIndex) => {
    Object.entries(row).forEach(([field, value]) => {
      if (CUSTOMER_FIELD_SLICE_EMAIL_PATTERN.test(String(value))) {
        hits.push({ row_index: rowIndex, field, pattern: "email" });
      }
    });
  });
  return hits;
}

function numericParseErrorsFromRows(rows) {
  return parseErrorsFromRows(rows, ["prediction_share_or_score", "observed_outcome"], (value) => {
    const number = Number(value);
    return Number.isFinite(number);
  });
}

function timestampParseErrorsFromRows(rows) {
  return parseErrorsFromRows(rows, ["outcome_timestamp"], (value) =>
    !Number.isNaN(Date.parse(String(value))),
  );
}

function parseErrorsFromRows(rows, fields, isValid) {
  const errors = [];
  rows.forEach((row, rowIndex) => {
    fields.forEach((field) => {
      if (!isValid(row[field])) {
        errors.push({ row_index: rowIndex, field });
      }
    });
  });
  return errors;
}

function customerFieldSliceValidationErrors({
  caseCount,
  minimumCaseCount,
  missingRequiredFields,
  customerApprovalPresent,
  directPiiColumns,
  directPiiValueHits,
  numericParseErrors,
  timestampParseErrors,
  duplicateCaseIds,
}) {
  const errors = [];
  if (caseCount < minimumCaseCount) {
    errors.push({ code: "minimum_case_count_not_met" });
  }
  if (missingRequiredFields.length > 0) {
    errors.push({ code: "missing_required_fields", fields: missingRequiredFields });
  }
  if (!customerApprovalPresent) {
    errors.push({ code: "customer_approval_reference_missing" });
  }
  if (directPiiColumns.length > 0) {
    errors.push({ code: "direct_pii_columns_present", fields: directPiiColumns });
  }
  if (directPiiValueHits.length > 0) {
    errors.push({ code: "direct_pii_values_present", hits: directPiiValueHits });
  }
  if (numericParseErrors.length > 0) {
    errors.push({ code: "numeric_field_parse_failed", errors: numericParseErrors });
  }
  if (timestampParseErrors.length > 0) {
    errors.push({ code: "timestamp_parse_failed", errors: timestampParseErrors });
  }
  if (duplicateCaseIds.length > 0) {
    errors.push({ code: "duplicate_case_id", case_ids: duplicateCaseIds });
  }
  return errors;
}

function renderCustomerWorkflowWorkbench(evidence, apiManifest) {
  if (!evidence) return "";
  const summary = evidence.evidence_summary || {};
  const workflow = summary.customer_validation_workflow_status_boundary || {};
  const handoff = summary.customer_field_slice_handoff_package_boundary || {};
  const readiness = summary.customer_trial_readiness_package_boundary || {};
  const operational = summary.customer_trial_operational_check_boundary || {};
  const packet = summary.customer_trial_launch_packet_export_boundary || {};
  const bundle = summary.customer_trial_launch_bundle_verification_boundary || {};
  const operatorRehearsal =
    summary.customer_field_slice_operator_rehearsal_boundary || {};
  const feedbackLoopRehearsal =
    summary.customer_feedback_loop_operator_rehearsal_boundary || {};
  const trialEvidenceLedger =
    summary.customer_trial_evidence_ledger_boundary || {};
  const arrival = summary.target_outcome_or_customer_field_slice_arrival_boundary || {};
  const revalidation =
    summary.pre_outcome_or_customer_field_outcome_revalidation_boundary || {};
  const endpoints = endpointMap(apiManifest.endpoints || []);
  const artifactPaths = apiManifest.artifact_paths || {};
  const scenarioHref = artifactPathToHref(artifactPaths.scenario_intake);
  const reportHref = artifactPathToHref(artifactPaths.customer_value_report);
  const outcomeHref = artifactPathToHref(artifactPaths.outcome_review);
  const templateHref = artifactPathToHref(
    readiness.template_output_path || handoff.template_output_path,
  );
  const packetHref = artifactPathToHref(packet.markdown_output_path);
  const launchPacketExportReady =
    packet.markdown_export_written === true && packet.launch_handoff_ready === true;
  const simulationGateReady =
    operational.customer_trial_request_operationally_ready === true
    && bundle.launch_bundle_verified === true
    && evidence.runtime_default_allowed === false;

  return `
    <article class="panel panel-wide customer-workflow-panel">
      <div class="panel-heading">
        <p class="eyebrow">Customer Workflow</p>
        <h2>试运行工作台</h2>
      </div>
      <div class="workflow-steps" aria-label="客户试运行工作流">
        ${workflowStep({
          label: "场景输入",
          statusLabel: "scenario_intake_status",
          status: endpointStatus(endpoints.scenario_intake),
          detail: endpoints.scenario_intake?.path || "/r6/product/scenario-intake",
          href: scenarioHref,
          linkLabel: "打开 scenario artifact",
          gate: true,
        })}
        ${workflowStep({
          label: "群体与先验",
          statusLabel: "population_prior_status",
          status: evidence.primary_decision_source || "guarded_baseline_customer_value_report",
          detail: `primary_decision_source: ${evidence.primary_decision_source || "guarded_baseline_customer_value_report"}`,
          href: templateHref,
          linkLabel: "字段模板",
          gate: handoff.customer_field_slice_contract_machine_checkable === true
            || readiness.customer_data_request_ready === true,
        })}
        ${workflowStep({
          label: "运行闸门",
          statusLabel: "simulation_run_gate_status",
          status: simulationGateReady
            ? "customer_trial_ready_runtime_default_blocked"
            : "customer_trial_not_ready",
          detail: `runtime_default_allowed=${String(evidence.runtime_default_allowed === true)} / launch_bundle_verified=${String(bundle.launch_bundle_verified === true)}`,
          href: packetHref,
          linkLabel: "launch packet",
          gate: simulationGateReady,
        })}
        ${workflowStep({
          label: "报告导出",
          statusLabel: "report_export_status",
          status: launchPacketExportReady
            ? "launch_packet_export_ready"
            : "launch_packet_export_pending",
          detail: packet.packet_export_status || "customer_trial_launch_packet_export_boundary 未提供",
          href: reportHref,
          linkLabel: "客户报告 JSON",
          gate: launchPacketExportReady,
        })}
        ${workflowStep({
          label: "outcome review",
          statusLabel: "outcome_review_status",
          status: revalidation.revalidation_status || workflow.workflow_status || "source_arrival_pending",
          detail: `field_or_pre_outcome_revalidation_ready=${String(arrival.field_or_pre_outcome_revalidation_ready === true)} / source_arrived=${String(workflow.source_arrived === true)}`,
          href: outcomeHref,
          linkLabel: "outcome review artifact",
          gate: arrival.field_or_pre_outcome_revalidation_ready === true,
        })}
      </div>
      <div class="workflow-footer">
        <span>customer_field_slice_template_generated: ${formatBooleanGate(Boolean(readiness.template_output_path || handoff.template_output_path), "customer_field_slice_template_generated")}</span>
        <span>operator_command_rehearsed: ${formatBooleanGate(operatorRehearsal.operator_command_rehearsed, "operator_command_rehearsed")}</span>
        <span>l22_to_l26_rehearsed: ${formatBooleanGate(feedbackLoopRehearsal.l26_synthetic_holdout_review_executed, "l26_synthetic_holdout_review_executed")}</span>
        <span>customer_trial_evidence_ledger_ready: ${formatBooleanGate(trialEvidenceLedger.launch_bundle_verified && trialEvidenceLedger.operator_rehearsal_executed && trialEvidenceLedger.feedback_loop_rehearsed_l22_to_l26, "customer_trial_evidence_ledger_ready")}</span>
        <span>field_or_pre_outcome_revalidation_ready: ${formatBooleanGate(arrival.field_or_pre_outcome_revalidation_ready, "field_or_pre_outcome_revalidation_ready")}</span>
        <span>primary_decision_source: ${escapeHtml(evidence.primary_decision_source || "guarded_baseline_customer_value_report")}</span>
      </div>
    </article>
  `;
}

function workflowStep({ label, statusLabel, status, detail, href, linkLabel, gate }) {
  return `
    <section class="workflow-step ${gate ? "workflow-step-ready" : "workflow-step-blocked"}">
      <div class="workflow-step-top">
        <span>${escapeHtml(label)}</span>
        <strong>${gate ? "可用" : "等待"}</strong>
      </div>
      <dl>
        <div>
          <dt>${escapeHtml(statusLabel)}</dt>
          <dd>${escapeHtml(status || "未提供")}</dd>
        </div>
        <div>
          <dt>source-backed detail</dt>
          <dd>${escapeHtml(detail || "未提供")}</dd>
        </div>
      </dl>
      <a class="artifact-link" href="${escapeHtml(href || "#")}" target="_blank" rel="noopener">${escapeHtml(linkLabel)}</a>
    </section>
  `;
}

function renderCustomerTrialActionPanel(evidence) {
  if (!evidence) return "";
  const summary = evidence.evidence_summary || {};
  const workflow = summary.customer_validation_workflow_status_boundary || {};
  const readiness = summary.customer_trial_readiness_package_boundary || {};
  const packet = summary.customer_trial_launch_packet_export_boundary || {};
  const bundle = summary.customer_trial_launch_bundle_verification_boundary || {};
  const operatorRehearsal =
    summary.customer_field_slice_operator_rehearsal_boundary || {};
  const feedbackLoopRehearsal =
    summary.customer_feedback_loop_operator_rehearsal_boundary || {};
  const trialEvidenceLedger =
    summary.customer_trial_evidence_ledger_boundary || {};
  const packetHref = artifactPathToHref(packet.markdown_output_path);
  const nextAction =
    workflow.next_action || "collect_customer_field_slice_or_wait_for_target_outcome";
  return `
    <article class="panel panel-wide customer-trial-action-panel">
      <div class="panel-heading">
        <p class="eyebrow">Customer Trial</p>
        <h2>客户试运行</h2>
      </div>
      <div class="trial-action-grid">
        <div class="trial-action-primary">
          <span>客户下一步</span>
          <strong>${escapeHtml(nextAction)}</strong>
          <p>当前只请求客户 field slice 或等待 target outcome，不声明 validation passed。</p>
        </div>
        <div class="trial-action-item">
          <span>stage</span>
          <strong>${escapeHtml(workflow.current_stage || bundle.current_stage || "source_arrival_pending")}</strong>
        </div>
        <div class="trial-action-item">
          <span>trial readiness</span>
          <strong>${escapeHtml(readiness.trial_package_status || "trial_readiness_package_boundary 未提供")}</strong>
        </div>
        <div class="trial-action-item">
          <span>launch packet</span>
          <strong>${formatBooleanGate(packet.markdown_export_written, "markdown_export_written")}</strong>
          <a class="artifact-link" href="${escapeHtml(packetHref)}" target="_blank" rel="noopener">打开 launch packet</a>
        </div>
        <div class="trial-action-item">
          <span>bundle verification</span>
          <strong>${formatBooleanGate(bundle.launch_bundle_verified, "launch_bundle_verified")}</strong>
          <small>${formatCount(bundle.resolved_required_item_count)} / ${formatCount(bundle.required_item_count)} required items</small>
        </div>
        <div class="trial-action-item">
          <span>operator rehearsal</span>
          <strong>${formatBooleanGate(operatorRehearsal.operator_command_rehearsed, "operator_command_rehearsed")}</strong>
          <small>${escapeHtml(operatorRehearsal.sample_slice_kind || "synthetic_rehearsal_fixture")}</small>
        </div>
        <div class="trial-action-item">
          <span>feedback loop rehearsal</span>
          <strong>${formatBooleanGate(feedbackLoopRehearsal.l26_synthetic_holdout_review_executed, "l26_synthetic_holdout_review_executed")}</strong>
          <small>L22 intake -> L26 holdout review</small>
        </div>
        <div class="trial-action-item">
          <span>r12_customer_trial_evidence_ledger</span>
          <strong>${escapeHtml(trialEvidenceLedger.ledger_status || "customer_trial_evidence_ledger_boundary 未提供")}</strong>
          <small>${formatCount(trialEvidenceLedger.customer_visible_readiness_evidence_count)} customer / ${formatCount(trialEvidenceLedger.operator_only_rehearsal_evidence_count)} operator / ${formatCount(trialEvidenceLedger.blocking_gap_count)} gaps</small>
        </div>
        <div class="trial-action-item">
          <span>blocked claim</span>
          <strong>${formatBooleanGate(bundle.field_outcome_validated, "field_outcome_validated")}</strong>
        </div>
      </div>
    </article>
  `;
}

function endpointMap(endpoints) {
  return Object.fromEntries(
    endpoints.map((endpoint) => [endpoint.endpoint_id, endpoint]),
  );
}

function endpointStatus(endpoint) {
  if (!endpoint) return "endpoint_missing";
  return `${endpoint.method || "GET"} ${endpoint.response_contract || "source_artifact_json"}`;
}

function renderR12TransferEvidence(evidence) {
  if (!evidence) return "";
  const metrics = evidence.metrics || {};
  const publicScope = evidence.public_data_validation_scope || {};
  const summary = evidence.evidence_summary || {};
  const extended = summary.extended_metric_gates || {};
  const highRiskBoundary = summary.high_risk_holdout_boundary || {};
  const highRiskReplay = summary.high_risk_replay_boundary || {};
  const recallUpdate = summary.recall_oriented_update_boundary || {};
  const recallStress = summary.recall_false_alarm_stress_boundary || {};
  const recallMitigation = summary.recall_false_alarm_mitigation_boundary || {};
  const recallMitigationHoldout =
    summary.recall_mitigation_holdout_validation_boundary || {};
  const recallMitigationIndependentData =
    summary.recall_mitigation_independent_holdout_data_boundary || {};
  const recallMitigationExternalSlice =
    summary
      .recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary
    || {};
  const externalOrCustomerRawSlice =
    summary.external_or_customer_holdout_raw_slice_boundary || {};
  const externalHoldoutRevalidation =
    summary.recall_mitigation_external_holdout_revalidation_boundary || {};
  const predictionPacket =
    summary.pre_outcome_or_independent_prediction_packet_boundary || {};
  const independentHindcast =
    summary.independent_hindcast_revalidation_boundary || {};
  const preOutcomeTrial =
    summary
      .pre_outcome_prediction_trial_or_customer_field_revalidation_boundary
    || {};
  const outcomeIngestion =
    summary.pre_outcome_or_customer_field_outcome_ingestion_boundary || {};
  const outcomeRevalidation =
    summary.pre_outcome_or_customer_field_outcome_revalidation_boundary || {};
  const targetOrCustomerArrival =
    summary.target_outcome_or_customer_field_slice_arrival_boundary || {};
  const customerFieldHandoff =
    summary.customer_field_slice_handoff_package_boundary || {};
  const customerFieldIntake =
    summary.customer_field_slice_intake_validation_boundary || {};
  const customerFieldRevalidation =
    summary.customer_field_slice_revalidation_boundary || {};
  const customerFieldFeedback =
    summary.customer_field_outcome_feedback_update_boundary || {};
  const customerFeedbackShadowReplay =
    summary.customer_feedback_update_shadow_replay_boundary || {};
  const customerFeedbackHoldoutReview =
    summary.customer_feedback_shadow_replay_holdout_review_boundary || {};
  const customerValidationWorkflow =
    summary.customer_validation_workflow_status_boundary || {};
  const customerTrialReadiness =
    summary.customer_trial_readiness_package_boundary || {};
  const customerTrialOperational =
    summary.customer_trial_operational_check_boundary || {};
  const customerTrialLaunch =
    summary.customer_trial_launch_handoff_package_boundary || {};
  const customerTrialPacketExport =
    summary.customer_trial_launch_packet_export_boundary || {};
  const customerTrialPacketHref = artifactPathToHref(customerTrialPacketExport.markdown_output_path);
  const customerTrialBundleVerification =
    summary.customer_trial_launch_bundle_verification_boundary || {};
  const customerFieldOperatorRehearsal =
    summary.customer_field_slice_operator_rehearsal_boundary || {};
  const customerFeedbackLoopRehearsal =
    summary.customer_feedback_loop_operator_rehearsal_boundary || {};
  const customerTrialEvidenceLedger =
    summary.customer_trial_evidence_ledger_boundary || {};
  const update = summary.accepted_update || {};
  return `
    <article class="panel panel-wide">
      <div class="panel-heading">
        <p class="eyebrow">R12 Transfer</p>
        <h2>R12 迁移验证</h2>
      </div>
      <div class="research-summary">
        <div>
          <span>update_transfer_gain</span>
          <strong>${formatSignedNumber(metrics.update_transfer_gain)}</strong>
        </div>
        <div>
          <span>validation MAE</span>
          <strong>${formatSignedNumber(metrics.validation_mean_absolute_error_delta)}</strong>
        </div>
        <div>
          <span>holdout MAE</span>
          <strong>${formatSignedNumber(metrics.holdout_mean_absolute_error_delta)}</strong>
        </div>
        <div>
          <span>区间退化</span>
          <strong>${formatSignedNumber(metrics.interval_coverage_delta)}</strong>
        </div>
        <div>
          <span>误报变化</span>
          <strong>${formatSignedNumber(metrics.false_alarm_rate_delta)}</strong>
        </div>
      </div>
      <div class="mechanism-box public-data-scope">
        <dl>
          <div>
            <dt>本阶段验证范围</dt>
            <dd>${escapeHtml(publicScope.stage || "public_data_validation_only")}</dd>
          </div>
          <div>
            <dt>公开数据有效声明</dt>
            <dd>${formatBooleanGate(evidence.public_data_effectiveness_claim_allowed, "public_data_effectiveness_claim_allowed")}</dd>
          </div>
          <div>
            <dt>客户 field 本阶段要求</dt>
            <dd>${formatBooleanGate(evidence.customer_field_validation_required_for_current_stage, "customer_field_validation_required_for_current_stage")}</dd>
          </div>
          <div>
            <dt>公开数据声明</dt>
            <dd>${escapeHtml(publicScope.public_data_effectiveness_claim || "tested_effective_on_public_data_guarded")}</dd>
          </div>
        </dl>
      </div>
      <div class="mechanism-box">
        <dl>
          <div>
            <dt>声明状态</dt>
            <dd>${escapeHtml(SUPPORT_LABELS[evidence.support_status] || evidence.support_status)}</dd>
          </div>
          <div>
            <dt>证据角色</dt>
            <dd>${escapeHtml(evidence.r12_output_role || "secondary_transfer_evidence_card_only")}</dd>
          </div>
          <div>
            <dt>更新对象</dt>
            <dd>${escapeHtml(update.target || "未提供")} ${escapeHtml(update.recommended_value ?? "")}</dd>
          </div>
          <div>
            <dt>运行默认</dt>
            <dd>${evidence.runtime_default_allowed ? "允许" : "不允许"}</dd>
          </div>
          <div>
            <dt>扩展指标</dt>
            <dd>${escapeHtml(extended.extended_product_metric_support_level || "extended_product_metric_support_level 未提供")}</dd>
          </div>
          <div>
            <dt>漏报恢复 holdout 覆盖</dt>
            <dd>${formatBooleanGate(extended.static_prior_miss_recovery_holdout_covered, "static_prior_miss_recovery_holdout_covered")}</dd>
          </div>
          <div>
            <dt>异常群体 holdout 覆盖</dt>
            <dd>${formatBooleanGate(extended.abnormal_segment_recall_holdout_covered, "abnormal_segment_recall_holdout_covered")}</dd>
          </div>
          <div>
            <dt>高风险候选</dt>
            <dd>${formatCount(highRiskBoundary.research_eligible_case_count)} 个研究候选，${formatCount(highRiskBoundary.research_recoverable_static_prior_miss_count)} 个可测漏报恢复</dd>
          </div>
          <div>
            <dt>Product 默认高风险 holdout</dt>
            <dd>${formatBooleanGate(highRiskBoundary.product_default_low_sensitive_high_risk_holdout_present, "product_default_low_sensitive_high_risk_holdout_present")}</dd>
          </div>
          <div>
            <dt>高风险边界</dt>
            <dd>${escapeHtml(highRiskBoundary.product_claim_boundary || "research_only_until_low_sensitive_or_customer_approved_holdout")}</dd>
          </div>
          <div>
            <dt>High-risk replay MAE</dt>
            <dd>${formatSignedNumber(highRiskReplay.mean_absolute_error_delta)}</dd>
          </div>
          <div>
            <dt>Replay 漏报恢复变化</dt>
            <dd>${formatSignedNumber(highRiskReplay.static_prior_miss_recovery_delta)}</dd>
          </div>
          <div>
            <dt>Replay 异常召回变化</dt>
            <dd>${formatSignedNumber(highRiskReplay.abnormal_segment_recall_delta)}</dd>
          </div>
          <div>
            <dt>Replay 决策</dt>
            <dd>${escapeHtml(highRiskReplay.transfer_decision || "r12_high_risk_replay_mae_positive_recall_flat_research_only")}</dd>
          </div>
          <div>
            <dt>召回更新 margin</dt>
            <dd>${escapeHtml(recallUpdate.recommended_activation_margin ?? "recommended_activation_margin 未提供")}</dd>
          </div>
          <div>
            <dt>召回更新漏报恢复</dt>
            <dd>${formatSignedNumber(recallUpdate.static_prior_miss_recovery_delta)}</dd>
          </div>
          <div>
            <dt>召回更新误报代价</dt>
            <dd>${formatSignedNumber(recallUpdate.false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>召回更新精度代价</dt>
            <dd>${formatSignedNumber(recallUpdate.precision_delta)}</dd>
          </div>
          <div>
            <dt>召回更新默认启用</dt>
            <dd>${formatBooleanGate(recallUpdate.product_default_allowed, "product_default_allowed")}</dd>
          </div>
          <div>
            <dt>下一验收产物</dt>
            <dd>${escapeHtml(recallUpdate.next_required_artifact || "r12_recall_update_holdout_false_alarm_stress_test")}</dd>
          </div>
          <div>
            <dt>误报压力测试</dt>
            <dd>${escapeHtml(recallStress.stress_status || "recall_false_alarm_stress_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>压力测试误报变化</dt>
            <dd>${formatSignedNumber(recallStress.global_false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>敏感轴误报变化</dt>
            <dd>${formatSignedNumber(recallStress.protected_sensitive_false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>低敏感召回可验</dt>
            <dd>${formatBooleanGate(recallStress.low_sensitive_recall_evaluable, "low_sensitive_recall_evaluable")}</dd>
          </div>
          <div>
            <dt>误报集中轴</dt>
            <dd>${escapeHtml(recallStress.dominant_false_alarm_segment_column || "dominant_false_alarm_segment_column 未提供")}</dd>
          </div>
          <div>
            <dt>压力测试下一步</dt>
            <dd>${escapeHtml(recallStress.next_required_artifact || "r12_recall_false_alarm_mitigation_candidate")}</dd>
          </div>
          <div>
            <dt>误报缓解候选</dt>
            <dd>${escapeHtml(recallMitigation.candidate_id || "recall_false_alarm_mitigation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>缓解后召回保留</dt>
            <dd>${formatSignedNumber(recallMitigation.l7_recall_gain_retained)}</dd>
          </div>
          <div>
            <dt>缓解后误报变化</dt>
            <dd>${formatSignedNumber(recallMitigation.mitigated_false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>缓解后精度变化</dt>
            <dd>${formatSignedNumber(recallMitigation.mitigated_precision_delta)}</dd>
          </div>
          <div>
            <dt>缓解过拟合风险</dt>
            <dd>${escapeHtml(recallMitigation.overfit_risk || "high_current_false_alarm_band_derived")}</dd>
          </div>
          <div>
            <dt>缓解下一验收</dt>
            <dd>${escapeHtml(recallMitigation.next_required_artifact || "r12_recall_mitigation_holdout_validation")}</dd>
          </div>
          <div>
            <dt>缓解 holdout 验证</dt>
            <dd>${escapeHtml(recallMitigationHoldout.validation_status || "recall_mitigation_holdout_validation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>leave-one 通过率</dt>
            <dd>${formatSignedNumber(recallMitigationHoldout.leave_one_pass_rate)}</dd>
          </div>
          <div>
            <dt>端点 holdout 失败</dt>
            <dd>${formatCount(recallMitigationHoldout.endpoint_holdout_failure_count)}</dd>
          </div>
          <div>
            <dt>独立 holdout</dt>
            <dd>${formatBooleanGate(recallMitigationHoldout.independent_holdout_present, "independent_holdout_present")}</dd>
          </div>
          <div>
            <dt>缓解默认启用</dt>
            <dd>${formatBooleanGate(recallMitigationHoldout.product_default_allowed, "product_default_allowed")}</dd>
          </div>
          <div>
            <dt>holdout 下一验收</dt>
            <dd>${escapeHtml(recallMitigationHoldout.next_required_artifact || "r12_recall_mitigation_independent_holdout_data")}</dd>
          </div>
          <div>
            <dt>独立数据审计</dt>
            <dd>${escapeHtml(recallMitigationIndependentData.data_status || "recall_mitigation_independent_holdout_data_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>同源诊断候选</dt>
            <dd>${formatCount(recallMitigationIndependentData.same_dataset_non_derivation_recall_candidate_count)}</dd>
          </div>
          <div>
            <dt>低敏感高风险样本</dt>
            <dd>${formatCount(recallMitigationIndependentData.low_sensitive_observed_high_risk_count)}</dd>
          </div>
          <div>
            <dt>外部候选源</dt>
            <dd>${formatCount(recallMitigationIndependentData.external_registry_candidate_count)}</dd>
          </div>
          <div>
            <dt>已接入独立数据</dt>
            <dd>${formatCount(recallMitigationIndependentData.ingested_external_independent_dataset_count)}</dd>
          </div>
          <div>
            <dt>独立数据下一步</dt>
            <dd>${escapeHtml(recallMitigationIndependentData.next_required_artifact || "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice")}</dd>
          </div>
          <div>
            <dt>外部/客户切片合同</dt>
            <dd>${escapeHtml(recallMitigationExternalSlice.contract_status || "recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>首选外部源</dt>
            <dd>${escapeHtml(recallMitigationExternalSlice.preferred_external_source_id || "preferred_external_source_id 未提供")}</dd>
          </div>
          <div>
            <dt>raw holdout slice</dt>
            <dd>${formatBooleanGate(recallMitigationExternalSlice.raw_external_or_customer_slice_present, "raw_external_or_customer_slice_present")}</dd>
          </div>
          <div>
            <dt>客户授权</dt>
            <dd>${formatBooleanGate(recallMitigationExternalSlice.customer_approval_present, "customer_approval_present")}</dd>
          </div>
          <div>
            <dt>合同下一步</dt>
            <dd>${escapeHtml(recallMitigationExternalSlice.next_required_artifact || "r12_external_or_customer_holdout_raw_slice")}</dd>
          </div>
          <div>
            <dt>外部 raw slice</dt>
            <dd>${escapeHtml(externalOrCustomerRawSlice.raw_slice_status || "external_or_customer_holdout_raw_slice_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>官方数据接入</dt>
            <dd>${formatBooleanGate(externalOrCustomerRawSlice.actual_public_data_ingested, "actual_public_data_ingested")}</dd>
          </div>
          <div>
            <dt>raw slice cases</dt>
            <dd>${formatCount(externalOrCustomerRawSlice.case_count)} / source rows ${formatCount(externalOrCustomerRawSlice.source_row_count)}</dd>
          </div>
          <div>
            <dt>observed complaints</dt>
            <dd>${formatCount(externalOrCustomerRawSlice.total_observed_complaint_cases)}</dd>
          </div>
          <div>
            <dt>预测字段</dt>
            <dd>${formatBooleanGate(externalOrCustomerRawSlice.prediction_fields_present, "prediction_fields_present")}</dd>
          </div>
          <div>
            <dt>raw slice 下一步</dt>
            <dd>${escapeHtml(externalOrCustomerRawSlice.next_required_artifact || "r12_recall_mitigation_external_holdout_revalidation")}</dd>
          </div>
          <div>
            <dt>外部 revalidation</dt>
            <dd>${escapeHtml(externalHoldoutRevalidation.revalidation_status || "recall_mitigation_external_holdout_revalidation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>revalidation passed</dt>
            <dd>${formatBooleanGate(externalHoldoutRevalidation.external_holdout_revalidation_passed, "external_holdout_revalidation_passed")}</dd>
          </div>
          <div>
            <dt>同表泄漏风险</dt>
            <dd>${formatBooleanGate(externalHoldoutRevalidation.same_table_prediction_leakage_risk, "same_table_prediction_leakage_risk")}</dd>
          </div>
          <div>
            <dt>proxy MAE 变化</dt>
            <dd>${formatSignedNumber(externalHoldoutRevalidation.mean_absolute_error_delta)}</dd>
          </div>
          <div>
            <dt>风险排序变化</dt>
            <dd>${formatSignedNumber(externalHoldoutRevalidation.risk_ranking_quality_delta)}</dd>
          </div>
          <div>
            <dt>漏报恢复变化</dt>
            <dd>${formatSignedNumber(externalHoldoutRevalidation.static_prior_miss_recovery_delta)}</dd>
          </div>
          <div>
            <dt>误报变化</dt>
            <dd>${formatSignedNumber(externalHoldoutRevalidation.false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>revalidation 下一步</dt>
            <dd>${escapeHtml(externalHoldoutRevalidation.next_required_artifact || "r12_pre_outcome_or_independent_prediction_packet")}</dd>
          </div>
          <div>
            <dt>prediction packet</dt>
            <dd>${escapeHtml(predictionPacket.packet_status || "pre_outcome_or_independent_prediction_packet_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>独立特征源</dt>
            <dd>${formatBooleanGate(predictionPacket.prediction_source_independent_of_target_outcome, "prediction_source_independent_of_target_outcome")}</dd>
          </div>
          <div>
            <dt>事前锁定</dt>
            <dd>${formatBooleanGate(predictionPacket.prediction_lock_timestamp_pre_target_outcome, "prediction_lock_timestamp_pre_target_outcome")}</dd>
          </div>
          <div>
            <dt>hindcast ready</dt>
            <dd>${formatBooleanGate(predictionPacket.hindcast_independent_revalidation_ready, "hindcast_independent_revalidation_ready")}</dd>
          </div>
          <div>
            <dt>pre-outcome ready</dt>
            <dd>${formatBooleanGate(predictionPacket.pre_outcome_revalidation_ready, "pre_outcome_revalidation_ready")}</dd>
          </div>
          <div>
            <dt>prediction cases</dt>
            <dd>${formatCount(predictionPacket.prediction_case_count)} / matched ${formatCount(predictionPacket.matched_case_count)}</dd>
          </div>
          <div>
            <dt>packet 下一步</dt>
            <dd>${escapeHtml(predictionPacket.next_required_artifact || "r12_independent_hindcast_revalidation")}</dd>
          </div>
          <div>
            <dt>independent hindcast</dt>
            <dd>${escapeHtml(independentHindcast.hindcast_status || "independent_hindcast_revalidation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>hindcast passed</dt>
            <dd>${formatBooleanGate(independentHindcast.hindcast_independent_revalidation_passed, "hindcast_independent_revalidation_passed")}</dd>
          </div>
          <div>
            <dt>hindcast MAE 变化</dt>
            <dd>${formatSignedNumber(independentHindcast.mean_absolute_error_delta)}</dd>
          </div>
          <div>
            <dt>hindcast 区间变化</dt>
            <dd>${formatSignedNumber(independentHindcast.interval_coverage_delta)}</dd>
          </div>
          <div>
            <dt>hindcast 风险排序</dt>
            <dd>${formatSignedNumber(independentHindcast.risk_ranking_quality_delta)}</dd>
          </div>
          <div>
            <dt>hindcast 漏报恢复</dt>
            <dd>${formatSignedNumber(independentHindcast.static_prior_miss_recovery_delta)}</dd>
          </div>
          <div>
            <dt>hindcast 误报变化</dt>
            <dd>${formatSignedNumber(independentHindcast.false_alarm_rate_delta)}</dd>
          </div>
          <div>
            <dt>hindcast 决策价值</dt>
            <dd>${formatSignedNumber(independentHindcast.decision_value_delta)}</dd>
          </div>
          <div>
            <dt>hindcast pre-outcome</dt>
            <dd>${formatBooleanGate(independentHindcast.pre_outcome_revalidation_ready, "pre_outcome_revalidation_ready")}</dd>
          </div>
          <div>
            <dt>hindcast 下一验收</dt>
            <dd>${escapeHtml(independentHindcast.next_required_artifact || "r12_pre_outcome_prediction_trial_or_customer_field_revalidation")}</dd>
          </div>
          <div>
            <dt>pre-outcome trial</dt>
            <dd>${escapeHtml(preOutcomeTrial.trial_status || "pre_outcome_prediction_trial_or_customer_field_revalidation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>锁定时间</dt>
            <dd>${escapeHtml(preOutcomeTrial.prediction_lock_timestamp || "prediction_lock_timestamp 未提供")}</dd>
          </div>
          <div>
            <dt>锁定早于 target</dt>
            <dd>${formatBooleanGate(preOutcomeTrial.prediction_lock_timestamp_pre_target_outcome, "prediction_lock_timestamp_pre_target_outcome")}</dd>
          </div>
          <div>
            <dt>target period</dt>
            <dd>${escapeHtml(preOutcomeTrial.target_outcome_period || "target_outcome_period 未提供")}</dd>
          </div>
          <div>
            <dt>target outcome</dt>
            <dd>${formatBooleanGate(preOutcomeTrial.target_outcome_artifact_present, "target_outcome_artifact_present")}</dd>
          </div>
          <div>
            <dt>trial cases</dt>
            <dd>${formatCount(preOutcomeTrial.prediction_case_count)}</dd>
          </div>
          <div>
            <dt>客户 field 合同</dt>
            <dd>${formatBooleanGate(preOutcomeTrial.customer_field_slice_contract_ready, "customer_field_slice_contract_ready")}</dd>
          </div>
          <div>
            <dt>客户 field slice</dt>
            <dd>${formatBooleanGate(preOutcomeTrial.customer_field_slice_present, "customer_field_slice_present")}</dd>
          </div>
          <div>
            <dt>trial 默认启用</dt>
            <dd>${formatBooleanGate(preOutcomeTrial.product_default_allowed, "product_default_allowed")}</dd>
          </div>
          <div>
            <dt>trial 下一验收</dt>
            <dd>${escapeHtml(preOutcomeTrial.next_required_artifact || "r12_pre_outcome_or_customer_field_outcome_ingestion")}</dd>
          </div>
          <div>
            <dt>outcome ingestion</dt>
            <dd>${escapeHtml(outcomeIngestion.ingestion_status || "pre_outcome_or_customer_field_outcome_ingestion_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>availability checked</dt>
            <dd>${escapeHtml(outcomeIngestion.availability_checked_at || "availability_checked_at 未提供")}</dd>
          </div>
          <div>
            <dt>latest report</dt>
            <dd>${escapeHtml(outcomeIngestion.latest_available_report || "latest_available_report 未提供")}</dd>
          </div>
          <div>
            <dt>target public outcome</dt>
            <dd>${formatBooleanGate(outcomeIngestion.target_public_outcome_available, "target_public_outcome_available")}</dd>
          </div>
          <div>
            <dt>outcome artifact</dt>
            <dd>${formatBooleanGate(outcomeIngestion.target_outcome_artifact_present, "target_outcome_artifact_present")}</dd>
          </div>
          <div>
            <dt>field slice contract</dt>
            <dd>${formatBooleanGate(outcomeIngestion.customer_field_slice_contract_ready, "customer_field_slice_contract_ready")}</dd>
          </div>
          <div>
            <dt>field slice present</dt>
            <dd>${formatBooleanGate(outcomeIngestion.customer_field_slice_present, "customer_field_slice_present")}</dd>
          </div>
          <div>
            <dt>revalidation ready</dt>
            <dd>${formatBooleanGate(outcomeIngestion.field_or_pre_outcome_revalidation_ready, "field_or_pre_outcome_revalidation_ready")}</dd>
          </div>
          <div>
            <dt>ingestion 下一验收</dt>
            <dd>${escapeHtml(outcomeIngestion.next_required_artifact || "r12_pre_outcome_or_customer_field_outcome_revalidation")}</dd>
          </div>
          <div>
            <dt>outcome revalidation</dt>
            <dd>${escapeHtml(outcomeRevalidation.revalidation_status || "pre_outcome_or_customer_field_outcome_revalidation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>metrics computed</dt>
            <dd>${formatBooleanGate(outcomeRevalidation.metrics_computed, "metrics_computed")}</dd>
          </div>
          <div>
            <dt>revalidation passed</dt>
            <dd>${formatBooleanGate(outcomeRevalidation.field_or_pre_outcome_revalidation_passed, "field_or_pre_outcome_revalidation_passed")}</dd>
          </div>
          <div>
            <dt>revalidation 默认启用</dt>
            <dd>${formatBooleanGate(outcomeRevalidation.product_default_allowed, "product_default_allowed")}</dd>
          </div>
          <div>
            <dt>revalidation 下一验收</dt>
            <dd>${escapeHtml(outcomeRevalidation.next_required_artifact || "r12_target_outcome_or_customer_field_slice_arrival")}</dd>
          </div>
          <div>
            <dt>target/field arrival</dt>
            <dd>${escapeHtml(targetOrCustomerArrival.arrival_status || "target_outcome_or_customer_field_slice_arrival_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>outcome source arrived</dt>
            <dd>${formatBooleanGate(targetOrCustomerArrival.outcome_source_arrived, "outcome_source_arrived")}</dd>
          </div>
          <div>
            <dt>arrival revalidation ready</dt>
            <dd>${formatBooleanGate(targetOrCustomerArrival.field_or_pre_outcome_revalidation_ready, "field_or_pre_outcome_revalidation_ready")}</dd>
          </div>
          <div>
            <dt>arrival metrics computed</dt>
            <dd>${formatBooleanGate(targetOrCustomerArrival.metrics_computed, "metrics_computed")}</dd>
          </div>
          <div>
            <dt>arrival 下一验收</dt>
            <dd>${escapeHtml(targetOrCustomerArrival.next_required_artifact || "r12_target_outcome_or_customer_field_slice_arrival")}</dd>
          </div>
          <div>
            <dt>field handoff package</dt>
            <dd>${escapeHtml(customerFieldHandoff.handoff_status || "customer_field_slice_handoff_package_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>customer data request</dt>
            <dd>${formatBooleanGate(customerFieldHandoff.customer_data_request_ready, "customer_data_request_ready")}</dd>
          </div>
          <div>
            <dt>template file</dt>
            <dd>${escapeHtml(customerFieldHandoff.template_output_path || "r12-customer-field-slice-template-current-001.csv")}</dd>
          </div>
          <div>
            <dt>minimum cases</dt>
            <dd>${formatCount(customerFieldHandoff.minimum_case_count)}</dd>
          </div>
          <div>
            <dt>handoff 下一验收</dt>
            <dd>${escapeHtml(customerFieldHandoff.next_required_artifact || "r12_customer_field_slice_handoff_package")}</dd>
          </div>
          <div>
            <dt>field intake validator</dt>
            <dd>${escapeHtml(customerFieldIntake.intake_status || "customer_field_slice_intake_validation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>ready for revalidation</dt>
            <dd>${formatBooleanGate(customerFieldIntake.ready_for_revalidation, "ready_for_revalidation")}</dd>
          </div>
          <div>
            <dt>privacy gate</dt>
            <dd>${formatBooleanGate(customerFieldIntake.privacy_valid, "privacy_valid")}</dd>
          </div>
          <div>
            <dt>intake quality gates</dt>
            <dd>${formatBooleanGate(customerFieldIntake.numeric_fields_valid, "numeric_fields_valid")} / ${formatBooleanGate(customerFieldIntake.timestamps_valid, "timestamps_valid")} / ${formatBooleanGate(customerFieldIntake.duplicate_case_ids_absent, "duplicate_case_ids_absent")}</dd>
          </div>
          <div>
            <dt>intake cases</dt>
            <dd>${formatCount(customerFieldIntake.case_count)} / ${formatCount(customerFieldIntake.minimum_case_count)}</dd>
          </div>
          <div>
            <dt>intake 下一验收</dt>
            <dd>${escapeHtml(customerFieldIntake.next_required_artifact || "r12_customer_field_slice_intake_validation")}</dd>
          </div>
          <div>
            <dt>field revalidation</dt>
            <dd>${escapeHtml(customerFieldRevalidation.revalidation_status || "customer_field_slice_revalidation_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>field metrics computed</dt>
            <dd>${formatBooleanGate(customerFieldRevalidation.metrics_computed, "metrics_computed")}</dd>
          </div>
          <div>
            <dt>field outcome validated</dt>
            <dd>${formatBooleanGate(customerFieldRevalidation.field_outcome_validated, "field_outcome_validated")}</dd>
          </div>
          <div>
            <dt>field MAE</dt>
            <dd>${formatNumber(customerFieldRevalidation.mean_absolute_error)} <span>mean_absolute_error</span></dd>
          </div>
          <div>
            <dt>field ranking</dt>
            <dd>${formatNumber(customerFieldRevalidation.risk_ranking_quality)} <span>risk_ranking_quality</span></dd>
          </div>
          <div>
            <dt>revalidation 下一验收</dt>
            <dd>${escapeHtml(customerFieldRevalidation.next_required_artifact || "r12_customer_field_slice_revalidation")}</dd>
          </div>
          <div>
            <dt>field feedback update</dt>
            <dd>${escapeHtml(customerFieldFeedback.feedback_update_status || "customer_field_outcome_feedback_update_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>feedback metrics consumed</dt>
            <dd>${formatBooleanGate(customerFieldFeedback.metrics_consumed, "metrics_consumed")}</dd>
          </div>
          <div>
            <dt>feedback candidate count</dt>
            <dd>${formatCount(customerFieldFeedback.candidate_count)} <span>candidate_count</span></dd>
          </div>
          <div>
            <dt>prompt/persona patch</dt>
            <dd>${formatBooleanGate(customerFieldFeedback.prompt_or_persona_manual_patch_allowed, "prompt_or_persona_manual_patch_allowed")}</dd>
          </div>
          <div>
            <dt>feedback 下一验收</dt>
            <dd>${escapeHtml(customerFieldFeedback.next_required_artifact || "r12_customer_field_outcome_feedback_update")}</dd>
          </div>
          <div>
            <dt>feedback shadow replay</dt>
            <dd>${escapeHtml(customerFeedbackShadowReplay.shadow_replay_status || "customer_feedback_update_shadow_replay_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>shadow replay executed</dt>
            <dd>${formatBooleanGate(customerFeedbackShadowReplay.replay_executed, "shadow_replay_executed")}</dd>
          </div>
          <div>
            <dt>accepted replay candidates</dt>
            <dd>${formatCount(customerFeedbackShadowReplay.accepted_candidate_count)} <span>accepted_candidate_count</span></dd>
          </div>
          <div>
            <dt>shadow replay 下一验收</dt>
            <dd>${escapeHtml(customerFeedbackShadowReplay.next_required_artifact || "r12_customer_feedback_update_shadow_replay")}</dd>
          </div>
          <div>
            <dt>feedback holdout review</dt>
            <dd>${escapeHtml(customerFeedbackHoldoutReview.holdout_review_status || "customer_feedback_shadow_replay_holdout_review_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>holdout review executed</dt>
            <dd>${formatBooleanGate(customerFeedbackHoldoutReview.holdout_review_executed, "holdout_review_executed")}</dd>
          </div>
          <div>
            <dt>holdout review passed</dt>
            <dd>${formatBooleanGate(customerFeedbackHoldoutReview.holdout_review_passed, "holdout_review_passed")}</dd>
          </div>
          <div>
            <dt>independent holdout cases</dt>
            <dd>${formatCount(customerFeedbackHoldoutReview.independent_holdout_case_count)} <span>independent_holdout_case_count</span></dd>
          </div>
          <div>
            <dt>holdout review 下一验收</dt>
            <dd>${escapeHtml(customerFeedbackHoldoutReview.next_required_artifact || "r12_customer_feedback_shadow_replay_holdout_review")}</dd>
          </div>
          <div>
            <dt>customer validation workflow</dt>
            <dd>${escapeHtml(customerValidationWorkflow.workflow_status || "customer_validation_workflow_status_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>workflow current_stage</dt>
            <dd>${escapeHtml(customerValidationWorkflow.current_stage || "r12_customer_validation_workflow_status")}</dd>
          </div>
          <div>
            <dt>workflow next_action</dt>
            <dd>${escapeHtml(customerValidationWorkflow.next_action || "collect_customer_field_slice_or_wait_for_target_outcome")}</dd>
          </div>
          <div>
            <dt>workflow source_arrived</dt>
            <dd>${formatBooleanGate(customerValidationWorkflow.source_arrived, "source_arrived")}</dd>
          </div>
          <div>
            <dt>workflow blocking artifact</dt>
            <dd>${escapeHtml(customerValidationWorkflow.blocking_artifact_id || "customer_field_slice_submission_or_target_outcome_artifact")}</dd>
          </div>
          <div>
            <dt>customer trial readiness</dt>
            <dd>${escapeHtml(customerTrialReadiness.trial_package_status || "customer_trial_readiness_package_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>trial current_stage</dt>
            <dd>${escapeHtml(customerTrialReadiness.current_stage || "r12_customer_trial_readiness_package")}</dd>
          </div>
          <div>
            <dt>trial template_output_path</dt>
            <dd>${escapeHtml(customerTrialReadiness.template_output_path || "r12-customer-field-slice-template-current-001.csv")}</dd>
          </div>
          <div>
            <dt>trial minimum_case_count</dt>
            <dd>${formatCount(customerTrialReadiness.minimum_case_count)}</dd>
          </div>
          <div>
            <dt>r12_customer_trial_operational_check</dt>
            <dd>${escapeHtml(customerTrialOperational.operational_check_status || "customer_trial_operational_check_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>trial operational ready</dt>
            <dd>${formatBooleanGate(customerTrialOperational.customer_trial_request_operationally_ready, "customer_trial_request_operationally_ready")}</dd>
          </div>
          <div>
            <dt>trial source_registry_resolvable</dt>
            <dd>${formatBooleanGate(customerTrialOperational.source_registry_resolvable, "source_registry_resolvable")}</dd>
          </div>
          <div>
            <dt>trial operator_runbook_declared</dt>
            <dd>${formatBooleanGate(customerTrialOperational.operator_runbook_declared, "operator_runbook_declared")}</dd>
          </div>
          <div>
            <dt>r12_customer_trial_launch_handoff_package</dt>
            <dd>${escapeHtml(customerTrialLaunch.launch_package_status || "customer_trial_launch_handoff_package_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>launch handoff ready</dt>
            <dd>${formatBooleanGate(customerTrialLaunch.launch_handoff_ready, "launch_handoff_ready")}</dd>
          </div>
          <div>
            <dt>r12_customer_trial_launch_packet_export</dt>
            <dd>${escapeHtml(customerTrialPacketExport.packet_export_status || "customer_trial_launch_packet_export_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>packet markdown_export_written</dt>
            <dd>${formatBooleanGate(customerTrialPacketExport.markdown_export_written, "markdown_export_written")}</dd>
          </div>
          <div>
            <dt>packet markdown_output_path</dt>
            <dd>${escapeHtml(customerTrialPacketExport.markdown_output_path || "r12-customer-trial-launch-packet-current-001.md")}</dd>
          </div>
          <div>
            <dt>packet delivery</dt>
            <dd>
              <a class="artifact-link" href="${escapeHtml(customerTrialPacketHref)}" target="_blank" rel="noopener">打开 launch packet</a>
            </dd>
          </div>
          <div>
            <dt>r12_customer_trial_launch_bundle_verification</dt>
            <dd>${escapeHtml(customerTrialBundleVerification.bundle_verification_status || "customer_trial_launch_bundle_verification_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>launch bundle verified</dt>
            <dd>${formatBooleanGate(customerTrialBundleVerification.launch_bundle_verified, "launch_bundle_verified")}</dd>
          </div>
          <div>
            <dt>bundle resolved_required_item_count</dt>
            <dd>${formatCount(customerTrialBundleVerification.resolved_required_item_count)} / ${formatCount(customerTrialBundleVerification.required_item_count)}</dd>
          </div>
          <div>
            <dt>bundle missing_required_item_ids</dt>
            <dd>${formatList(customerTrialBundleVerification.missing_required_item_ids)}</dd>
          </div>
          <div>
            <dt>r12_customer_field_slice_operator_rehearsal</dt>
            <dd>${escapeHtml(customerFieldOperatorRehearsal.operator_rehearsal_status || "customer_field_slice_operator_rehearsal_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>operator command rehearsed</dt>
            <dd>${formatBooleanGate(customerFieldOperatorRehearsal.operator_command_rehearsed, "operator_command_rehearsed")}</dd>
          </div>
          <div>
            <dt>sample slice ready</dt>
            <dd>${formatBooleanGate(customerFieldOperatorRehearsal.sample_slice_ready_for_revalidation, "sample_slice_ready_for_revalidation")}</dd>
          </div>
          <div>
            <dt>real customer slice</dt>
            <dd>${formatBooleanGate(customerFieldOperatorRehearsal.real_customer_field_slice_submitted, "real_customer_field_slice_submitted")}</dd>
          </div>
          <div>
            <dt>r12_customer_feedback_loop_operator_rehearsal</dt>
            <dd>${escapeHtml(customerFeedbackLoopRehearsal.feedback_loop_rehearsal_status || "customer_feedback_loop_operator_rehearsal_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>L22 intake rehearsal</dt>
            <dd>${formatBooleanGate(customerFeedbackLoopRehearsal.l22_intake_validator_executed, "l22_intake_validator_executed")}</dd>
          </div>
          <div>
            <dt>L23 field metrics rehearsal</dt>
            <dd>${formatBooleanGate(customerFeedbackLoopRehearsal.l23_field_revalidation_executed, "l23_field_revalidation_executed")}</dd>
          </div>
          <div>
            <dt>L24 feedback candidate rehearsal</dt>
            <dd>${formatBooleanGate(customerFeedbackLoopRehearsal.l24_feedback_candidates_generated, "l24_feedback_candidates_generated")}</dd>
          </div>
          <div>
            <dt>L25 shadow replay rehearsal</dt>
            <dd>${formatBooleanGate(customerFeedbackLoopRehearsal.l25_shadow_replay_executed, "l25_shadow_replay_executed")}</dd>
          </div>
          <div>
            <dt>L26 synthetic holdout rehearsal</dt>
            <dd>${formatBooleanGate(customerFeedbackLoopRehearsal.l26_synthetic_holdout_review_executed, "l26_synthetic_holdout_review_executed")}</dd>
          </div>
          <div>
            <dt>r12_customer_trial_evidence_ledger</dt>
            <dd>${escapeHtml(customerTrialEvidenceLedger.ledger_status || "customer_trial_evidence_ledger_boundary 未提供")}</dd>
          </div>
          <div>
            <dt>customer visible evidence</dt>
            <dd>${formatCount(customerTrialEvidenceLedger.customer_visible_readiness_evidence_count)}</dd>
          </div>
          <div>
            <dt>operator rehearsal evidence</dt>
            <dd>${formatCount(customerTrialEvidenceLedger.operator_only_rehearsal_evidence_count)}</dd>
          </div>
          <div>
            <dt>blocking_gap_count</dt>
            <dd>${formatCount(customerTrialEvidenceLedger.blocking_gap_count)}</dd>
          </div>
        </dl>
        <p>R12 当前只能作为次级迁移证据展示，主决策仍来自 guarded baseline，真实客户 outcome 回流前不进入 runtime default。</p>
      </div>
    </article>
  `;
}

function statusPill(label, status) {
  return `
    <div class="status-pill ${statusClass(status)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(SUPPORT_LABELS[status] || status)}</strong>
    </div>
  `;
}

function metricCard(label, value, status, detail) {
  return `
    <article class="metric-card">
      <div>
        <p>${escapeHtml(label)}</p>
        <strong>${escapeHtml(value)}</strong>
      </div>
      <span class="support-tag ${statusClass(status)}">${escapeHtml(SUPPORT_LABELS[status] || status || "未提供")}</span>
      <small>${escapeHtml(detail)}</small>
    </article>
  `;
}

function renderCaseRow(caseItem, intervalCases) {
  const interval = intervalCases.find((item) => item.source_key === caseItem.source_key) || {};
  const riskInterval = interval.risk_interval || {};
  const containsObserved = Boolean(riskInterval.contains_observed);
  const observed = toNumber(interval.observed_reject_proxy);
  const lower = toNumber(riskInterval.lower);
  const upper = toNumber(riskInterval.upper);
  const left = clampPercent(lower);
  const width = Math.max(1, clampPercent(upper) - left);
  const marker = clampPercent(observed);

  return `
    <div class="case-row">
      <div class="case-meta">
        <h3>${escapeHtml(caseName(caseItem.source_key))}</h3>
        <div class="case-badges">
          <span class="${caseItem.matches_outcome ? "good" : "bad"}">${caseItem.matches_outcome ? "方向命中" : "方向偏离"}</span>
          <span>${escapeHtml(directionLabel(caseItem.trend_direction))}</span>
          <span>outcome ${escapeHtml(directionLabel(caseItem.outcome_direction))}</span>
        </div>
      </div>
      <div class="interval-visual" aria-label="${escapeHtml(caseName(caseItem.source_key))} 风险区间">
        <div class="interval-scale">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
        <div class="interval-track">
          <div class="interval-band ${containsObserved ? "contains" : "miss"}" style="left: ${left}%; width: ${width}%"></div>
          <div class="observed-marker" style="left: ${marker}%"></div>
        </div>
        <div class="interval-summary">
          <span>区间 ${formatPercent(lower)} - ${formatPercent(upper)}</span>
          <strong class="${containsObserved ? "good-text" : "bad-text"}">${containsObserved ? "覆盖 observed proxy" : "未覆盖 observed proxy"}</strong>
          <span>observed ${formatPercent(observed)}</span>
        </div>
      </div>
    </div>
  `;
}

function renderDistribution(distribution) {
  const falseAlarm = clampPercent(distribution.false_alarm_rate);
  const ranking = clampPercent(distribution.risk_ranking_quality);
  return `
    <div class="gauge-stack">
      ${gaugeRow("误报率", falseAlarm, "bad")}
      ${gaugeRow("排序质量", ranking, "good")}
    </div>
    <p class="panel-note">当前风险分布具备诊断价值，但误报仍高，不能作为默认上线策略。</p>
  `;
}

function gaugeRow(label, percent, tone) {
  return `
    <div class="gauge-row">
      <div class="gauge-label">
        <span>${escapeHtml(label)}</span>
        <strong>${formatPercent(percent / 100)}</strong>
      </div>
      <div class="gauge-track">
        <div class="gauge-fill ${tone}" style="width: ${percent}%"></div>
      </div>
    </div>
  `;
}

function renderSegmentGroup(group) {
  return `
    <section class="segment-group">
      <div class="segment-group-heading">
        <h3>${escapeHtml(caseName(group.source_key))}</h3>
        <span class="support-tag ${statusClass(group.support_status)}">${escapeHtml(SUPPORT_LABELS[group.support_status] || group.support_status)}</span>
      </div>
      <div class="segment-list">
        ${(group.segments || []).map(renderSegment).join("")}
      </div>
    </section>
  `;
}

function renderSegment(segment) {
  return `
    <div class="segment-item">
      <div>
        <strong>${escapeHtml(segment.segment_id)}</strong>
        <span>reject shift ${formatSignedPercent(segment.delta_reject)}</span>
      </div>
      <p>${(segment.mechanisms || []).map(escapeHtml).join(" / ")}</p>
    </div>
  `;
}

function renderMechanism(mechanism) {
  const status = mechanism?.support_status || "diagnostic_only";
  const claim = mechanism?.claim_status || "diagnostic_only";
  return `
    <div class="mechanism-box">
      <dl>
        <div>
          <dt>支撑状态</dt>
          <dd>${escapeHtml(SUPPORT_LABELS[status] || status)}</dd>
        </div>
        <div>
          <dt>声明状态</dt>
          <dd>${escapeHtml(SUPPORT_LABELS[claim] || claim)}</dd>
        </div>
      </dl>
      <p>机制解释当前用于定位风险路径和异常群体，不用于宣称 field validated 或 runtime default。</p>
    </div>
  `;
}

function renderResearchSupport(researchSupport, supportGapLedger, researchNextTasks) {
  const coverage = researchSupport.support_coverage || {};
  const summary = researchSupport.product_claim_support_summary || {};
  const executionSummary = researchSupport.research_next_task_execution_summary || {};
  return `
    <div class="research-summary">
      <div>
        <span>部分支撑</span>
        <strong>${escapeHtml(coverage.partial_value_count ?? 0)}</strong>
      </div>
      <div>
        <span>诊断支撑</span>
        <strong>${escapeHtml(coverage.diagnostic_value_count ?? 0)}</strong>
      </div>
      <div>
        <span>阻断项</span>
        <strong>${escapeHtml(coverage.blocked_value_count ?? 0)}</strong>
      </div>
      <div>
        <span>完整支撑</span>
        <strong>${summary.overall_product_core_value_supported ? "是" : "否"}</strong>
      </div>
      <div>
        <span>任务执行</span>
        <strong>${escapeHtml(executionSummary.task_count ?? researchNextTasks.length)}</strong>
      </div>
    </div>
    <div class="ledger-table" role="table" aria-label="Research 支撑缺口">
      <div class="ledger-head" role="row">
        <span>Product value</span>
        <span>当前状态</span>
        <span>差距</span>
        <span>下一步</span>
      </div>
      ${supportGapLedger.map(renderLedgerRow).join("")}
    </div>
    <div class="task-list">
      ${researchNextTasks.map(renderResearchTask).join("")}
    </div>
  `;
}

function renderLedgerRow(item) {
  return `
    <div class="ledger-row" role="row">
      <strong>${escapeHtml(item.product_value)}</strong>
      <span class="support-tag ${statusClass(item.current_support_status)}">${escapeHtml(SUPPORT_LABELS[item.current_support_status] || item.current_support_status)}</span>
      <span>${escapeHtml(formatLedgerGap(item.gap_to_target))}</span>
      <span>${escapeHtml(item.next_research_task_id)}</span>
    </div>
  `;
}

function renderResearchTask(task) {
  return `
    <section class="task-row">
      <div>
        <strong>${escapeHtml(task.task_id)}</strong>
        <span>${escapeHtml((task.unblocks_product_values || []).join(" / "))}</span>
      </div>
      <p>${escapeHtml(task.goal)}</p>
      <small>${escapeHtml(task.acceptance_criteria)}</small>
    </section>
  `;
}

function renderReadiness(gates) {
  const rows = Object.entries(gates).map(([key, value]) => `
    <tr>
      <th>${escapeHtml(key)}</th>
      <td><span class="gate ${value ? "pass" : "blocked"}">${value ? "通过" : "未通过"}</span></td>
    </tr>
  `);
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Gate</th><th>状态</th></tr>
        </thead>
        <tbody>${rows.join("")}</tbody>
      </table>
    </div>
  `;
}

function renderBlockedClaims(blockedClaims) {
  return `
    <ul class="blocked-list">
      ${blockedClaims.slice(0, 12).map((claim) => `<li>${escapeHtml(claim)}</li>`).join("")}
    </ul>
  `;
}

function renderSources(sourceRefs, registry, endpoints) {
  const registryRows = registry.map((entry) => `
    <tr>
      <th>${escapeHtml(entry.artifact_id)}</th>
      <td>${escapeHtml(entry.path)}</td>
    </tr>
  `);
  const endpointRows = endpoints
    .filter((endpoint) =>
      ["frontend_demo", "customer_value_report", "product_readiness"].includes(endpoint.endpoint_id)
      || endpoint.path === "/r6/product/r12-transfer-evidence"
    )
    .map((endpoint) => `
      <tr>
        <th>${escapeHtml(endpoint.endpoint_id)}</th>
        <td>${escapeHtml(endpoint.path)}</td>
      </tr>
    `);
  return `
    <div class="source-summary">
      <p>${sourceRefs.map(escapeHtml).join(" / ")}</p>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Artifact</th><th>路径</th></tr>
        </thead>
        <tbody>${registryRows.join("")}</tbody>
      </table>
    </div>
    <div class="table-wrap compact-table">
      <table>
        <thead>
          <tr><th>Endpoint</th><th>路径</th></tr>
        </thead>
        <tbody>${endpointRows.join("")}</tbody>
      </table>
    </div>
  `;
}

function renderLoadError(error) {
  app.innerHTML = `
    <section class="load-error">
      <p class="eyebrow">Fail Closed</p>
      <h1>artifact 加载失败</h1>
      <p>本页面不展示静态兜底结论；请先确认 R6 current artifacts 已生成并从仓库根目录启动服务。</p>
      <pre>${escapeHtml(error.message)}</pre>
    </section>
  `;
}

function statusClass(status) {
  if (!status) return "status-muted";
  if (status.includes("blocked") || status.includes("failed") || status.includes("false_alarm")) return "status-bad";
  if (status.includes("partial") || status.includes("diagnostic") || status.includes("guarded")) return "status-warn";
  if (status.includes("ready") || status.includes("passed")) return "status-good";
  return "status-muted";
}

function caseName(sourceKey) {
  return CASE_NAMES[sourceKey] || sourceKey || "未命名 case";
}

function directionLabel(direction) {
  if (direction === "risk_up") return "风险上升";
  if (direction === "risk_down") return "风险下降";
  return direction || "未提供";
}

function formatPercent(value) {
  const number = toNumber(value);
  if (number === null) return "未提供";
  return `${(number * 100).toFixed(1)}%`;
}

function formatSignedPercent(value) {
  const number = toNumber(value);
  if (number === null) return "未提供";
  const sign = number > 0 ? "+" : "";
  return `${sign}${(number * 100).toFixed(1)}%`;
}

function formatLedgerGap(value) {
  if (Number.isFinite(value)) {
    return value === 0 ? "已达标" : `差 ${formatPercent(value)}`;
  }
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${Number.isFinite(item) ? formatPercent(item) : item}`)
      .join(" / ");
  }
  return value || "未提供";
}

function formatCount(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "0";
  }
  return String(Number(value));
}

function formatList(value) {
  if (!Array.isArray(value) || value.length === 0) return "无";
  return value.map((item) => String(item)).join(" / ");
}

function formatSignedNumber(value) {
  const number = toNumber(value);
  if (number === null) return "未提供";
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(6)}`;
}

function formatBooleanGate(value, fallback) {
  if (value === true) return "通过";
  if (value === false) return `未覆盖: ${fallback}`;
  return fallback;
}

function clampPercent(value) {
  const number = toNumber(value);
  if (number === null) return 0;
  return Math.max(0, Math.min(100, number * 100));
}

function toNumber(value) {
  return Number.isFinite(value) ? value : null;
}

function uniqueItems(items) {
  return [...new Set(items.filter(Boolean))];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
