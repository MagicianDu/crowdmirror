const ARTIFACTS = {
  customerValueReport:
    "/experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json",
  valueSupport:
    "/experiments/results/r6_research_product_value_support/r6-research-product-value-support-current-001.json",
  readinessIndex:
    "/experiments/results/r6_product_readiness_index/r6-product-readiness-index-current-001.json",
  apiManifest:
    "/experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json",
};

const SECTION_LABELS = [
  "趋势方向",
  "风险区间",
  "风险分布",
  "异常群体",
  "机制解释",
  "研究支撑",
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
}

function renderR12TransferEvidence(evidence) {
  if (!evidence) return "";
  const metrics = evidence.metrics || {};
  const summary = evidence.evidence_summary || {};
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

function formatSignedNumber(value) {
  const number = toNumber(value);
  if (number === null) return "未提供";
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(6)}`;
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
