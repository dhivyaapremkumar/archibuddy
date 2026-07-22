"""Compliance PDF report, built with fpdf2."""
from datetime import datetime

from fpdf import FPDF

from app.features.compliance.rules import RULES


def build_pdf_bytes(check_result: dict) -> bytes:
    inputs = check_result["inputs"]

    pdf = FPDF(format="A4", unit="pt")
    pdf.set_auto_page_break(auto=True, margin=48)
    pdf.add_page()
    left = 48

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(31, 56, 100)
    pdf.set_xy(left, 40)
    pdf.cell(0, 22, "TN Compliance Copilot — Compliance report", ln=1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.set_x(left)
    pdf.cell(0, 14, "TNCDBR 2019 - DTCP jurisdiction - Non-high-rise residential", ln=1)
    pdf.set_x(left)
    pdf.cell(0, 14, f"Generated: {datetime.now():%Y-%m-%d %H:%M}", ln=1)
    pdf.ln(8)

    pdf.set_draw_color(220, 220, 220)
    pdf.line(left, pdf.get_y(), 547, pdf.get_y())
    pdf.ln(14)

    def row(label, value):
        pdf.set_x(left)
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(260, 16, label)
        pdf.cell(0, 16, str(value), ln=1)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(20, 20, 20)
    pdf.set_x(left)
    pdf.cell(0, 18, "Plot details", ln=1)

    row("Frontage width (road-facing)", f"{inputs['frontage_ft']} ft")
    row("Depth (front to back)", f"{inputs['depth_ft']} ft")
    row("Abutting road width", f"{inputs['road_ft']} ft")
    row("Floors", inputs["floors"])
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(left)
    pdf.cell(0, 18, "Computed compliance envelope", ln=1)

    row("Front setback (road width table)", f"{check_result['front_ft']:.1f} ft")
    row("Side setback (height / plot width table)", f"{check_result['side_ft']:.1f} ft")
    row("Rear setback (building height table)", f"{check_result['rear_ft']:.1f} ft")
    row(f"Maximum built-up area (FSI {RULES['fsi']:.1f})", f"{check_result['max_fsi_sqft']:.0f} sqft")
    row("Buildable footprint at ground level", f"{check_result['buildable_sqft']:.0f} sqft")
    row("Estimated parking requirement", f"{check_result['parking']} covered space(s)")
    pdf.ln(6)

    if check_result.get("warning"):
        pdf.set_text_color(160, 40, 40)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(left)
        pdf.multi_cell(499, 14, f"Warning: {check_result['warning']}")
        pdf.ln(4)
        pdf.set_text_color(20, 20, 20)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(left)
    pdf.cell(0, 18, "Mandatory requirements", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(left)
    pdf.cell(0, 16, "Rainwater harvesting is mandatory for all developments under TNCDBR 2019.", ln=1)
    pdf.ln(10)

    pdf.set_draw_color(220, 220, 220)
    pdf.line(left, pdf.get_y(), 547, pdf.get_y())
    pdf.ln(14)

    disclaimer = (
        f"Rule set: {check_result['rules_version']}. These figures are drawn from secondary "
        "TNCDBR 2019 summaries and have not yet been verified against the official gazette "
        "text or subsequent amendments. This report is a compliance aid for internal use and "
        "does not substitute for verification by a licensed architect or the relevant "
        "sanctioning authority (DTCP) before submission."
    )
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.set_x(left)
    pdf.multi_cell(499, 11, disclaimer)

    out = pdf.output()
    return bytes(out)
