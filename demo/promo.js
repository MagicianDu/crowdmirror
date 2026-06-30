const PROMO_ARTIFACTS = {
  productSupportGate:
    "../experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json",
  customerValueReport:
    "../experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json",
  r13StructuredRollout:
    "../experiments/results/r13_llm_rule_structured_rollout/r13-llm-rule-structured-rollout-current-001.json",
};

window.addEventListener("DOMContentLoaded", () => {
  loadPromoArtifacts()
    .then(renderPromoEvidence)
    .catch(renderPromoError);
});

async function loadPromoArtifacts() {
  const entries = await Promise.all(
    Object.entries(PROMO_ARTIFACTS).map(async ([key, path]) => {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${key} artifact 加载失败: ${response.status}`);
      }
      return [key, await response.json()];
    }),
  );
  return Object.fromEntries(entries);
}

function renderPromoEvidence({ productSupportGate, customerValueReport, r13StructuredRollout }) {
  const scope = productSupportGate.public_data_validation_scope || {};
  const gates = productSupportGate.acceptance_gates || {};
  const r13Gates = r13StructuredRollout.acceptance_gates || {};
  const r13Population = r13StructuredRollout.synthetic_population || {};
  const r13Llm = r13StructuredRollout.llm_rule_generation || {};
  const r12Evidence =
    (customerValueReport.display_payload || {}).r12_transfer_evidence || {};
  const allowedClaims = [
    "公开数据上测试有效，且指标有 artifact 支撑。",
    "LLM 生成 segment/persona 行为规则，结构化 rollout 已扩展到 1 万+ synthetic individuals。",
    "离线校准与自优化候选已跑通生成、验证、接受或拒绝门禁。",
    "适合受控企业试用和 design partner 反馈。",
  ];
  const blockedClaims = [
    "不承诺精确预测单点结果。",
    "不宣称客户 field validation 已完成。",
    "不把校准更新默认自动上线。",
  ];

  setText(
    "promo-public-claim",
    scope.public_data_effectiveness_claim_allowed
      ? "tested_effective_on_public_data_guarded"
      : "blocked",
  );
  setText(
    "promo-calibration",
    gates.r12_transfer_positive_guarded && gates.r12_independent_hindcast_revalidation_passed
      ? "离线校准与自优化候选已通过公开数据门禁"
      : "等待公开数据门禁",
  );
  setText(
    "promo-runtime",
    gates.runtime_default_allowed ? "允许" : "关闭，人工确认后进入试用流程",
  );
  setText(
    "promo-r13-scale",
    r13Gates.synthetic_population_10k_met && r13Gates.llm_calls_not_per_individual
      ? `${r13Population.individual_count} synthetic / LLM calls=${r13Llm.llm_call_count}`
      : "等待 rollout 证据",
  );
  renderList("promo-allowed-claims", allowedClaims);
  renderList(
    "promo-blocked-claims",
    blockedClaims.concat((r12Evidence.blocked_claims || []).slice(0, 3)),
  );
}

function renderPromoError(error) {
  setText("promo-public-claim", "artifact 加载失败");
  setText("promo-calibration", "artifact 加载失败");
  setText("promo-r13-scale", "artifact 加载失败");
  setText("promo-runtime", error.message);
}

function renderList(id, items) {
  const node = document.getElementById(id);
  if (!node) return;
  node.innerHTML = items
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
