#!/usr/bin/env python3

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus.frames import Frame
from reportlab.lib.units import cm


class MyDocTemplate(BaseDocTemplate):

    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('normal', [Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')])
        self.addPageTemplates(template)
        self.chapter = 0
        self.section = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'Title':
                self.chapter += 1
                self.canv.bookmarkPage(f"chapter{self.chapter}")
                self.canv.addOutlineEntry(f"Chapter {self.chapter}", f"chapter{self.chapter}", level=0)
            elif style == 'Heading1':
                self.section += 1
                self.canv.bookmarkPage(f"section{self.section}")
                self.canv.addOutlineEntry(f"Section {self.section}", f"section{self.section}", level=1)


def main(filename):
    path = "/mnt/data/projects/noto-cjk/Serif/Variable/TTF/Subset/NotoSerifSC-VF.ttf",
    path = "/mnt/data/projects/noto-cjk/Serif/Variable/TTF/NotoSerifCJKsc-VF.ttf"
    # path = "/mnt/data/projects/noto-cjk/Serif/OTC/NotoSerifCJK-Regular.ttc"
    path = "/mnt/data/projects/noto-cjk/Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Regular.otf"
    path = "/mnt/data/projects/note-cjk2/NotoSerifCJKjp-Regular.ttf"
    nscr = "nscr"
    pdfmetrics.registerFont(TTFont(nscr, path))
    pdfmetrics.registerFont(UnicodeCIDFont(path))

    title = ParagraphStyle(name='Title',
                           # fontName='Noto Serif CJK SC Light',
                           fontname=nscr,
                           fontSize=22,
                           leading=16,
                           alignment=1,
                           spaceAfter=20)

    h1 = ParagraphStyle(
        name='Heading1',
        fontSize=14,
        leading=16)

    story = []

    story.append(Paragraph('继承BaseDocTemplate', title))
    story.append(Paragraph('Section 1', h1))
    story.append(Paragraph('Text in Section 1.1'))
    story.append(PageBreak())
    story.append(Paragraph('Section 2', h1))
    story.append(Paragraph('怎么肥四？'))
    story.append(PageBreak())
    story.append(Paragraph('Chapter 2', title))
    story.append(Paragraph('Section 1', h1))
    story.append(Paragraph('Text in Section 2.1'))

    doc = MyDocTemplate(filename)
    doc.build(story)


if __name__ == "__main__":
    main("x.pdf")
