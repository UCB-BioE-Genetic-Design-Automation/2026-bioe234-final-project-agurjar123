"""Standalone function for filtering, sorting, and preparing a CRE activity DataFrame."""

import pandas as pd


_DEFAULT_DISPLAY_COLS = [
    "element_id", "chrom", "start", "end",
    "dna_counts", "rna_counts", "log2_ratio",
    "fdr", "pval", "active",
    "designed_category", "chromatin_state", "top_motif",
]


def format_activity_summary_table(
    activity_df,
    search_text=None,
    activity_filter="All",
    sort_by_fdr=False,
    display_cols=None,
):
    """
    Filter, sort, and prepare a CRE activity DataFrame for display.

    Applies optional substring search on the element identifier column,
    filters rows by activity status, optionally sorts by FDR, and
    restricts the output to a defined set of columns.

    Args:
        activity_df (pd.DataFrame): Activity results table. Must contain a
            ``log2_ratio`` column. If an ``oligo_id`` column is present but
            ``element_id`` is not, it is renamed to ``element_id``
            automatically.
        search_text (str or None): Case-insensitive substring to match
            against the ``element_id`` column (or the first column if
            ``element_id`` is absent). Rows that do not match are dropped.
            Pass ``None`` or ``""`` to skip filtering. Default ``None``.
        activity_filter (str): One of ``"All"``, ``"Active only"``, or
            ``"Inactive only"``. Filters on the ``active`` column when
            present; ignored if the column is absent. Default ``"All"``.
        sort_by_fdr (bool): If ``True``, sort the result by the ``fdr``
            column ascending (falling back to ``pval`` if ``fdr`` is
            absent). Default ``False``.
        display_cols (list[str] or None): Ordered list of column names to
            keep in the returned DataFrame. Columns not present in
            ``activity_df`` are silently skipped. Defaults to a standard
            set of CRE-seq columns (element_id, chrom, start, end,
            dna_counts, rna_counts, log2_ratio, fdr, pval, active,
            designed_category, chromatin_state, top_motif).

    Returns:
        pd.DataFrame: A copy of ``activity_df`` with filters and sort
        applied, restricted to the requested display columns and with the
        index reset.

    Raises:
        TypeError: if ``activity_df`` is not a pandas DataFrame.
        ValueError: if ``activity_df`` does not contain a ``log2_ratio``
            column.
        ValueError: if ``activity_filter`` is not one of the three
            accepted strings.
    """
    if not isinstance(activity_df, pd.DataFrame):
        raise TypeError(
            f"activity_df must be a pandas DataFrame, got {type(activity_df).__name__}"
        )

    df = activity_df.copy()

    if "oligo_id" in df.columns and "element_id" not in df.columns:
        df = df.rename(columns={"oligo_id": "element_id"})

    if "log2_ratio" not in df.columns:
        raise ValueError(
            "activity_df is missing required column 'log2_ratio'. "
            "Ensure the activity-calling step has been run."
        )

    _valid_filters = {"All", "Active only", "Inactive only"}
    if activity_filter not in _valid_filters:
        raise ValueError(
            f"activity_filter must be one of {sorted(_valid_filters)!r}, "
            f"got {activity_filter!r}"
        )

    if search_text:
        id_col = "element_id" if "element_id" in df.columns else df.columns[0]
        df = df[df[id_col].astype(str).str.contains(search_text, case=False, na=False)]

    if activity_filter == "Active only" and "active" in df.columns:
        df = df[df["active"]]
    elif activity_filter == "Inactive only" and "active" in df.columns:
        df = df[~df["active"]]

    if sort_by_fdr:
        fdr_col = (
            "fdr" if "fdr" in df.columns
            else ("pval" if "pval" in df.columns else None)
        )
        if fdr_col:
            df = df.sort_values(fdr_col, ascending=True)

    cols = display_cols if display_cols is not None else _DEFAULT_DISPLAY_COLS
    cols = [c for c in cols if c in df.columns]
    return df[cols].reset_index(drop=True)
