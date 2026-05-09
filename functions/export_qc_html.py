"""Standalone function for generating a self-contained HTML QC report."""

import html
import pathlib


_TOOL_LABELS = {
    "barcode_complexity": "Barcode Complexity",
    "oligo_recovery": "Oligo Recovery",
    "synthesis_error_profile": "Synthesis Error Profile",
    "barcode_collision_analysis": "Barcode Collision Analysis",
    "barcode_uniformity": "Barcode Uniformity",
    "plasmid_depth_summary": "Plasmid Depth",
    "gc_content_bias": "GC Content Bias",
    "variant_family_coverage": "Variant Family Coverage",
}

_CSS = """
body{font-family:system-ui,sans-serif;margin:2rem;color:#1a1a1a}
h1{margin-bottom:.25rem}
.banner{padding:.75rem 1.25rem;border-radius:6px;font-size:1.1rem;font-weight:600;margin-bottom:1.5rem}
.pass{background:#d4edda;color:#155724;border:1px solid #c3e6cb}
.fail{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}
table{border-collapse:collapse;width:100%;margin-bottom:2rem}
th,td{text-align:left;padding:.5rem .75rem;border:1px solid #dee2e6}
th{background:#f8f9fa;font-weight:600}
tr:nth-child(even){background:#f8f9fa}
.ok{color:#155724;font-weight:600}
.ng{color:#721c24;font-weight:600}
details{margin-bottom:1rem}
summary{cursor:pointer;font-weight:600;padding:.4rem 0}
pre{background:#f8f9fa;padding:1rem;border-radius:4px;overflow-x:auto;font-size:.85rem}
"""


def _esc(s):
    return html.escape(str(s))


def export_qc_html(qc_results, output_path=None):
    """
    Generate a self-contained HTML QC report from library_summary_report output.

    Builds a single HTML document (no external CSS/JS dependencies) that
    shows a pass/fail banner, a per-check summary table, and collapsible
    detail sections with the raw scalar metrics for each QC tool.

    Args:
        qc_results (dict): Output of
            ``creseq_mcp.qc.library.library_summary_report()``.  The dict
            must include a ``"_report"`` key whose value is a dict with at
            least two fields:

            - ``overall_pass`` (bool): ``True`` if all checks passed.
            - ``failed_checks`` (list[str]): Tool names of checks that
              failed (empty list when ``overall_pass`` is ``True``).

            All other keys are treated as individual QC tool results.
            Each tool value may be a dict of scalar metrics, a
            ``(DataFrame, metrics_dict)`` tuple, or any object with a
            ``__str__`` representation.
        output_path (str or pathlib.Path or None): If provided, the HTML
            document is written to this path in UTF-8 encoding. Parent
            directories must already exist. Default ``None`` (no file
            written).

    Returns:
        str: Self-contained HTML document as a string, beginning with
        ``<!DOCTYPE html>``.

    Raises:
        TypeError: if ``qc_results`` is not a dict.
        ValueError: if ``qc_results`` is empty.
        ValueError: if ``qc_results`` is missing the ``"_report"`` key.
    """
    if not isinstance(qc_results, dict):
        raise TypeError(
            f"qc_results must be a dict, got {type(qc_results).__name__}"
        )
    if not qc_results:
        raise ValueError("qc_results is empty — nothing to report")
    if "_report" not in qc_results:
        raise ValueError(
            "qc_results is missing the '_report' key. "
            "Pass the direct return value of library_summary_report()."
        )

    report = qc_results["_report"]
    overall_pass = bool(report.get("overall_pass", False))
    failed_checks = report.get("failed_checks", [])

    banner_class = "pass" if overall_pass else "fail"
    banner_text = (
        "✅ Library QC passed — all checks within thresholds"
        if overall_pass
        else f"❌ Library QC failed — {len(failed_checks)} check(s) did not pass: "
        + ", ".join(_TOOL_LABELS.get(c, c) for c in failed_checks)
    )

    tool_keys = [k for k in qc_results if k != "_report"]

    rows_html = []
    for key in tool_keys:
        label = _TOOL_LABELS.get(key, key.replace("_", " ").title())
        passed = key not in failed_checks
        status_html = (
            '<span class="ok">PASS</span>'
            if passed
            else '<span class="ng">FAIL</span>'
        )
        rows_html.append(
            f"<tr><td>{_esc(label)}</td><td>{status_html}</td></tr>"
        )

    summary_table = (
        "<table><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>"
        + "".join(rows_html)
        + "</tbody></table>"
    )

    details_sections = []
    for key in tool_keys:
        label = _TOOL_LABELS.get(key, key.replace("_", " ").title())
        value = qc_results[key]

        if isinstance(value, tuple) and len(value) == 2:
            _, metrics = value
        elif isinstance(value, dict):
            metrics = value
        else:
            metrics = {"result": str(value)}

        if isinstance(metrics, dict):
            metrics_lines = "\n".join(
                f"  {k}: {v}" for k, v in metrics.items()
            )
        else:
            metrics_lines = str(metrics)

        details_sections.append(
            f"<details><summary>{_esc(label)}</summary>"
            f"<pre>{_esc(metrics_lines)}</pre></details>"
        )

    body_parts = [
        f'<div class="banner {banner_class}">{banner_text}</div>',
        "<h2>Check Summary</h2>",
        summary_table,
        "<h2>Detailed Results</h2>",
        *details_sections,
    ]

    doc = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>CRE-seq Library QC Report</title>"
        f"<style>{_CSS}</style></head>"
        "<body>"
        "<h1>CRE-seq Library QC Report</h1>"
        + "\n".join(body_parts)
        + "</body></html>"
    )

    if output_path is not None:
        pathlib.Path(output_path).write_text(doc, encoding="utf-8")

    return doc
