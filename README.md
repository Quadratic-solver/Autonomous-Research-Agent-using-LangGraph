# Autonomous-Research-Agent-using-LangGraph

An LLM-powered pipeline that turns raw meter-reading data into a polished monthly PDF report — automating the "collect data → chart it → explain it → recommend action" workflow a human analyst would normally do by hand.

Built as a trimmed-down, template-driven version of a larger multi-agent article-writing system, adapted for a fixed business report format instead of open-ended topics.

## What it does

Given two months of raw meter-reading data (one row per meter reading, per team), the pipeline:

1. Aggregates raw readings up to team-level metrics
2. Renders a month-over-month comparison chart
3. Generates each section of the report with an LLM (Claude Haiku)
4. Self-checks the **Analysis** section specifically — the one place a model is most likely to invent a wrong explanation for a data pattern — and sends it back for revision if it doesn't correctly use the human-provided context
5. Compiles everything into a formatted PDF

## Why the Analysis section gets special treatment

Most sections here are template fill-ins: describe the chart, summarize, wrap up. Low risk if the model gets creative.

Analysis is different — it's asking the model to explain *why* a number moved, which is exactly where LLMs tend to confidently invent plausible-sounding but wrong causes. To guard against that, the pipeline includes a small **Builder → Critic loop**:

- A **Builder** node drafts the analysis, using the data *and* a human-written context note (e.g. "Team B covers hillside routes, which explains longer travel times")
- A **Critic** node checks whether the draft actually used that context correctly, rather than inventing its own explanation
- If not approved, it retries — capped at 2 attempts, so it can never loop forever

This is the one part of the pipeline where the model's own judgment changes what happens next, rather than just filling in text in a fixed order. Everything else here is a straightforward pipeline, not an autonomous agent — worth being upfront about, since "agent" gets thrown around loosely.

## Architecture

```
Intro → Plot (chart) → Comment → Analysis ⇄ Critic → Recommendation → Conclusion → Compile to PDF
                                     ↑________|
                                   retry (max 2)
```

| Layer | What it means here |
|---|---|
| **Prompt** | The instructions sent to the model for each section |
| **Context** | The data tables + human-written notes fed into those prompts |
| **Harness** | Structured output validation (Pydantic) + fallback handling so a bad LLM call never crashes the pipeline |
| **Loop** | The Builder/Critic retry cycle on the Analysis section |

## Tech stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — orchestration
- [Claude API](https://docs.claude.com) (Haiku 4.5) via `langchain-anthropic`
- `pandas` — data aggregation
- `matplotlib` — chart rendering
- `WeasyPrint` — Markdown → PDF compilation
- `pydantic` — structured output validation

## Project structure

```
meter_agent/
├── data/
│   └── meter_collections.xlsx      # raw data, two sheets: current + previous month
├── output/                         # generated chart + PDF land here
├── src/
│   ├── state.py                    # shared pipeline state
│   ├── data_loader.py              # reads Excel, aggregates to team level
│   ├── nodes.py                    # all LLM calls + chart rendering
│   ├── graph.py                    # wires nodes into the LangGraph pipeline
│   └── compiler.py                 # assembles sections into the final PDF
├── main.py                         # entry point
├── requirements.txt
└── .env.example
```

## Setup

```bash
git clone https://github.com/<your-username>/meter-agent.git
cd meter-agent
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Data format

Drop an Excel file at `data/meter_collections.xlsx` with two sheets (one per month), each containing these columns:

| Column | Type | Example |
|---|---|---|
| `reading_id` | text | MC-00001 |
| `date` | date | 2026-07-03 |
| `team_name` | text | Team Alpha |
| `collector_name` | text | J. Santos |
| `barangay` | text | Barangay Poblacion |
| `meter_id` | text | MTR-10234 |
| `previous_reading_kwh` | integer | 4820 |
| `current_reading_kwh` | integer | 5010 |
| `consumption_kwh` | integer | 190 |
| `collection_status` | text | Collected / Missed / Disputed |
| `time_spent_min` | integer | 8 |

Update the sheet names and manual context note in `main.py` to match your data:

```python
df_current, df_previous = load_meter_data(
    "data/meter_collections.xlsx",
    current_sheet="july_2026",
    previous_sheet="june_2026",
)

manual_notes = "Team B covers the hillside barangays, which explains longer travel time..."
```

## Usage

```bash
python main.py
```

Output lands in `output/`:
- `collection_rate_chart.png`
- `monthly_report.pdf`

## Possible next steps

- Extend the Builder/Critic loop to other sections beyond Analysis
- Let the pipeline decide *whether* a visual is needed at all, rather than always generating one
- Support more than two months of trend data
- Swap the fixed template for a dynamic one that adapts section structure to the data provided

## Background

This project is a simplified offshoot of a larger multi-agent article pipeline built to explore **prompt, context, harness, and loop engineering** as distinct, separately-debuggable layers of an LLM system — rather than treating "prompting" as the only lever available.
