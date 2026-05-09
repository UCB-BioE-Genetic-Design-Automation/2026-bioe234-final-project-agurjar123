"""Tests for functions.format_activity_summary_table."""

import pandas as pd
import pytest

from functions import format_activity_summary_table


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_df():
    """Minimal activity DataFrame with all standard columns."""
    return pd.DataFrame({
        "element_id": [f"ENSR{i:05d}" for i in range(10)],
        "chrom":      ["chr1"] * 10,
        "log2_ratio": [float(i - 5) for i in range(10)],
        "fdr":        [0.001 * (i + 1) for i in range(10)],
        "pval":       [0.01 * (i + 1) for i in range(10)],
        "active":     [i >= 5 for i in range(10)],
        "designed_category": ["test_element"] * 10,
    })


@pytest.fixture
def oligo_id_df():
    """Activity DataFrame that uses oligo_id instead of element_id."""
    return pd.DataFrame({
        "oligo_id":   [f"oligo_{i:04d}" for i in range(4)],
        "log2_ratio": [1.0, 2.0, -1.0, -2.0],
        "fdr":        [0.01, 0.02, 0.5, 0.8],
        "active":     [True, True, False, False],
    })


# ---------------------------------------------------------------------------
# Standard cases
# ---------------------------------------------------------------------------


def test_returns_dataframe(base_df):
    result = format_activity_summary_table(base_df)
    assert isinstance(result, pd.DataFrame)


def test_index_is_reset(base_df):
    result = format_activity_summary_table(base_df, activity_filter="Active only")
    assert list(result.index) == list(range(len(result)))


def test_all_filter_returns_all_rows(base_df):
    result = format_activity_summary_table(base_df, activity_filter="All")
    assert len(result) == len(base_df)


def test_active_only_filter(base_df):
    result = format_activity_summary_table(base_df, activity_filter="Active only")
    assert len(result) == base_df["active"].sum()
    assert result["active"].all()


def test_inactive_only_filter(base_df):
    result = format_activity_summary_table(base_df, activity_filter="Inactive only")
    assert len(result) == (~base_df["active"]).sum()
    assert not result["active"].any()


def test_search_text_filters_by_element_id(base_df):
    # "ENSR0000" is a prefix of all 10 IDs (ENSR00000–ENSR00009)
    result = format_activity_summary_table(base_df, search_text="ENSR0000")
    assert len(result) == 10
    # Narrow search: only ENSR00001 contains "ENSR00001"
    result2 = format_activity_summary_table(base_df, search_text="ENSR00001")
    assert len(result2) == 1
    assert result2.iloc[0]["element_id"] == "ENSR00001"


def test_sort_by_fdr_ascending(base_df):
    result = format_activity_summary_table(base_df, sort_by_fdr=True)
    assert list(result["fdr"]) == sorted(result["fdr"])


def test_sort_by_fdr_false_preserves_original_order(base_df):
    result = format_activity_summary_table(base_df, sort_by_fdr=False)
    assert list(result["element_id"]) == list(base_df["element_id"])


# ---------------------------------------------------------------------------
# Column handling
# ---------------------------------------------------------------------------


def test_renames_oligo_id_to_element_id(oligo_id_df):
    result = format_activity_summary_table(oligo_id_df)
    assert "element_id" in result.columns
    assert "oligo_id" not in result.columns


def test_custom_display_cols(base_df):
    result = format_activity_summary_table(
        base_df, display_cols=["element_id", "log2_ratio"]
    )
    assert list(result.columns) == ["element_id", "log2_ratio"]


def test_missing_display_col_is_silently_skipped(base_df):
    result = format_activity_summary_table(
        base_df, display_cols=["element_id", "nonexistent_col"]
    )
    assert "element_id" in result.columns
    assert "nonexistent_col" not in result.columns


def test_does_not_mutate_input(base_df):
    original_len = len(base_df)
    original_cols = list(base_df.columns)
    format_activity_summary_table(base_df, activity_filter="Active only", sort_by_fdr=True)
    assert len(base_df) == original_len
    assert list(base_df.columns) == original_cols


# ---------------------------------------------------------------------------
# Combined filter + sort
# ---------------------------------------------------------------------------


def test_active_filter_and_sort_combined(base_df):
    result = format_activity_summary_table(
        base_df, activity_filter="Active only", sort_by_fdr=True
    )
    assert result["active"].all()
    assert list(result["fdr"]) == sorted(result["fdr"])


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_raises_type_error_on_non_dataframe():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        format_activity_summary_table({"element_id": [1], "log2_ratio": [1.0]})


def test_raises_value_error_on_missing_log2_ratio():
    df = pd.DataFrame({"element_id": ["e1"], "fdr": [0.01]})
    with pytest.raises(ValueError, match="log2_ratio"):
        format_activity_summary_table(df)


def test_raises_value_error_on_invalid_activity_filter(base_df):
    with pytest.raises(ValueError, match="activity_filter"):
        format_activity_summary_table(base_df, activity_filter="invalid")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_dataframe_returns_empty():
    df = pd.DataFrame({"element_id": pd.Series([], dtype=str), "log2_ratio": pd.Series([], dtype=float)})
    result = format_activity_summary_table(df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_search_text_no_match_returns_empty(base_df):
    result = format_activity_summary_table(base_df, search_text="ZZZNOMATCH")
    assert len(result) == 0


def test_fallback_to_pval_when_fdr_absent():
    df = pd.DataFrame({
        "element_id": ["a", "b", "c"],
        "log2_ratio": [1.0, 2.0, 0.5],
        "pval": [0.5, 0.1, 0.9],
    })
    result = format_activity_summary_table(df, sort_by_fdr=True)
    assert list(result["pval"]) == sorted(result["pval"])
