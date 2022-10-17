import re

import epubpacker
import xl

import epub_public

import sn


def _pian_title_and_range(pian: sn.Container):
    m = re.match(r"^(.+篇) \((\d+)-(\d+)\)$", pian.mulu)
    assert m
    return m.group(0), m.group(1), m.group(2)


def _xy_range(snikaya: sn.Container, pian: sn.Container):
    xy_counter = 0
    xy_begin = None
    xy_end = None
    for _pian in snikaya.terms:
        if _pian is pian:
            xy_begin = xy_counter + 1

        for xy in _pian.terms:
            if not isinstance(xy, sn.Container):
                continue
            xy_counter += 1

        if _pian is pian:
            xy_end = xy_counter
            break
    return xy_begin, xy_end


def _sutta_range(container: sn.Container):
    pass


def write_suttas(nikaya: sn.SN, epub: epubpacker.Epub, bns, xc, _test=False):
    c = xc.c
    xy_serial = 0
    for pian in nikaya.terms:
        pian_title = pian.mulu

        def _write_pian_part(_body):
            xl.sub(_body, "h1", {"class": "title"}, [c(pian_title)])
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
