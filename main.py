"""
This is the file you actually run. It does everything in order:
 
1. Load your API key
2. Read the Excel data
3. Run the pipeline (writes all the sections, makes the chart)
4. Save the final PDF

"""

from dotenv import load_dotenv

# Load the .env file to get the Anthropic API key
load_dotenv()

from src.data_loader import load_meter_data, summarize_by_team, breakdown_by_status
from src.graph import build_graph
from src.compiler import compile_to_pdf

# Reads the Excel workbook, aggregates to team level, and runs the report generation graph.
def main():
    df_current, df_previous = load_meter_data(
        "data/meter_collections.xlsx",
        current_sheet="july_2026",
        previous_sheet="june_2026",
    )

    team_summary_current = summarize_by_team(df_current)
    team_summary_previous = summarize_by_team(df_previous)
    breakdown = breakdown_by_status(df_current)

    # TODO: replace with your real note once you generate the data
    manual_notes = (
        "Team B covers the hillside barangays, which explains longer "
        "travel time and higher missed/disputed rates this month."
    )

    # This is the shared box that gets passed through every step
    initial_state = {
        "current_month": "July 2026",
        "previous_month": "June 2026",
        "team_summary_current": team_summary_current,
        "team_summary_previous": team_summary_previous,
        "breakdown": breakdown,
        "manual_notes": manual_notes,
        "chart_path": "",
        "sections": {},
        "analysis_feedback": "",
        "analysis_retry_count": 0,
        "analysis_status": "",
        "final_pdf_path": "",
    }

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    pdf_path = compile_to_pdf(final_state)
    print(f"Report generated: {pdf_path}")


if __name__ == "__main__":
    main()