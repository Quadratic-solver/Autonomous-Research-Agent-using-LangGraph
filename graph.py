"""
Builds the graph of nodes for the Meter Collection Report pipeline.

This implements a linear pipeline with a Builder/Critic loop around the
Analysis step. It uses a critique function to decide whether to move forward to `recommendation` or
retry the builder node. A max retry cap is enforced to avoid infinite loops.
"""


from langgraph.graph import StateGraph, END
from src.state import ReportState
from src.nodes import (
    plot_node, intro_node, comment_node,
    analysis_builder_node, analysis_critic_node,
    recommendation_node, conclusion_node,
)

MAX_ANALYSIS_RETRIES = 2

#Decides whether to proceed to recommendation or retry the analysis builder based on the Critic's output.
def route_after_critique(state):
    if state["analysis_status"] == "approved":
        return "recommendation"
    if state.get("analysis_retry_count", 0) >= MAX_ANALYSIS_RETRIES:
        return "recommendation"  # cap hit — move on rather than loop forever
    return "analysis_builder"


def build_graph():
    graph = StateGraph(ReportState)

    # Register nodes by name (these are simple callables accepting `state`).
    graph.add_node("intro", intro_node)
    graph.add_node("plot", plot_node)
    graph.add_node("comment", comment_node)
    graph.add_node("analysis_builder", analysis_builder_node)
    graph.add_node("analysis_critic", analysis_critic_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("conclusion", conclusion_node)

    # Linear flow with a conditional loop on analysis_critic
    graph.set_entry_point("intro")
    graph.add_edge("intro", "plot")
    graph.add_edge("plot", "comment")
    graph.add_edge("comment", "analysis_builder")
    graph.add_edge("analysis_builder", "analysis_critic")
    graph.add_conditional_edges("analysis_critic", route_after_critique, {
        "recommendation": "recommendation",
        "analysis_builder": "analysis_builder",
    })
    graph.add_edge("recommendation", "conclusion")
    graph.add_edge("conclusion", END)

    return graph.compile()