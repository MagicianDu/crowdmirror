# DCL-PRS L3 Official Public Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the cross-domain data gate from access audit to official public-use file evidence without overstating authenticated Eurobarometer access.

**Architecture:** Split official data handling into two artifacts. `gss_public_use_download_manifest` verifies a local official GSS public-use ZIP by size/hash. `official_public_use_file_probe` records source-level availability: GSS direct public ZIP reachable/downloaded, Eurobarometer GESIS catalogue requires login/registration and is not downloaded.

**Tech Stack:** Python standard library, `pytest`, `curl` for external download, ignored `data/raw/` for downloaded files.

---

## Task 1: GSS Public-Use Download Manifest

**Files:**
- Create: `experiments/dcl_prs_gss_public_use_download.py`
- Test: `tests/test_dcl_prs_gss_public_use_download.py`

- [ ] Write tests that create a small local file and assert the manifest records source URL, byte count, sha256, and `download_verified=true`.
- [ ] Implement manifest builder and CLI accepting `--source-path`.
- [ ] Keep this artifact source-agnostic enough for the real downloaded GSS ZIP.

## Task 2: Official Public-Use File Probe

**Files:**
- Create: `experiments/dcl_prs_official_public_use_file_probe.py`
- Test: `tests/test_dcl_prs_official_public_use_file_probe.py`

- [ ] Write tests asserting GSS direct download is available and Eurobarometer remains `login_required_not_downloaded`.
- [ ] Implement deterministic source probe from current official access evidence.
- [ ] Accept optional GSS download manifest and mark GSS as `download_verified` only when the manifest is passed.

## Task 3: Gate Upgrade

**Files:**
- Modify: `experiments/dcl_prs_gate_index.py`
- Modify: `tests/test_dcl_prs_gate_index.py`

- [ ] Add L3 artifact parameters.
- [ ] Close `cross_domain_microdata_download_missing` only partially: GSS can be marked downloaded, Eurobarometer remains open.
- [ ] Required next gates should include `complete_eurobarometer_authenticated_download` and `bind_gss_public_use_variables_to_policy_tasks`.

## Task 4: Generate Real Local GSS Evidence

**Files:**
- No committed binary files.

- [ ] Download `https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/2024_stata.zip` into `data/raw/dcl_prs/gss/2024_stata.zip`.
- [ ] Generate `experiments/results/dcl_prs_gss_public_use_download/dcl-prs-gss-public-use-download-current-001.json`.
- [ ] Generate `experiments/results/dcl_prs_official_public_use_file_probe/dcl-prs-official-public-use-file-probe-current-001.json`.
- [ ] Regenerate `experiments/results/dcl_prs_gate_index/dcl-prs-gate-current-001.json`.

## Task 5: Verification and Commit

- [ ] Run `pytest tests/test_dcl_prs_*.py -q`.
- [ ] Run `pytest -q`.
- [ ] Run `git diff --check`.
- [ ] Commit only L3 plan, modules, tests, and gate changes.

## Claim Boundary

- GSS direct public-use file download can be claimed only for the downloaded local ZIP and its checksum.
- Eurobarometer cannot be claimed as downloaded until GESIS login/registration and the selected data catalogue file are completed.
- No L3 artifact proves DCL-PRS model quality or CCF-A readiness.
