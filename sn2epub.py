import re

import epubpacker
import xl

import base
import epub_public

import sn_from_xml
from epub_public import get_html_id, transform_digit


def _xy_range(snikaya: sn.SN, pian: base.Container):
    xy_counter = 0
    xy_begin = None
    xy_end = None
    for _pian in snikaya.terms:
        if _pian is pian:
            xy_begin = xy_counter + 1

        for xy in _pian.terms:
            if not isinstance(xy, base.Container):
                continue
            xy_counter += 1

        if _pian is pian:
            xy_end = xy_counter
            break
    return xy_begin, xy_end


def get_sutta_range_and_name(mulu: str):
    m = re.match(r"〔([〇一二三四五六七八九十]+)〕(\S*)$", mulu)
    if m:
        serial = transform_digit(m.group(1))
        return serial, serial, m.group(2)

    m = re.match(r"〔([〇一二三四五六七八九十]+)〕第\S+?　(.*)$", mulu)
    if m:
        serial = transform_digit(m.group(1))
        return serial, serial, m.group(2)

    m = re.match(r"〔([〇一二三四五六七八九十]+)[、|～]([〇一二三四五六七八九十]+)〕(\S*)$", mulu)
    if m:
        return transform_digit(m.group(1)), transform_digit(m.group(2)), m.group(3)

    m = re.match(r"〔([〇一二三四五六七八九十]+)[、|～]([〇一二三四五六七八九十]+)〕"
                 r"第\S+　(\S*)$", mulu)
    if m:
        return transform_digit(m.group(1)), transform_digit(m.group(2)), m.group(3)

    if mulu == "〔三八～四三〕第八　父、第九　兄弟、第十　姊妹、第十一　子、第十二　女、第十三　妻":
        return 38, 43, "父、兄弟、姊妹、子、女、妻"

    print(repr(mulu))
    raise Exception


def get_first_container_term(terms):
    for term in terms:
        if isinstance(term, base.Container):
            return term
    raise Exception


def get_sutta_begin(container: base.Container):
    if sn.is_sutta_parent(container):
        return get_sutta_range_and_name(get_first_container_term(container.terms).mulu)[0]
    else:
        return get_sutta_begin(get_first_container_term(container.terms))


def get_sutta_end(container: base.Container):
    if sn.is_sutta_parent(container):
        return get_sutta_range_and_name(get_first_container_term(reversed(container.terms)).mulu)[0]
    else:
        last = get_first_container_term(reversed(container.terms))
        return get_sutta_end(last)


def get_sutta_range(container: base.Container):
    return get_sutta_begin(container), get_sutta_end(container)


def write(nikaya, ebook: epubpacker.Epub, xc, _test=False) -> base.NoteCollection():
    note_collection = base.NoteCollection()
    c = xc.c
    xy_serial = 0

    elements_before_xy = []
    pian_serial = 0
    for pian in nikaya.terms:
        pian_serial += 1
        pian_id = "pian{}".format(pian_serial)
        elements_before_xy.append(xl.Element("h1", {"class": "title", "id": pian_id}, [c(pian.mulu)]))

        _xy_begin, _xy_end = _xy_range(nikaya, pian)
        pian_toc = epubpacker.Toc(c(pian.mulu) + " {}~{}".format(_xy_begin, _xy_end))
        ebook.root_toc.append(pian_toc)

        for term in pian.terms:
            if not isinstance(term, base.Container):
                elements_before_xy.extend(base.term2xml(term, c, note_collection, "SN/SN.fake.xhtml"))
                continue

            xy = term
            # print("w", term.mulu)
            xy_serial += 1
            xy_id = "sn{}".format(xy_serial)
            doc_path = "SN/SN.{}.xhtml".format(xy_serial)

            if xy_serial == _xy_begin:
                pian_toc.href = doc_path + "#" + pian_id

            xy_toc = epubpacker.Toc("{}. {}".format(xy_serial, xy.mulu), doc_path + "#" + xy_id)
            pian_toc.kids.append(xy_toc)
            _xy_title = "{}. {}".format(xy_serial, c(xy.mulu))
            html, body = epub_public.make_doc(doc_path=doc_path, xc=xc, title=_xy_title)
            body.attrs["class"] = "sutta"
            body.kids.extend(elements_before_xy)
            elements_before_xy.clear()
            xl.sub(body, "h2", {"class": "title", "id": xy_id}, kids=[_xy_title])

            if sn.is_sutta_parent(xy):
                write_sutta_parent(nikaya, xy, xy_serial, note_collection, doc_path, xy_toc, xc, body)
            else:
                write_before_sutta(nikaya, xy, xy_serial, note_collection, doc_path, xy_toc, xc, body)

            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p", "h1", "h2", "h3", "h4"])
            ebook.userfiles[doc_path] = htmlstr
            ebook.spine.append(doc_path)

    return note_collection


def write_before_sutta(nikaya: sn.SN, container: base.Container, xy_serial, note_collection,
                       doc_path, toc,
                       xc, body: xl.Element):
    c = xc.c
    for _x in container.terms:
        if isinstance(_x, base.Head):
            continue

        if isinstance(_x, base.Term):
            body.kids.extend(base.term2xml(_x, c, note_collection, doc_path))
            continue

        term = _x
        # print("wbs", term.mulu)
        _html_id = get_html_id(nikaya, term)
        xl.sub(body, "h3", {"class": "title", "id": _html_id}, kids=[c(term.mulu)])
        sutta_begin, sutta_end = get_sutta_range(term)
        toc_name = "{} {}~{}".format(term.mulu, sutta_begin, sutta_end)
        my_toc = epubpacker.Toc(toc_name, doc_path + "#" + _html_id)
        toc.kids.append(my_toc)

        if sn.is_sutta_parent(term):
            write_sutta_parent(nikaya, term, xy_serial, note_collection, doc_path, my_toc, xc, body)
        else:
            write_before_sutta(nikaya, term, xy_serial, note_collection, doc_path, my_toc, xc, body)


def write_sutta_parent(nikaya, container, xy_serial, note_collection, doc_path, toc, xc, body):
    c = xc.c
    for _x in container.terms:
        if isinstance(_x, base.Term):
            body.kids.extend(base.term2xml(_x, c, note_collection, doc_path))
            continue
        sutta = _x
        # print("ws", sutta.mulu, sutta.level)
        sutta_begin, sutta_end, name = get_sutta_range_and_name(sutta.mulu)
        _html_id = get_html_id(nikaya, sutta)
        if sutta_begin == sutta_end:
            serial = sutta_begin
        else:
            serial = "{}~{}".format(sutta_begin, sutta_end)
        sutta_toc = epubpacker.Toc("{}. {}".format(serial, c(name)), doc_path + "#" + _html_id)
        toc.kids.append(sutta_toc)

        title = "SN {}.{}　{}".format(xy_serial, serial, c(name))
        body.ekid("h4", {"class": "title", "id": get_html_id(nikaya, sutta)}, kids=[title])

        for x in sutta.terms:
            if isinstance(x, base.Container):
                write_after_sutta(nikaya, x, note_collection, doc_path, sutta_toc, xc, body)
            else:
                body.kids.extend(base.term2xml(x, c, note_collection, doc_path))


def write_after_sutta(nikaya, container, note_collection, doc_path, toc, xc, body):
    c = xc.c
    body.ekid("h5", {"class": "title", "id": get_html_id(nikaya, container)}, kids=[c(container.mulu)])
    _html_id = get_html_id(nikaya, container)
    toc.kids.append(epubpacker.Toc(c(container.mulu), doc_path + "#" + _html_id))

    for term in container.terms:
        if not isinstance(term, base.Term):
            print("ccc", type(term))
            raise Exception
        body.kids.extend(base.term2xml(term, c, note_collection, doc_path))


def make(xc, temprootdir, books_dir, epubcheck):
    nikaya = sn.get_nikaya()
    epub_public.make(nikaya, write, xc, temprootdir, books_dir, epubcheck)
