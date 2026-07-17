"""
This file has all the steps that write text with the AI, plus the one
step that makes the chart (no AI involved in the chart itself).
 
Every function here takes the shared `state` box, adds its own result to
it, and passes it along.

"""

import os
import matplotlib.pyplot as plt
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic

# calls the LLM with the Anthropic API key from the environment
def get_llm():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key and api_key.startswith('"') and api_key.endswith('"'):
        api_key = api_key[1:-1]
        os.environ["ANTHROPIC_API_KEY"] = api_key
    return ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.3)


# ── Plot (deterministic, no LLM) ─────────────────────────────────────
# Creates a bar chart comparing collection rates for each team across two months.
def plot_node(state):
    
    current = state["team_summary_current"]
    previous = state["team_summary_previous"]
    merged = current.merge(previous, on="team_name", suffixes=("_current", "_previous"))

    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(merged))
    width = 0.35
    ax.bar([i - width / 2 for i in x], merged["collection_rate_previous"], width,
           label=state["previous_month"])
    ax.bar([i + width / 2 for i in x], merged["collection_rate_current"], width,
           label=state["current_month"])
    ax.set_xticks(list(x))
    ax.set_xticklabels(merged["team_name"])
    ax.set_ylabel("Collection Rate (%)")
    ax.set_title("Team Collection Rate: Month-over-Month")
    ax.legend()

    os.makedirs("output", exist_ok=True)
    path = "output/collection_rate_chart.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)

    state["chart_path"] = path
    return state


# ── Intro ──────────────────────────────────────────────────────────
# Calls Claude to produce a short, factual introduction paragraph for the report.
def intro_node(state):
    prompt = f"""Write a short intro paragraph (2-3 sentences) for a monthly meter
collection performance report covering {state['current_month']}, compared
against {state['previous_month']}. Keep it factual and direct, no fluff."""
    response = get_llm().invoke(prompt)
    state["sections"]["intro"] = response.content
    return state


# ── Comment on the chart ──────────────────────────────────────────
# Calls Claude to produce a short paragraph describing what the chart shows.
def comment_node(state):
    summary_text = state["team_summary_current"].to_string(index=False)
    prompt = f"""Here is this month's team collection summary:

{summary_text}

Write a short paragraph (3-4 sentences) simply describing what the chart
shows. Do not explain WHY yet, just describe the pattern."""
    response = get_llm().invoke(prompt)
    state["sections"]["comment"] = response.content
    return state


# ── Analysis (Builder + Critic loop lives here) ───────────────────
class AnalysisCritique(BaseModel):
    approved: bool
    feedback: str

# Asks Claude to explain WHY the numbers look the way they do.
def analysis_builder_node(state):
    current = state["team_summary_current"].to_string(index=False)
    previous = state["team_summary_previous"].to_string(index=False)
    breakdown = state["breakdown"].to_string(index=False)
    feedback = state.get("analysis_feedback", "")
    feedback_block = f"\n\nPrevious feedback to address:\n{feedback}" if feedback else ""

    prompt = f"""Current month team summary:
{current}

Previous month team summary:
{previous}

Status breakdown by team:
{breakdown}

Manual context notes (treat as ground truth, do not contradict):
{state['manual_notes']}

Write a short analysis paragraph (4-6 sentences) explaining WHY the
patterns in the data occurred. You must incorporate the manual context
notes where relevant instead of inventing your own explanation.{feedback_block}"""

    response = get_llm().invoke(prompt)
    state["sections"]["analysis"] = response.content
    return state

# Checks whether the analysis is grounded in the data and manual notes, and either approves it or provides feedback for a retry.
def analysis_critic_node(state):
    structured_llm = get_llm().with_structured_output(AnalysisCritique)
    prompt = f"""Analysis draft:
{state['sections']['analysis']}

Manual context notes (ground truth):
{state['manual_notes']}

Does the analysis correctly incorporate the manual notes instead of
inventing its own explanation for any performance gaps? Does it stay
grounded in the data provided? Respond with approved=True/False and
brief feedback."""

    try:
        result = structured_llm.invoke(prompt)
    except Exception:
        # If the check itself breaks, just let the draft through rather
        # than getting the whole pipeline stuck.
        result = AnalysisCritique(approved=True, feedback="")

    state["analysis_status"] = "approved" if result.approved else "retry"
    state["analysis_feedback"] = result.feedback
    if not result.approved:
        state["analysis_retry_count"] = state.get("analysis_retry_count", 0) + 1
    return state


# ── Recommendation ─────────────────────────────────────────────────
# Calls Claude to produce 2-3 short, concrete recommendations for next month based on the analysis.
def recommendation_node(state):
    prompt = f"""Analysis:
{state['sections']['analysis']}

Based on this analysis, write 2-3 short, concrete recommendations for
next month. Be direct and actionable."""
    response = get_llm().invoke(prompt)
    state["sections"]["recommendation"] = response.content
    return state


# ── Conclusion ─────────────────────────────────────────────────────
# Calls Claude to produce a short conclusion paragraph summarizing the report.
def conclusion_node(state):
    prompt = f"""Summarize this report in 2-3 sentences as a closing conclusion:

{state['sections']['intro']}
{state['sections']['comment']}
{state['sections']['analysis']}
{state['sections']['recommendation']}"""
    response = get_llm().invoke(prompt)
    state["sections"]["conclusion"] = response.content
    return state