from __future__ import annotations

import argparse
import http.cookiejar
import csv
import json
import re
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.lcdu_anes_public_microdata_ingestion import (
    ANES_SDA_ANALYSIS_URL,
    SELECTED_VARIABLES,
)


SDA_ANALYSIS_POST_URL = "https://sda.berkeley.edu/sdaweb/analysis/index.jsf"


def fetch_anes_sda_subset_csv(
    *,
    output_csv: str | Path,
    variables: list[str] | None = None,
    analysis_url: str = ANES_SDA_ANALYSIS_URL,
) -> dict[str, object]:
    variables = variables or SELECTED_VARIABLES
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    initial_text = _urlopen_text(opener, analysis_url, timeout=30)
    view_state = _extract_view_state_from_html(initial_text)

    opened_text = _urlopen_text(
        opener,
        SDA_ANALYSIS_POST_URL,
        data={
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "top-form:cb-subset",
            "javax.faces.partial.execute": "top-form",
            "javax.faces.partial.render": "top-form mainPanel vsf:varselectpanel",
            "top-form:cb-subset": "top-form:cb-subset",
            "top-form": "top-form",
            "top-form:sec508": "false",
            "javax.faces.ViewState": view_state,
        },
        headers={"Faces-Request": "partial/ajax"},
        timeout=40,
    )
    view_state = _extract_view_state_from_partial(opened_text, view_state)

    form = {
        "subsetWizardForm": "subsetWizardForm",
        "subsetWizardForm:subsetTabview:j_idt1749": "CSV",
        "subsetWizardForm:subsetTabview:varTextarea": " ".join(variables),
        "subsetWizardForm:subsetTabview:filters": "",
        "subsetWizardForm:subsetTabview:subsetTree_selection": "",
        "subsetWizardForm:subsetTabview:subsetTree_scrollState": "0,0",
        "subsetWizardForm:subsetTabview_activeIndex": "2",
    }
    changed_text = _urlopen_text(
        opener,
        SDA_ANALYSIS_POST_URL,
        data={
            **form,
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "subsetWizardForm:subsetTabview:varTextarea",
            "javax.faces.partial.execute": "subsetWizardForm:subsetTabview:varTextarea",
            "javax.faces.partial.render": "subsetWizardForm:subsetTabview:varTextarea",
            "javax.faces.behavior.event": "valueChange",
            "javax.faces.partial.event": "change",
            "javax.faces.ViewState": view_state,
        },
        headers={"Faces-Request": "partial/ajax"},
        timeout=40,
    )
    view_state = _extract_view_state_from_partial(changed_text, view_state)

    form["subsetWizardForm:subsetTabview_activeIndex"] = "3"
    created_text = _urlopen_text(
        opener,
        SDA_ANALYSIS_POST_URL,
        data={
            **form,
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "subsetWizardForm:subsetTabview:j_idt1829",
            "javax.faces.partial.execute": "subsetWizardForm",
            "javax.faces.partial.render": "subsetWizardForm:subsetTabview:fileLinksPanel",
            "subsetWizardForm:subsetTabview:j_idt1829": (
                "subsetWizardForm:subsetTabview:j_idt1829"
            ),
            "javax.faces.ViewState": view_state,
        },
        headers={"Faces-Request": "partial/ajax"},
        timeout=60,
    )
    if "Subsetting Completed" not in created_text:
        raise RuntimeError("SDA subset creation did not complete")
    view_state = _extract_view_state_from_partial(created_text, view_state)

    downloaded_content = _urlopen_bytes(
        opener,
        SDA_ANALYSIS_POST_URL,
        data={
            **form,
            "subsetWizardForm:subsetTabview:j_idt1835": (
                "subsetWizardForm:subsetTabview:j_idt1835"
            ),
            "javax.faces.ViewState": view_state,
        },
        timeout=60,
    )
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(downloaded_content)
    row_count = _csv_row_count(output_path)
    return {
        "output_csv": str(output_path),
        "row_count": row_count,
        "selected_variable_count": len(variables),
        "source_url": analysis_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-csv",
        default="data/raw/anes_2024/anes2024_sda_lcdu_subset.csv",
    )
    parser.add_argument(
        "--variables",
        nargs="*",
        default=SELECTED_VARIABLES,
    )
    args = parser.parse_args()
    result = fetch_anes_sda_subset_csv(
        output_csv=args.output_csv,
        variables=args.variables,
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


def _extract_view_state_from_html(html: str) -> str:
    match = re.search(r'name="javax.faces.ViewState"[^>]+value="([^"]+)"', html)
    if not match:
        raise RuntimeError("SDA page missing JSF view state")
    return match.group(1)


def _extract_view_state_from_partial(xml_text: str, fallback: str) -> str:
    matches = re.findall(
        r'<update id="j_id1:javax.faces.ViewState:[^"]+"><!\[CDATA\[([^\]]+)\]\]></update>',
        xml_text,
    )
    return matches[-1] if matches else fallback


def _urlopen_text(
    opener,
    url: str,
    *,
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int,
) -> str:
    return _urlopen_bytes(
        opener,
        url,
        data=data,
        headers=headers,
        timeout=timeout,
    ).decode("utf-8")


def _urlopen_bytes(
    opener,
    url: str,
    *,
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int,
) -> bytes:
    encoded_data = None
    request_headers = {"User-Agent": "lcdu-anes-sda-subset-fetch/1.0"}
    if headers:
        request_headers.update(headers)
    if data is not None:
        encoded_data = urlencode(data).encode("utf-8")
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=encoded_data, headers=request_headers)
    with opener.open(request, timeout=timeout) as response:
        return response.read()


def _csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _ in csv.DictReader(handle, skipinitialspace=True))


if __name__ == "__main__":
    raise SystemExit(main())
