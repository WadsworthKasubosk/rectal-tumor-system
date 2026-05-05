"""PDF report generation with reportlab."""

from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image


def generate_pdf_report(
    case,           # Case ORM instance
    diagnosis,      # Diagnosis ORM instance
    doctor_notes: str,
    output_path: str,
) -> None:
    """Generate an A4 PDF report with patient info, AI results, and images.

    Args:
        case: Case ORM object (patient_name, patient_gender, patient_age, etc.).
        diagnosis: Diagnosis ORM object (detection_count, scores, etc.).
        doctor_notes: Free-text notes from the doctor.
        output_path: Where to save the PDF file.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register Chinese font — fall back to built-in if not available
    try:
        pdfmetrics.registerFont(TTFont("SimSun", "C:/Windows/Fonts/simsun.ttc"))
        cn_font = "SimSun"
    except Exception:
        cn_font = "Helvetica"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Title ---
    title = Paragraph(f"<b>直肠肿瘤 AI 辅助诊断报告</b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 6 * mm))

    # --- Header info ---
    header_data = [
        ["报告日期:", datetime.now().strftime("%Y-%m-%d")],
        ["患者姓名:", case.patient_name],
        ["性别:", case.patient_gender or "—"],
        ["年龄:", str(case.patient_age) if case.patient_age else "—"],
        ["检查日期:", case.exam_date.strftime("%Y-%m-%d") if case.exam_date else "—"],
        ["检查类型:", case.exam_type or "直肠镜"],
        ["AI 模型:", diagnosis.model_name],
    ]
    for row in header_data:
        story.append(Paragraph(f"<b>{row[0]}</b> {row[1]}", styles["Normal"]))
        story.append(Spacer(1, 1 * mm))

    story.append(Spacer(1, 6 * mm))

    # --- AI Results ---
    story.append(Paragraph("<b>AI 分析结果</b>", styles["Heading2"]))
    result_data = [
        ["指标", "数值"],
        ["检出肿瘤数量", str(diagnosis.detection_count)],
        ["最高置信度", f"{diagnosis.max_confidence:.4f}"],
        ["平均置信度", f"{diagnosis.avg_confidence:.4f}"],
        ["推理耗时 (ms)", f"{diagnosis.inference_time_ms:.1f}"],
    ]
    tbl = Table(result_data, colWidths=[80 * mm, 80 * mm])
    tbl.setStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ])
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # --- Original image ---
    if diagnosis.image_path and Path(diagnosis.image_path).exists():
        story.append(Paragraph("<b>原图</b>", styles["Heading3"]))
        img = Image.open(diagnosis.image_path)
        img.thumbnail((400, 400))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        story.append(RLImage(buf, width=150 * mm, height=100 * mm))

    story.append(Spacer(1, 6 * mm))

    # --- Doctor notes ---
    story.append(Paragraph("<b>医生备注</b>", styles["Heading2"]))
    story.append(Paragraph(doctor_notes or "（无）", styles["Normal"]))
    story.append(Spacer(1, 10 * mm))

    # --- Footer ---
    story.append(Paragraph("医生签名: ____________________", styles["Normal"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("AI 模型版本: YOLO11s-seg", styles["Normal"]))
    story.append(Paragraph(
        "<i>免责声明: 本报告由 AI 辅助生成，仅供临床参考，不能替代专业医学诊断。</i>",
        styles["Normal"],
    ))

    doc.build(story)
