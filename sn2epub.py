import re

import epubpacker
import xl

import epub_public

import sn


def term2xml(term):
    return term.to_xml()


class TermNotFoundError(Exception):
    pass


def html_id(container, term, prefix=None):
    prefix = prefix or "id"
    serial = 0
    for _term in container.terms:
        serial += 1

        current_prefix = "{}-{}".format(prefix, serial)
        if _term == term:
            return current_prefix

        if isinstance(_term, container):
            try:
                return html_id(_term, term, current_prefix)
            except TermNotFoundError:
                pass

    raise TermNotFoundError()


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



def write_suttas(nikaya: sn.SN, ebook: epubpacker.Epub, bns, xc, _test=False):
    c = xc.c
    xy_serial = 0

    elements_before_xy = []
    pian_serial = 0
    for pian in nikaya.terms:
        pian_serial += 1
        pian_title = pian.mulu
        pian_id = "pian{}".format(pian_serial)
        elements_before_xy.append(xl.Element("h1", {"class": "title", "id": pian_id}, [c(pian_title)]))

        _xy_begin, _xy_end = _xy_range(nikaya, pian)
        pian_toc = epubpacker.Toc(c(pian_title) + " {}~{}".format(_xy_begin, _xy_end))
        ebook.root_toc.append(pian_toc)

        for sub in pian.terms:
            if not isinstance(sub, sn.Container):
                elements_before_xy.append(term2xml(sub))
                continue

            xy = sub
            xy_serial += 1
            xy_id = "sn{}".format(xy_serial)
            doc_path = "SN/SN.{}.xhtml".format(xy_serial)

            if xy_serial == _xy_begin:
                pian_toc.href = doc_path + "#" + pian_id

            xy_name = _xy_name(xy)
            xy_toc = epubpacker.Toc("{}. {}".format(xy_serial, xy_name), doc_path + "#" + xy_id)
            pian_toc.kids.append(xy_toc)
            _xy_title = "{}. {}".format(xy_serial, c(xy_name))
            html, body = epub_public.make_doc(doc_path=doc_path, xc=xc, title=_xy_title)
            body.kids.extend(elements_before_xy)
            elements_before_xy.clear()
            xl.sub(body, "h2", {"class": "title", "id": xy_id}, kids=[_xy_title])

            if sn.is_sutta(xy):
                write_sutta(xy)
            else:
                write_before_sutta(xy, ebook, xc, body)


def write_before_sutta(nikaya: sn.SN, container: sn.Container, ebook: epubpacker.Epub, xc, body: xl.Element):
    for term in container.terms:
        _html_id = html_id(nikaya, term)
        title =
        xl.sub(body, "h3", {"class": "title", "id": _html_id}, kids=[c(pin.title)])


def write_sutta(container):
    # todo


def write_after_sutta():
    #todo


def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub_public.make(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
