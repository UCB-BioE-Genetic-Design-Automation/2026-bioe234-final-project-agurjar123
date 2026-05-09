"""Tests for functions.export_qc_html."""

import pathlib

import pytest

from functions import export_qc_html


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_qc_results(overall_pass=True, failed_checks=None, include_tool_data=True):
    """Build a minimal qc_results dict that mirrors library_summary_report output."""
    if failed_checks is None:
        failed_checks = []
    result = {
        "_report": {
            "overall_pass": overall_pass,
            "failed_checks": failed_checks,
        }
    }
    if include_tool_data:
        result["barcode_complexity"] = {
            "median_barcodes_per_oligo": 20.5,
            "fraction_oligos_above_min": 0.97,
        }
        result["oligo_recovery"] = {
            "n_recovered": 490,
            "n_designed": 500,
            "recovery_fraction": 0.98,
        }
    return result


@pytest.fixture
def passing_qc():
    return _make_qc_results(overall_pass=True, failed_checks=[])


@pytest.fixture
def failing_qc():
    return _make_qc_results(
        overall_pass=False,
        failed_checks=["barcode_complexity", "oligo_recovery"],
    )


# ---------------------------------------------------------------------------
# Return type and structure
# ---------------------------------------------------------------------------


def test_returns_string(passing_qc):
    result = export_qc_html(passing_qc)
    assert isinstance(result, str)


def test_html_starts_with_doctype(passing_qc):
    result = export_qc_html(passing_qc)
    assert result.startswith("<!DOCTYPE html>")


def test_html_is_self_contained(passing_qc):
    result = export_qc_html(passing_qc)
    assert "<html" in result
    assert "<head>" in result or "<head " in result
    assert "<body>" in result or "<body " in result
    assert "<style>" in result  # inline CSS, no external stylesheet link


# ---------------------------------------------------------------------------
# Pass/fail banners
# ---------------------------------------------------------------------------


def test_pass_banner_present_when_all_checks_pass(passing_qc):
    result = export_qc_html(passing_qc)
    assert "pass" in result.lower()
    assert "✅" in result or "passed" in result.lower()


def test_fail_banner_present_when_checks_fail(failing_qc):
    result = export_qc_html(failing_qc)
    assert "fail" in result.lower()
    assert "❌" in result or "failed" in result.lower()


def test_fail_banner_names_failed_checks(failing_qc):
    result = export_qc_html(failing_qc)
    assert "Barcode Complexity" in result or "barcode_complexity" in result
    assert "Oligo Recovery" in result or "oligo_recovery" in result


# ---------------------------------------------------------------------------
# Check table contents
# ---------------------------------------------------------------------------


def test_html_contains_barcode_complexity_section(passing_qc):
    result = export_qc_html(passing_qc)
    assert "barcode_complexity" in result.lower() or "Barcode Complexity" in result


def test_html_contains_oligo_recovery_section(passing_qc):
    result = export_qc_html(passing_qc)
    assert "oligo_recovery" in result.lower() or "Oligo Recovery" in result


def test_html_contains_pass_status_for_passing_checks(passing_qc):
    result = export_qc_html(passing_qc)
    assert "PASS" in result


def test_html_contains_fail_status_for_failing_checks(failing_qc):
    result = export_qc_html(failing_qc)
    assert "FAIL" in result


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def test_writes_file_when_output_path_given(passing_qc, tmp_path):
    out = tmp_path / "report.html"
    result = export_qc_html(passing_qc, output_path=out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content == result


def test_does_not_create_file_when_output_path_is_none(passing_qc, tmp_path):
    export_qc_html(passing_qc, output_path=None)
    assert list(tmp_path.iterdir()) == []


def test_output_path_accepts_string(passing_qc, tmp_path):
    out = str(tmp_path / "report.html")
    export_qc_html(passing_qc, output_path=out)
    assert pathlib.Path(out).exists()


# ---------------------------------------------------------------------------
# Tuple-valued tool results
# ---------------------------------------------------------------------------


def test_handles_tuple_valued_tool_results():
    import pandas as pd
    qc = {
        "_report": {"overall_pass": True, "failed_checks": []},
        "barcode_complexity": (
            pd.DataFrame({"barcode": ["ACGT"], "count": [5]}),
            {"median_barcodes_per_oligo": 22.0, "fraction_above_min": 0.98},
        ),
    }
    result = export_qc_html(qc)
    assert isinstance(result, str)
    assert "<!DOCTYPE html>" in result


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_raises_type_error_on_non_dict():
    with pytest.raises(TypeError, match="dict"):
        export_qc_html("not a dict")


def test_raises_value_error_on_empty_dict():
    with pytest.raises(ValueError, match="empty"):
        export_qc_html({})


def test_raises_value_error_on_missing_report_key():
    with pytest.raises(ValueError, match="_report"):
        export_qc_html({"barcode_complexity": {"median": 20}})
