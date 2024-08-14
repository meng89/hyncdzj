#!/usr/bin/env python3
import reportlab.platypus.doctemplate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, A6, A8

from reportlab.pdfbase.cidfonts import UnicodeCIDFont

class MyDoc(reportlab.platypus.doctemplate.BaseDocTemplate):
    pass


def main():
    print(reportlab.platypus.doctemplate.BaseDocTemplate)




if __name__ == "__main__":
    main()
