import re

import epubpacker
import xl

import base
import epub_public

import mn
from epub_public import get_html_id, transform_digit


class TermNotFoundError(Exception):
    pass


def get_sutta_seril_and_name(mulu: str):
    m = re.match(r"^第([〇一二三四五六七八九十]+)　(\S+)$", mulu)
    if m:
        return transform_digit(m.group(1)), m.group(2)

    print(repr(mulu))
    raise Exception


def get_sutta_begin(container: base.Container):
    for term in container.terms:
        if isinstance(term, base.Container):
            seril, _name = get_sutta_seril_and_name(term.mulu)
            return seril
    raise Exception


def get_sutta_end(container: base.Container):
    for term in reversed(container.terms):
        if isinstance(term, base.Container):
            seril, _name = get_sutta_seril_and_name(term.mulu)
            return seril
    raise Exception


def get_sutta_range(container: base.Container):
    return get_sutta_begin(container), get_sutta_end(container)


def write(nikaya: base.Nikaya, ebook: epubpacker.Epub, xc, _test=False) -> base.NoteCollection():
    note_collection = base.NoteCollection()
    c = xc.c

    fake_path = "MN/SN.fake.xhtml"
    elements_before_xy = []
    pian_serial = 0
    for term1 in nikaya.terms:
        if not isinstance(term1, base.Container):
            elements_before_xy.extend(base.term2xml(term1, c, note_collection, fake_path))
            continue

        pian = term1
        pian_serial += 1
        pian_id = "pian{}".format(pian_serial)
        elements_before_xy.append(xl.Element("h1", {"class": "title", "id": pian_id}, [c(pian.mulu)]))

        pian_toc = epubpacker.Toc(c(pian.mulu))
        ebook.root_toc.append(pian_toc)
        for term2 in pian.terms:
            if not isinstance(term2, base.Container):
                elements_before_xy.extend(base.term2xml(term2, c, note_collection, fake_path))
                continue

            pin = term2

            # print("w", term.mulu)

            sutta_begin, sutta_end = get_sutta_range(pin)
            pin_id = epub_public.get_html_id(nikaya, pin)

            pin_toc = epubpacker.Toc("{}　{}~{}".format(c(pin.mulu), sutta_begin, sutta_end))
            pian_toc.kids.append(pin_toc)

            xl.sub(body, "h2", {"class": "title", "id": pin_id}, kids=[c(pin.mulu)])

            elements_before_xy.append(xl.Element("h2", {"class": "title", "id": pin_id}, kids=[c(pin.mulu)]))

            for term3 in pin.terms:
                if not isinstance(term2, base.Container):
                    elements_before_xy.extend(base.term2xml(term2, c, note_collection, fake_path))
                    continue

                sutta = term3
                sutta_seril, sutta_name = get_sutta_seril_and_name(sutta.mulu)
                doc_path = "MN/MN.{}.xhtml".format(sutta_seril)
                html, body = epub_public.make_doc(doc_path=fake_path, xc=xc, title=c(pin.mulu))
                body.attrs["class"] = "sutta"
                body.kids.extend(elements_before_xy)
                elements_before_xy.clear()

                if not pian_toc.href:
                    pian_toc.href = doc_path + "#" + pian_id
                if not pin_toc.href:
                    pin_toc.href = doc_path + "#" + pin_id
                sutta_id = get_html_id(nikaya, sutta)
                sutta_toc = epubpacker.Toc("{}.　{}".format(sutta_seril, c(sutta_name)), doc_path + "#" + sutta_id)
                sutta_title = "MN {}　{}".format(sutta_seril, c(sutta_name))
                body.ekid("h3", {"class": "title", "id": sutta_id}, kids=[c(sutta_title)])
                pin_toc.kids.append(sutta_toc)
                for term4 in sutta.terms:
                    if not isinstance(term4, base.Term):
                        raise Exception
                    body.kids.extend(base.term2xml(term4, c, note_collection, doc_path))

                htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p", "h1", "h2", "h3", "h4"])
                ebook.userfiles[doc_path] = htmlstr
                ebook.spine.append(doc_path)

    return note_collection


def make(xc, temprootdir, books_dir, epubcheck):
    nikaya = mn.get_nikaya()
    epub_public.make(nikaya, write, xc, temprootdir, books_dir, epubcheck)
