"""
This is just a labeled box that gets passed from step to step.

Every step in the pipeline (writing the intro, making the chart, writing
the analysis, etc.) reads what it needs from this box and adds its own
result back into it, so the next step has everything so far.
"""

from typing import TypedDict
import pandas as pd


class ReportState(TypedDict):
# The two months being compared    
    current_month: str
    previous_month: str

    # Tables with one row per team, for each month
    team_summary_current: pd.DataFrame
    team_summary_previous: pd.DataFrame

    # Table that shows how many readings were collected, missed, or disputed per team
    breakdown: pd.DataFrame

    # Notes provided by the user to give context to the analysis (e.g., known issues, special circumstances)
    manual_notes: str

    # Saves the chart image to disk and stores the path here for later use in the PDF.
    chart_path: str

    # The actual written report text, one entry per section
    # (intro, comment, analysis, recommendation, conclusion)
    sections: dict

    # Builder/Critic loop state for analysis section
    analysis_feedback: str
    analysis_retry_count: int
    analysis_status: str

    # Final produced PDF path
    final_pdf_path: str
