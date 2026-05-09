# CRE-seq Analyzer — Individual Submission

**BioEng 134 Final Project**  
**Author:** Arjun Gurjar (`arjungurjar2006@gmail.com`)

The full team repository lives at [github.com/Bnovey/BioE-134-Final-Proj](https://github.com/Bnovey/BioE-134-Final-Proj) and contains the complete backend pipeline. This submission focuses on my individual scope: the Streamlit frontend, the MCP Chat integration, and the two standalone analysis functions described below.

---

## Project Overview

CRE-seq (cis-regulatory element sequencing) measures the transcriptional activity of thousands of DNA regulatory elements in parallel using a lentiMPRA assay. This tool takes raw FASTQ barcode reads and outputs activity scores for each element with statistical significance, motif annotations, and variant effect sizes. The GUI layer I built wraps a 32-tool MCP server with a five-page Streamlit application and a Claude-powered chat interface.

**Reference:** Agarwal et al. 2025, *Nature* — "Massively parallel characterization of transcriptional regulatory elements." DOI: 10.1038/s41586-024-08430-9

---

## Scope of Work

I developed two standalone analysis functions, the Streamlit frontend, and the MCP Chat integration. Backend analysis modules (QC library, activity calling, motif enrichment, stats) were built by teammates and are credited in the Team Contributions section.

### Standalone Functions

| Function | File | Purpose |
|---|---|---|
| `format_activity_summary_table` | `functions/activity_table.py` | Filter, sort, and prepare a CRE activity DataFrame for display |
| `export_qc_html` | `functions/export_qc_html.py` | Generate a self-contained HTML QC report from library QC results |

### Frontend (Streamlit)

| Function / Section | What it does |
|---|---|
| `_load_results()` | Reads `activity_results.tsv` from disk, normalises column names |
| `_run_async(coro)` | Runs an async coroutine from Streamlit's synchronous context |
| `_load_paper_excerpt()` | Loads the Agarwal 2025 paper excerpt for the agent system prompt |
| `_build_system_prompt()` | Constructs the Claude agent system prompt with pipeline context |
| `_extract_charts()` | Parses MCP tool results and builds inline Plotly charts (volcano, motif bar) |
| `_agent_turn()` | Full async Claude + MCP agent loop with tool discovery, execution, and chart extraction |
| Upload page | 4-step pipeline UI: association → counting → activity, with per-step status tracker, skip-association toggle, activity calling threshold controls |
| Chat page | Claude + MCP chat interface with suggested prompt chips, tool call log expander |
| QC & Plots page | 4-tab dashboard: Library QC (8 checks, threshold controls, CSV export), Activity Plots, Motif Analysis (run-from-UI enrichment), Variant Effects (run-from-UI delta scores) |
| Results page | Summary metrics, live search/filter, computed enrichment summary, CSV download |
| Help page | Pipeline diagram, tool reference, file glossary, FAQ |
| Sidebar | Navigation, session status, two-step reset confirmation |

### MCP Tools (added by me)

| Tool | What it does |
|---|---|
| `tool_variant_delta_scores` | Computes Δlog₂ (mutant − reference) for all variant families; writes `variant_delta_scores.tsv` |
| `tool_export_qc_html` | Runs all 8 QC checks and writes a self-contained HTML report |

---

## Function Descriptions

### `format_activity_summary_table`

**File:** `functions/activity_table.py`  
**Import:** `from functions import format_activity_summary_table`

```python
def format_activity_summary_table(
    activity_df,
    search_text=None,
    activity_filter="All",
    sort_by_fdr=False,
    display_cols=None,
):
```

Filters, sorts, and prepares a CRE activity results DataFrame for tabular display or CSV export.

**Args:**

| Parameter | Type | Description |
|---|---|---|
| `activity_df` | `pd.DataFrame` | Activity results table. Must contain `log2_ratio`. `oligo_id` is auto-renamed to `element_id` if present. |
| `search_text` | `str or None` | Case-insensitive substring matched against `element_id`. Empty string or `None` skips filtering. |
| `activity_filter` | `str` | `"All"`, `"Active only"`, or `"Inactive only"`. Filters on the `active` column. |
| `sort_by_fdr` | `bool` | Sort rows by `fdr` ascending (falls back to `pval` if `fdr` absent). |
| `display_cols` | `list[str] or None` | Columns to keep. Defaults to the standard 13-column CRE-seq display set. Missing columns are silently skipped. |

**Returns:** `pd.DataFrame` — filtered/sorted copy with reset index.

**Raises:**

- `TypeError` if `activity_df` is not a DataFrame
- `ValueError` if `activity_df` is missing the `log2_ratio` column
- `ValueError` if `activity_filter` is not one of the three accepted values

**Example:**

```python
import pandas as pd
from functions import format_activity_summary_table

df = pd.read_csv("activity_results.tsv", sep="\t")
display = format_activity_summary_table(
    df,
    search_text="ENSR",
    activity_filter="Active only",
    sort_by_fdr=True,
)
print(display.head())
```

---

### `export_qc_html`

**File:** `functions/export_qc_html.py`  
**Import:** `from functions import export_qc_html`

```python
def export_qc_html(qc_results, output_path=None):
```

Generates a self-contained HTML QC report from the output of `library_summary_report()`. The document includes no external CSS or JavaScript — it can be emailed or opened offline.

**Args:**

| Parameter | Type | Description |
|---|---|---|
| `qc_results` | `dict` | Return value of `creseq_mcp.qc.library.library_summary_report()`. Must contain a `"_report"` key with `overall_pass` (bool) and `failed_checks` (list). |
| `output_path` | `str or Path or None` | If given, the HTML is written to this path. Parent directory must exist. |

**Returns:** `str` — complete HTML document starting with `<!DOCTYPE html>`.

**Raises:**

- `TypeError` if `qc_results` is not a dict
- `ValueError` if `qc_results` is empty
- `ValueError` if `qc_results` is missing the `"_report"` key

**Example:**

```python
from creseq_mcp.qc.library import library_summary_report
from functions import export_qc_html

qc = library_summary_report(
    mapping_table_path="mapping_table.tsv",
    plasmid_count_path="plasmid_counts.tsv",
    design_manifest_path="oligo_design.tsv",
)
html = export_qc_html(qc, output_path="qc_report.html")
```

---

## Error Handling

Both functions perform explicit input validation at the top of the function body and raise informative exceptions before any computation runs.

`format_activity_summary_table`:
- `TypeError`: input is not a `pd.DataFrame` — raised immediately, before any column inspection
- `ValueError("...log2_ratio...")`: `log2_ratio` column absent — raised after the `oligo_id` rename so the message reflects the normalised column set
- `ValueError("activity_filter must be one of...")`: invalid filter string — includes the full accepted-values list in the message

`export_qc_html`:
- `TypeError`: input is not a `dict`
- `ValueError("...empty...")`: dict has no keys
- `ValueError("..._report...")`: `"_report"` key absent — raised before any HTML generation begins

---

## Testing

Tests live in `tests/test_activity_table.py` and `tests/test_export_qc_html.py`. Run with:

```bash
pytest tests/test_activity_table.py tests/test_export_qc_html.py -v
```

### `test_activity_table.py` (19 tests)

| Test | What it covers |
|---|---|
| `test_returns_dataframe` | Return type is `pd.DataFrame` |
| `test_index_is_reset` | Output index starts at 0 after filtering |
| `test_all_filter_returns_all_rows` | `"All"` filter preserves every row |
| `test_active_only_filter` | Only rows with `active == True` returned |
| `test_inactive_only_filter` | Only rows with `active == False` returned |
| `test_search_text_filters_by_element_id` | Substring search against `element_id` |
| `test_sort_by_fdr_ascending` | Rows ordered by `fdr` ascending when flag is set |
| `test_sort_by_fdr_false_preserves_original_order` | Order unchanged when flag is False |
| `test_renames_oligo_id_to_element_id` | `oligo_id` column renamed automatically |
| `test_custom_display_cols` | Custom `display_cols` honoured |
| `test_missing_display_col_is_silently_skipped` | Non-existent column name ignored |
| `test_does_not_mutate_input` | Input DataFrame is not modified |
| `test_active_filter_and_sort_combined` | Both filter and sort applied together |
| `test_raises_type_error_on_non_dataframe` | `TypeError` on dict input |
| `test_raises_value_error_on_missing_log2_ratio` | `ValueError` when column absent |
| `test_raises_value_error_on_invalid_activity_filter` | `ValueError` on bad filter string |
| `test_empty_dataframe_returns_empty` | Empty DataFrame in → empty DataFrame out |
| `test_search_text_no_match_returns_empty` | Unmatched search returns empty DataFrame |
| `test_fallback_to_pval_when_fdr_absent` | Falls back to `pval` for sorting |

### `test_export_qc_html.py` (17 tests)

| Test | What it covers |
|---|---|
| `test_returns_string` | Return type is `str` |
| `test_html_starts_with_doctype` | Output begins with `<!DOCTYPE html>` |
| `test_html_is_self_contained` | Inline `<style>` tag present, no external links |
| `test_pass_banner_present_when_all_checks_pass` | Green pass banner for passing QC |
| `test_fail_banner_present_when_checks_fail` | Red fail banner for failing QC |
| `test_fail_banner_names_failed_checks` | Failed check names appear in the banner |
| `test_html_contains_barcode_complexity_section` | Per-check section present |
| `test_html_contains_oligo_recovery_section` | Per-check section present |
| `test_html_contains_pass_status_for_passing_checks` | PASS label in table |
| `test_html_contains_fail_status_for_failing_checks` | FAIL label in table |
| `test_writes_file_when_output_path_given` | File written and contents match return value |
| `test_does_not_create_file_when_output_path_is_none` | No file written when path omitted |
| `test_output_path_accepts_string` | String path (not just `Path`) accepted |
| `test_handles_tuple_valued_tool_results` | `(DataFrame, dict)` tool result handled |
| `test_raises_type_error_on_non_dict` | `TypeError` on string input |
| `test_raises_value_error_on_empty_dict` | `ValueError` on `{}` |
| `test_raises_value_error_on_missing_report_key` | `ValueError` when `"_report"` absent |

---

## Usage Instructions

```bash
# Install the MCP package in editable mode
git clone <repo-url>
cd BioE-134-Final-Proj
pip install -e .

# Import standalone functions directly
from functions import format_activity_summary_table, export_qc_html

# Run the full Streamlit application
streamlit run frontend/app.py

# Set your Anthropic API key for the Chat agent
export ANTHROPIC_API_KEY=sk-ant-...
```

### Data and portability

The app is fully portable — output files are written to `~/Desktop/creseq_outputs/` on whoever's machine is running it (`Path.home()` resolves at runtime, not hardcoded to any specific user).

**To use the pipeline end-to-end you need:**

1. **Real FASTQ files** — the association and counting steps require raw sequencing data from a lentiMPRA run. The file-path fields in the Upload page accept any local path; the placeholder text (e.g. `~/Desktop/creseq_test_data/`) is just a hint, not a hardcoded location.
2. **`starcode`** — the association step shells out to this C binary for barcode clustering. Install it separately (`brew install starcode` on macOS or build from [github.com/gui11aume/starcode](https://github.com/gui11aume/starcode)). All other dependencies are Python packages covered by `pip install -e .`.

**To demo the UI without running the pipeline:**

Pre-computed outputs are included in `demo_outputs/`. Copy them into the output directory and the Results, QC & Plots, and Chat pages will load immediately:

```bash
mkdir -p ~/Desktop/creseq_outputs
cp demo_outputs/*.tsv ~/Desktop/creseq_outputs/
```

---

## MCP Integration

The two functions in `functions/` are also exposed as MCP tools in `creseq_mcp/server.py` (`tool_variant_delta_scores`, `tool_export_qc_html`) and described in JSON wrappers under `wrapper/`. This allows the Claude agent in the Chat page to call them by name.

```
wrapper/
├── activity_table.json       ← MCP wrapper for format_activity_summary_table
├── export_qc_html.json       ← MCP wrapper for export_qc_html
└── prompts.json              ← 6 test prompts (3 per function) with expected calls
```

Each wrapper follows the `UCB-BioE-Anderson-Lab/UCB_BioE134_FinalProject` schema: `id`, `type`, `name`, `description`, `keywords`, `inputs`, `outputs`, `examples`, `execution_details`.

---

## Architecture

```
FASTQ reads
    │
    ▼
1. Association  ─── mappy alignment + STARCODE barcode clustering
    │                    → mapping_table.tsv
    ▼
2. DNA Counting ─── count plasmid barcodes per oligo
    │                    → plasmid_counts.tsv
    ▼
3. RNA Counting ─── count RNA barcodes (multiple replicates, parallel)
    │                    → rna_counts.tsv
    ▼
4. Activity     ─── log₂(RNA/DNA), z-score vs. negative controls, BH-FDR
                     → activity_results.tsv

Streamlit UI  ◄──────────────────────── MCP Server (32 tools)
     │                                       │
     └─── Claude (claude-sonnet-4-6) ────────┘
          AsyncAnthropic + stdio MCP client
```

---

## Reflection

### What was difficult to implement

The hardest part was bridging Streamlit's synchronous execution model with the async MCP client. Claude's Python SDK uses `asyncio`, but Streamlit runs its render loop in a single thread — calling `await` directly inside a page handler crashes with a "no running event loop" error. I solved this by spinning up a fresh `asyncio` event loop per agent turn (`asyncio.new_event_loop(); loop.run_until_complete(coro); loop.close()`), but this has a real cost: the UI blocks completely while the agent is running. For quick queries that finish in a second or two this is fine, but a full pipeline run (QC → motif enrichment → plotting) could keep the browser tab frozen for a minute. A proper fix would use `asyncio.run_coroutine_threadsafe` on a background thread, but that significantly complicates session-state sharing with the main thread — a tradeoff I deferred given the project timeline.

The second hard problem was parsing MCP tool results for inline chart rendering. Every tool returns a JSON string, but the schemas are heterogeneous: some return `rows[]` arrays, some return `top_motifs[]`, some return a file path string, and some return a nested `plot_data` dict. Writing `_extract_charts()` to detect the right schema and produce the correct Plotly figure type required reading the output contract of every tool individually, which took longer than the actual chart code.

Managing session state across Streamlit's stateless rerenders was a persistent source of subtle bugs. The two-step reset confirmation, the QC result cache, and the suggested prompt chips all required careful use of `st.session_state` keys and `st.rerun()`. The chip buttons were particularly tricky: a button click and the `st.chat_input()` widget are both consumed in the same render cycle, so a button click that sets `st.session_state["_pending_chat"]` must call `st.rerun()` to hand off to the input-processing block in the next cycle — otherwise both fire simultaneously and the message is processed twice.

### Design choices

I chose Streamlit over a custom React/Flask app because the team needed something deployable within hours, not weeks. The target users — computational biologists — are already comfortable with Python notebooks; Streamlit's page-based mental model maps directly onto what they already know. The main tradeoff is the blocking execution model described above, which would be a problem in a production multi-user deployment but is acceptable for a tool run by one person at a time on a local machine.

The pipeline trigger in the Upload page is intentionally synchronous and blocking. An asynchronous "run in the background" design would have been more polished, but getting the subprocess management and session-state synchronisation right would have taken two days; the status table gives enough user feedback that blocking is acceptable. Incremental progress updates within each step would require hooking into the backend's internal logging, which would have required changes to Bowman's pipeline code — a cross-team coordination cost I avoided.

The most consequential design choice was keeping the Claude + MCP chat as the primary power-user interface, with the QC/Plots dashboard pages as a simplified shortcut view. This avoids duplicating logic: the "▶ Run Motif Enrichment" button and the "▶ Compute Variant Delta Scores" button in the QC page call the same underlying Python functions the agent would invoke via MCP. Adding a new capability means writing one MCP tool; both the chat interface and the UI button automatically benefit.

Pipeline output goes to `~/Desktop/creseq_outputs/` (a user-visible directory) rather than a temp dir. This was a deliberate choice: the association step on a real 50M-read FASTQ dataset takes 20–30 minutes. If the output went to a temp dir, a browser refresh would wipe it and force a full rerun. Writing to the Desktop means partial results persist across sessions.

### How a GUI changes the CRE-seq workflow

Traditional MPRA analysis is a Snakemake or bash pipeline: the bioinformatician writes config files, submits jobs to a cluster, inspects TSVs in R or Python notebooks, and iterates manually. Each QC decision — "is 15 barcodes/oligo enough?" — requires editing a script parameter, re-running, and re-inspecting. The GUI collapses this loop: adjustable threshold sliders in the QC panel let a researcher run sensitivity analyses in seconds rather than minutes.

More importantly, a GUI lowers the barrier to entry for wet-lab collaborators who generated the library but cannot write Python. A biologist who designed the oligo library and ran the sequencing can now upload their FASTQ files, click through the four-step pipeline, and see whether their library passed QC — all without touching a terminal. The results page with its live text search makes it easy to ask "did the enhancer near gene X show activity?" without needing to write a `pandas` query.

The integrated Claude agent changes the interaction pattern from a static report to a conversation. A researcher who sees that barcode uniformity failed can type "why did barcode uniformity fail and what should I do?" The agent can cross-reference the QC metric (Gini coefficient of per-barcode read counts), the paper context from Agarwal et al. 2025 loaded into the system prompt, and any relevant PubMed literature returned by `tool_search_pubmed` — synthesising an interpretation that a static HTML table cannot produce. This is most valuable for novel failure modes that are not covered by the hard-coded QC thresholds.

---

## Team Contributions

| Member | Contribution |
|---|---|
| Arjun Gurjar | Streamlit frontend (all 5 pages), MCP Chat integration, `format_activity_summary_table`, `export_qc_html`, `tool_variant_delta_scores`, `tool_export_qc_html` |
| Bowman Novey | Backend pipeline (association, counting, activity calling), MCP server wiring, library QC module, integration |
| Sarrah Rose | Activity calling module, motif enrichment, plotting |
| Zach Rao | Stats & RAG tools (normalization, ranking, PubMed/JASPAR/ENCODE search) |

---

## Citation

Agarwal, H. et al. "Massively parallel characterization of transcriptional regulatory elements." *Nature* (2025). DOI: 10.1038/s41586-024-08430-9
