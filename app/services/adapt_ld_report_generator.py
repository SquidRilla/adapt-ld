
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64


def generate_adapt_ld_report(student_id, metrics, prediction, images: dict = None):
    """Generate a PDF report and optionally embed provided images.

    images: optional dict mapping title -> base64-encoded PNG data (data URL or raw base64)
    """
    filename = f"adapt_ld_report_{student_id}.pdf"
    doc = SimpleDocTemplate(filename)
    elements = []
    elements.append(Paragraph("ADAPT-LD Diagnostic Report"))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Student ID: {student_id}"))
    elements.append(Paragraph(f"Prediction: {prediction}"))
    elements.append(Spacer(1, 12))
    # Metrics
    if metrics:
        elements.append(Paragraph("Metrics"))
        for k, v in metrics.items():
            try:
                elements.append(Paragraph(f"{k}: {float(v):.3f}"))
            except Exception:
                elements.append(Paragraph(f"{k}: {v}"))
        elements.append(Spacer(1, 12))

    # Embed images
    if images:
        for title, b64 in images.items():
            # accept data URLs or raw base64
            if isinstance(b64, str) and b64.startswith('data:'):
                b64 = b64.split(',', 1)[1]
            try:
                img_data = BytesIO()
                img_data.write(base64.b64decode(b64))
                img_data.seek(0)
                elements.append(Paragraph(title))
                img = Image(ImageReader(img_data), width=400, height=200)
                elements.append(img)
                elements.append(Spacer(1, 12))
            except Exception as e:
                elements.append(Paragraph(f"Could not embed image {title}: {e}"))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Note: Screening support tool only."))
    doc.build(elements)
    return filename
