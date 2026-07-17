"""
This part reads the Excel workbook and aggregates the per-reading rows into team-level summaries.

The read the monthly assets (current and previous month) and make a lightweight summary for each team. 
The summaries are used by the plotting and analysis nodes to generate the report.
"""

import pandas as pd

# Reads excel workbook and returns two DataFrames: current month and previous month.
def load_meter_data(filepath, current_sheet="july_2026", previous_sheet="june_2026"):
    df_current = pd.read_excel(filepath, sheet_name=current_sheet)
    df_previous = pd.read_excel(filepath, sheet_name=previous_sheet)
    return df_current, df_previous

# Aggregates per-reading rows into one summary row per team, 
# Using collection counts, rates, average time spent, and total consumption to 
# produce columns used by the plotting and analysis nodes.
def summarize_by_team(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("team_name").agg(
        total_readings=("reading_id", "count"),
        collected=("collection_status", lambda x: (x == "Collected").sum()),
        missed=("collection_status", lambda x: (x == "Missed").sum()),
        disputed=("collection_status", lambda x: (x == "Disputed").sum()),
        avg_time_spent_min=("time_spent_min", "mean"),
        total_consumption_kwh=("consumption_kwh", "sum"),
    ).reset_index()

    # Makes easy and readable columns for the report and charting. 
    summary["collection_rate"] = (
        summary["collected"] / summary["total_readings"] * 100
    ).round(1)
    summary["avg_time_spent_min"] = summary["avg_time_spent_min"].round(1)
    return summary

# Returns one row per (team_name, collection_status) with counts.
# This condensed table is used by the Analysis node to reason about misses/disputes per team.
def breakdown_by_status(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["team_name", "collection_status"]).size().reset_index(name="count")
    )
