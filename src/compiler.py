"""
This compiles the generated sections into a single PDF using Markdown -> HTML -> PDF.

The compiler expects `state['sections']` to contain the keys produced by
the nodes and `state['chart_path']` to point to the saved chart image.

We use `weasyprint` to convert the rendered HTML to PDF.
"""

import markdown
from weasyprint import HTML

# Creates a markdown string with the report sections and chart image, then renders to PDF.
def compile_to_pdf(state, output_path="output/monthly_report.pdf"):

    sections = state["sections"]

    md = f"""# Monthly Meter Collection Report
## {state['current_month']} vs {state['previous_month']}

### Introduction
{sections['intro']}

### Collection Rate Overview
![Collection Rate Chart]({state['chart_path']})

{sections['comment']}

### Analysis
{sections['analysis']}

### Recommendations
{sections['recommendation']}

### Conclusion
{sections['conclusion']}
"""

    html_body = markdown.markdown(md)
    HTML(string=html_body, base_url=".").write_pdf(output_path)
    return output_path
