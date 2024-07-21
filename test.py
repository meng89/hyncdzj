#!/usr/bin/env python3

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, A6, A8


def hello(c):
    c.drawString(100, 100, "Hello World")


c = canvas.Canvas("hello.pdf", pagesize=A8)

hello(c)
c.showPage()
c.save()
