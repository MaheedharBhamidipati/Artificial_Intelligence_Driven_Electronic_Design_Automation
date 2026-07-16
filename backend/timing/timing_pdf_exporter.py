# ================================================================
# TIMING PDF EXPORTER
# ================================================================

from reportlab.platypus import (

    SimpleDocTemplate,

    Paragraph,

    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


class TimingPDFExporter:

    def __init__(

        self,

        output_file="timing_report.pdf"
    ):

        self.output_file = output_file

    # ============================================================
    # EXPORT PDF
    # ============================================================

    def export(

        self,

        reports
    ):

        doc = SimpleDocTemplate(

            self.output_file
        )

        styles = getSampleStyleSheet()

        elements = []

        title = Paragraph(

            "Timing Analysis Report",

            styles["Title"]
        )

        elements.append(title)

        elements.append(

            Spacer(1, 12)
        )

        for report in reports:

            text = (

                f'Startpoint: '
                f'{report.get("startpoint")}<br/>'

                f'Endpoint: '
                f'{report.get("endpoint")}<br/>'

                f'Slack: '
                f'{report.get("slack")} ns<br/>'

                f'Status: '
                f'{report.get("status")}<br/>'

                f'Violation Type: '
                f'{report.get("violation_type")}<br/><br/>'
            )

            para = Paragraph(

                text,

                styles["BodyText"]
            )

            elements.append(para)

            elements.append(

                Spacer(1, 10)
            )

        doc.build(elements)

        return self.output_file