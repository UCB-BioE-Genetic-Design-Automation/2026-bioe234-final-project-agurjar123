"""
functions/
==========
Standalone analysis and display utilities developed by Arjun Gurjar
for the CRE-seq Analyzer (BioEng 134 Final Project).

Functions
---------
format_activity_summary_table : Filter, sort, and prepare a CRE activity
    DataFrame for display in the Streamlit results page.
export_qc_html : Generate a self-contained HTML QC report from the output
    of creseq_mcp.qc.library.library_summary_report().
"""

from functions.activity_table import format_activity_summary_table
from functions.export_qc_html import export_qc_html

__all__ = ["format_activity_summary_table", "export_qc_html"]
