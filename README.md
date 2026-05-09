# CRE-seq Analyzer — Individual Submission

**BioEng 134 Final Project**  
**Author:** Arjun Gurjar (`arjungurjar2006@gmail.com`)

The full team repository lives at [github.com/Bnovey/BioE-134-Final-Proj](https://github.com/Bnovey/BioE-134-Final-Proj) and contains the complete backend pipeline. This submission focuses on my individual scope: the Streamlit frontend, the Claude + MCP **client-side** chat integration, and the two standalone analysis functions described below.

---

## Project Overview

CRE-seq (cis-regulatory element sequencing) measures the transcriptional activity of thousands of DNA regulatory elements in parallel using a lentiMPRA assay. It takes raw FASTQ barcode reads and produces activity scores per element with statistical significance, motif annotations, and variant effect sizes. I built the GUI layer: a five-page Streamlit app and a Claude-powered chat interface that sits on top of a 32-tool MCP server.

**Reference:** Agarwal et al. 2025, *Nature* — "Massively parallel characterization of transcriptional regulatory elements." DOI: 10.1038/s41586-024-08430-9

---

## Scope of Work

I developed two standalone analysis functions, the Streamlit frontend, and the Claude + MCP chat client. The MCP **server** (`creseq_mcp/server.py`) and its core tool suite were built by Bowman Novey; I added two tools to that server (`tool_variant_delta_scores`, `tool_export_qc_html`) and built the client-side integration that connects the frontend to it. All other backend modules (QC library, activity calling, motif enrichment, stats) were built by teammates and are credited in the Team Contributions section.

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

### MCP Tools (added to Bowman's server)

Bowman built the FastMCP server architecture and the core 30-tool suite. I added two tools to that server:

| Tool | What it does |
|---|---|
| `tool_variant_delta_scores` | Computes Δlog₂ (mutant − reference) for all variant families; writes `variant_delta_scores.tsv` |
| `tool_export_qc_html` | Runs all 8 QC checks and writes a self-contained HTML report |

### MCP Chat Client (built by me)

The chat page connects to Bowman's server via the Model Context Protocol stdio transport. The client-side integration I wrote:

| Component | What it does |
|---|---|
| `_agent_turn()` | Async loop: discovers available tools, calls `AsyncAnthropic`, routes tool-use blocks back to the MCP server, collects results, loops until `end_turn` |
| `_run_async(coro)` | Bridges Streamlit's synchronous thread to the asyncio MCP client via a fresh event loop per turn |
| `_build_system_prompt()` | Injects pipeline context + Agarwal 2025 paper excerpt so the agent understands the domain |
| `_extract_charts()` | Parses heterogeneous MCP tool result schemas and renders inline Plotly charts (volcano, motif bar) |

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

Getting the Claude agent to work inside Streamlit was harder than expected. The two frameworks have conflicting execution models: Streamlit is synchronous and rerenders the whole page on every user action, while the Claude SDK and MCP client are fully async. Bridging them required some awkward plumbing, and the result is that the UI freezes while the agent is running. For a quick query that's barely noticeable, but for a longer tool chain it can feel sluggish. A cleaner implementation would run the agent on a background thread, but that adds enough complexity that I left it as-is.

The other tricky part was building the inline chart rendering. Each MCP tool returns results in its own format, and I had no control over those formats since Bowman wrote the tools. Writing the parser that detects which kind of result came back and picks the right chart type meant reading through every tool's output contract one by one.

Session state in Streamlit is also more finicky than it looks. Because the page rerenders on every interaction, anything that needs to persist between clicks has to be explicitly saved and retrieved. The suggested prompt chips were the clearest example: getting a button click to correctly populate and submit the chat input without double-firing took several iterations to get right.

### Design choices

I picked Streamlit over React or Flask because we needed something working fast and the likely users (computational biologists) already think in terms of Python scripts and notebooks. Streamlit's model felt close enough to that. The downside is the blocking execution I described above, which would be a real problem if multiple people were using it at once, but for a single-user local tool it's acceptable.

The pipeline trigger blocks the UI intentionally. Making it async would have meant managing subprocesses on a background thread and syncing their output back to session state, which would have required touching Bowman's pipeline code to add callbacks. Not worth it for a project with one user at a time. The status table rows showing per-step timing give enough feedback that the blocking feels okay in practice.

The biggest structural choice was treating the Chat page as the main power-user interface and making the QC/Plots page buttons just shortcuts to the same underlying functions. The "Run Motif Enrichment" button in the QC tab calls the same code the agent would call via MCP. That way adding a new analysis tool automatically shows up in both places without duplicating anything.

I also wrote pipeline output to `~/Desktop/creseq_outputs/` rather than a temp directory. The association step takes 20-30 minutes on a real dataset, so if results landed in a temp dir they'd be gone on the next browser refresh. Keeping them on the Desktop means a partial run persists across sessions.

### How a GUI changes the CRE-seq workflow

The typical MPRA analysis workflow is a Snakemake or bash pipeline: write configs, submit to a cluster, open TSVs in a notebook, iterate. Every threshold change ("what if I require 20 barcodes per oligo instead of 15?") means editing a script, rerunning, and reloading. The GUI replaces that with a slider, so a researcher can test a few thresholds in a few seconds without touching code.

The bigger impact is on who can run it at all. Wet-lab biologists who designed and sequenced the library often can't write Python. With the GUI they can upload files, run the pipeline, and check QC results themselves without needing a bioinformatician to babysit the process.

The Chat integration changes how results get interpreted. Without it, a failed QC check is just a red cell in a table and you have to figure out what it means on your own. With the agent, you can ask "why did barcode uniformity fail?" and get an answer that ties the Gini coefficient back to what Agarwal et al. say about library preparation and what to do about it. That kind of contextual interpretation is hard to bake into a static report.

---

## Team Contributions

| Member | Contribution |
|---|---|
| Arjun Gurjar | Streamlit frontend (all 5 pages), Claude + MCP chat client (`_agent_turn`, `_run_async`, `_extract_charts`, `_build_system_prompt`), `format_activity_summary_table`, `export_qc_html`, `tool_variant_delta_scores` and `tool_export_qc_html` (added to Bowman's server) |
| Bowman Novey | Backend pipeline (association, counting, activity calling), FastMCP server architecture and 30-tool suite, library QC module, pytests |
| Sarrah Rose | Activity calling module, motif enrichment, plotting |
| Zach Rao | Stats & RAG tools (normalization, ranking, PubMed/JASPAR/ENCODE search) |

---

## References

**Experimental method**

Agarwal, H. et al. "Massively parallel characterization of transcriptional regulatory elements." *Nature* (2025). DOI: 10.1038/s41586-024-08430-9

Inoue, F. et al. "A systematic comparison reveals substantial differences in chromosomal versus episomal encoding of enhancer activity." *Genome Research* 27, 38–52 (2017). DOI: 10.1101/gr.212092.116 *(lentiMPRA assay design)*

**Sequence alignment and barcode clustering**

Li, H. "Minimap2: pairwise alignment for nucleotide sequences." *Bioinformatics* 34, 3094–3100 (2018). DOI: 10.1093/bioinformatics/bty191 *(mappy Python bindings used in the association step)*

Zorita, E., Cuscó, P. & Filion, G. "Starcode: sequence clustering based on all-pairs search." *Bioinformatics* 31, 1913–1919 (2015). DOI: 10.1093/bioinformatics/btv053 *(barcode clustering in the association step)*

**Statistics**

Benjamini, Y. & Hochberg, Y. "Controlling the false discovery rate: a practical and powerful approach to multiple testing." *Journal of the Royal Statistical Society B* 57, 289–300 (1995). *(BH-FDR correction applied in activity calling and variant delta scores)*

**Motif databases**

Castro-Mondragon, J. A. et al. "JASPAR 2022: the 9th release of the open-access database of transcription factor binding profiles." *Nucleic Acids Research* 50, D165–D173 (2022). DOI: 10.1093/nar/gkab1113 *(TF motif enrichment via pyjaspar)*

**LLM and tool-use infrastructure**

Anthropic. "Claude API." https://docs.anthropic.com (2024). *(AsyncAnthropic SDK used for the chat agent)*

Model Context Protocol. "MCP specification." https://modelcontextprotocol.io (2024). *(stdio MCP transport connecting the frontend to the tool server)*

**Frontend framework**

Streamlit Inc. "Streamlit: the fastest way to build data apps." https://streamlit.io (2024).
