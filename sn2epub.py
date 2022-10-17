import epubpacker
import xl

import epub_public


import sn


def write_suttas(nikaya: sn.SN, epub: epubpacker.Epub, bns, xc, _test=False):
    c = xc.c
    xy_serial = 0
    for pian in nikaya.terms:
        def _write_pian_part(_body):
            xl.sub(_body, "h1", {"class": "title"}, [c(pian.title)])
            nonlocal pian_toc

        for xy in pian.terms:
            xy_serial += 1
            xy_id = "sn"
            doc_path = "SN/SN.{}.xhtml".format(xy_serial)
            _xy_title = xy_serial + ". " + c(xy.title)
            html, body = epub_public.make_doc(doc_path=doc_path, xc=xc, title=_xy_title)








def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub_public.make(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
