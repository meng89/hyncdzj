import re

import epubpacker
import xl

import epub_public

import sn

def term2xml(term):
    return term.to_xml()


def _xy_range(snikaya: sn.SN, pian: sn.Container):
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


def _xy_name(xy: sn.Container):
    m = re.match(r"^第[一二三四五六七八九十]+　(.+相應)$", xy.mulu)
    return m.group(0)


def _sutta_range(container: sn.Container):



def write_suttas(nikaya: sn.SN, epub: epubpacker.Epub, bns, xc, _test=False):
    c = xc.c
    xy_serial = 0

    elements_before_xy = []

    for pian in nikaya.terms:
        pian_title = pian.mulu

        elements_before_xy.append(xl.Element("h1", {"class": "title"}, [c(pian_title)]))

        _xy_begin, _xy_end = _xy_range(nikaya, pian)
        pian_toc = epubpacker.Toc(
            c(pian_title) + "({}~{})".format(_xy_begin, _xy_end))
        epub.root_toc.append(pian_toc)

        for sub in pian.terms:
            if not isinstance(sub, sn.Container):
                elements_before_xy.append()

            xy = sub

            xy_serial += 1
            xy_id = "sn"
            doc_path = "SN/SN.{}.xhtml".format(xy_serial)
            _xy_title = "{}. {}".format(xy_serial, c(_xy_name(xy)))
            html, body = epub_public.make_doc(doc_path=doc_path, xc=xc, title=_xy_title)


def write2(container: sn.Container, epub: epubpacker.Epub, xc, body: xl.Element):
    fot sub in container.terms



def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub_public.make(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
