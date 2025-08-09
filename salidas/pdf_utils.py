import os
import io
from pypdf import PdfReader
from django.conf import settings
from svglib.svglib import svg2rlg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics import renderPDF
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    if uri.startswith(settings.STATIC_URL):
        path = uri[len(settings.STATIC_URL):]
        real_path = finders.find(path)
        if real_path:
            return real_path
    return uri

def create_watermark_page(svg_uri):
    # Resuelve ruta de disco y carga el SVG
    svg_path = finders.find(svg_uri)
    drawing = svg2rlg(svg_path)
    w, h = A4

    # Calcula factor de escala 
    max_width  = w * 0.7
    max_height = h * 0.7
    scale_w = max_width  / drawing.width
    scale_h = max_height / drawing.height
    scale = min(scale_w, scale_h, 1)  

    # Prepara canvas
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    c.saveState()
    c.setFillAlpha(0.1)  

    # Aplica escala y centra
    c.translate(w/2, h/2)
    c.scale(scale, scale)
    renderPDF.draw(
        drawing,
        c,
        -drawing.width/2,
        -drawing.height/2,
    )

    c.restoreState()
    c.showPage()
    c.save()
    packet.seek(0)

    return PdfReader(packet).pages[0]

