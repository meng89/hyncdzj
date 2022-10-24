#!/usr/bin/env python3
import abc
import re
import os
import datetime

from typing import List

import epubpacker
import xl

import epub_public

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
xmlp5_dir = os.path.join(PROJECT_ROOT, "xml-p5a")


xmls = [
    "N/N13/N13n0006.xml",
    "N/N14/N14n0006.xml",
    "N/N15/N15n0006.xml",
    "N/N16/N16n0006.xml",
    "N/N17/N17n0006.xml",
    "N/N18/N18n0006.xml"
]

g_map = {"#CB03020": "婬"
         }


class SN(object):
    def __init__(self):
        self.terms: List[Container] = []
        self.abbr = "SN"
        self.title_hant = "相應部"
        self.title_pali = "Saṃyutta Nikāya"
        self.last_modified = None


class Container(object):
    def __init__(self, mulu=None):
        self.mulu = mulu
        self.head = None
        self.level = None
        self.terms: List[Container or Term] = []


def is_pin_sub(xy_cbdiv):
    pin_count = 0
    for div in xy_cbdiv.find_kids("cb:div"):
        mulu = div.find_kids("cb:mulu")[0]
        mulu_text = mulu.kids[0]
        m = re.match("^第[一二三四五六七八九十]+.*品.*$", mulu_text)
        if m:
            pin_count += 1

    if pin_count == 1 and len(xy_cbdiv.find_kids("cb:div")) == 1:
        return True
    if pin_count > 1:
        return True
    return False


################################################################################


class Term(object):
    @abc.abstractmethod
    def to_xml(self, *args, **kwargs) -> list:
        pass


class Str(Term):
    def __init__(self, string):
        if isinstance(string, str):
            self._s = string
        else:
            raise TypeError

    def to_xml(self, c, *args, **kwargs):
        return xl.Element("p", kids=[c(self._s)])


class NoteCollection(object):
    def __init__(self, qty_of_list=100, path_prefix=None, id_prefix=None):
        self._qty_of_list = qty_of_list
        self._lists_of_notes = [[]]
        self.path_prefix = path_prefix or "note/note"
        self.id_prefix = id_prefix or "id"

    def add(self, note):
        try:
            return self.get_link(note)
        except NoteNotFoundError:
            last_list = self._lists_of_notes[-1]
            if len(last_list) < self._qty_of_list:
                last_list.append(note)
            else:
                self._lists_of_notes.append([note])
        finally:
            return self.get_link(note)

    def get_link(self, note):
        for notes in self._lists_of_notes:
            for _note in notes:
                if note == _note:
                    doc_path = "{}{}.xhtml".format(self.path_prefix, self._lists_of_notes.index(notes))
                    id_ = "{}{}".format(self.id_prefix, notes.index(note))
                    return doc_path + "#" + id_

        raise NoteNotFoundError

    def write2ebook(self, ebook: epubpacker.Epub, xc):
        for notes in self._lists_of_notes:
            doc_path = "{}{}.xhtml".format(self.path_prefix, self._lists_of_notes.index(notes))
            html, body = epub_public.make_doc(doc_path, xc)
            sec = body.ekid("section", {"epub:type": "endnotes", "role": "doc-endnotes"})
            ol = sec.ekid("ol")
            for note in notes:
                id_ = "{}{}".format(self.id_prefix, notes.index(note))
                li = ol.ekid("li", {"id": id_})
                p = li.ekid("p")
                for x in note.kids:
                    p.kids.extend(term2xml(x, xc.c, self))
            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p"])
            ebook.userfiles[doc_path] = htmlstr
            ebook.spine.append(doc_path)


class Note(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "note":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, c: callable, note_collection: NoteCollection, *args, **kwargs):
        href = note_collection.add(self._e)
        assert len(self._e.kids) == 1
        a = xl.Element("a", {"epub:type": "noteref", "href": href, "class": "noteref"}, [c(self._e.kids[0])])
        return [a]


class P(Term):
    def __init__(self, e):
        if isinstance(e, xl.Element) and e.tag == "p":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, c, note_collection, *args, **kwargs) -> list:
        p = xl.Element("p")
        for x in self._e.kids:
            p.kids.extend(term2xml(x, c, note_collection))
        return [p]


class G(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "g":
            self._e: xl.Element = e

    def to_xml(self, c, *args, **kwargs) -> list:
        return [c(g_map[self._e.attrs["ref"]])]


class Ref(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "ref":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, *args, **kwargs) -> list:
        return [self._e]


class Lg(Term):
    def __init__(self, e):
        if isinstance(e, xl.Element) and e.tag == "lg":
            pass
        else:
            raise TypeError

        self._poet = None
        self._body = []

        for le in e.find_kids("l"):
            line = []
            sentence = []
            for _lkid in le.kids:
                if isinstance(_lkid, str):
                    m = re.match(r"^(〔.+〕)(.+)$", _lkid)
                    if m:
                        assert self._poet is None
                        self._poet = m.group(1)
                        sentence.append(m.group(2))
                    else:
                        sentence.append(_lkid)

                elif isinstance(_lkid, xl.Element):
                    if _lkid.tag == "caesura":
                        line.append(sentence)
                        sentence = []
                        continue

                    else:
                        sentence.append(do_atom(_lkid))

            assert sentence
            line.append(sentence)
            self._body.append(line)

    def to_xml(self, c, *args, **kwargs) -> list:
        div = xl.Element("div", {"class": "ji"})
        if self._poet:
            div.ekid("p", {"class": "_poet"}, [term2xml(self._poet, c, *args, **kwargs)])
        for line in self._body:
            for sentence in line:
                div.ekid("p", {"class": "sentence"}, [term2xml(sentence, c, *args, **kwargs)])

        return [div]


class App(Term):
    def __init__(self, e):
        if isinstance(e, xl.Element) and e.tag == "app":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, c, *args, **kwargs) -> list:
        lem = self._e.kids[0]
        if isinstance(lem.kids[0], str):
            return [c(lem.kids[0])]
        elif isinstance(lem.kids[0], xl.Element) and lem.kids[0].tag == "space":
            return []


def term2xml(term: Term or str, c, note_collection):
    if isinstance(term, str):
        return [c(term)]
    elif isinstance(term, Term):
        return term.to_xml(c, note_collection)
    input(("type:{}".format(type(term))))
    raise Exception


class NoteNotFoundError(object):
    pass


###############################################################################

def do_atom(atom: any):
    for Class in (Str, Lg, P, G, Ref, Note, App):
        try:
            return Class(atom)
        except TypeError:
            continue
    raise TypeError


################################################################################

class ElementError(Exception):
    pass


def get_parent_container(container, level):
    if level == 1:
        return container
    else:
        for term in reversed(container.terms):
            if isinstance(term, Container):
                return get_parent_container(term, level - 1)

    raise Exception("cant be here")


def get_last_container(container):
    for term in reversed(container.terms):
        if isinstance(term, Container):
            return get_last_container(term)

    return container


def make_tree(sn: Container or SN, cbdiv: xl.Element):
    # cb:mulu 出现在目录中，而 head 出现在正文的标题中。head 有时会有 note 。两者似乎有冗余，也许该在上游精简。
    # 少数 cb:div 标签中无 head。

    # 少数 cb:div 标签中第一个子标签不是cb:mulu.

    kids = cbdiv.kids

    if kids[0].tag == "cb:mulu":
        _str_level = kids[0].attrs["level"]
        level = int(_str_level)
        parent = get_parent_container(sn, level)

        if level == 1:
            _pian_mulu = kids[0].kids[0]  # 篇
            m = re.match(r"^(.+篇).* \(\d+-\d+\)$", _pian_mulu)
            assert m
            mulu = m.group(1)
            if len(parent.terms) == 0 or parent.terms[-1].mulu != mulu:
                container = Container()
                container.level = level
                container.mulu = mulu
                parent.terms.append(container)
            else:
                container = parent.terms[-1]
        else:
            container = Container()
            container.level = level
            assert len(kids[0].kids) == 1
            container.mulu = kids[0].kids[0]
            parent.terms.append(container)

        kids.pop(0)

    # SN.46.6
    else:
        for kid in kids:
            if isinstance(kid, xl.Element):
                if kid.tag == "cb:mulu":
                    input(kid.tag)

        container = get_last_container(sn)

    first = cbdiv.kids[0]
    if isinstance(first, xl.Element) and first.tag == "head":
        container.head = first.kids[:]
        # input(container.head)
        cbdiv.kids.pop(0)

    for kid in cbdiv.kids:
        if isinstance(kid, xl.Element) and kid.tag == "cb:div":
            make_tree(sn, kid)

        else:
            container.terms.append(do_atom(kid))


def get_tree():
    snikaya = SN()
    for one in xmls:
        filename = os.path.join(xmlp5_dir, one)
        file = open(filename, "r")
        last_modified = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
        if snikaya.last_modified:
            if snikaya.last_modified < last_modified:
                snikaya.last_modified = last_modified
        else:
            snikaya.last_modified = last_modified

        xmlstr = file.read()

        xml = xl.parse(xmlstr, do_strip=True)

        tei = xml.root

        tei = filter_element(tei, is_lb)
        tei = filter_element(tei, is_pb)
        tei = filter_element(tei, is_num_p)

        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]
        print(one)

        for cb_div in body.find_kids("cb:div"):
            make_tree(snikaya, cb_div)

    return snikaya


def is_lb(x):
    # <lb ed="N" n="0206a14"/>
    if isinstance(x, xl.Element):
        if x.tag == "lb":
            if x.attrs["ed"] == "N":
                if "n" in x.attrs.keys():
                    if not x.kids:
                        return True
    return False


def is_pb(x):
    # <pb ed="N" xml:id="N18.0006.0207a" n="0207a"/>
    if isinstance(x, xl.Element):
        if x.tag == "pb":
            if x.attrs["ed"] == "N":
                if "n" in x.attrs.keys():
                    if "xml:id" in x.attrs.keys():
                        if not x.kids:
                            return True
    return False


def is_num_p(x):
    if isinstance(x, xl.Element):
        if x.tag == "p":
            if len(x.kids) == 1:
                if re.match(r"^[〇一二三四五六七八九十]+$", x.kids[0]):
                    return True
    return False


def filter_element(x: xl.Element or str, fun: callable):
    if isinstance(x, xl.Element):
        new_e = xl.Element(tag=x.tag, attrs=x.attrs)
        for kid in x.kids:
            if fun(kid):
                pass
            else:
                new_e.kids.append(filter_element(kid, fun))
        return new_e

    elif isinstance(x, str):
        return x

    raise TypeError


def is_sutta_parent(parent_container: Container):
    len_of_container = 0
    lot_of_match = 0
    for sub in parent_container.terms:
        if isinstance(sub, Container):
            len_of_container += 1

            if not isinstance(sub.mulu, str):
                input(sub.mulu)

            m = re.match(r"^〔[、～〇一二三四五六七八九十]+〕.*$", sub.mulu)
            if m:
                lot_of_match += 1

    if lot_of_match:
        if lot_of_match == len_of_container:
            return True
        else:
            print("需要检查子div:{}".format(parent_container.mulu, 1))
            print("len_of_container:", len_of_container)
            print("lot_of_match:", lot_of_match)
            input()
            return False
    else:
        return False


def traverse_sn(sn: SN):
    for pian in sn.terms:
        print(pian)


def print_title(sn):
    for pian in sn.terms:
        print_title2(pian, 0)


def print_title2(container, depth):
    for term in container.terms:
        if isinstance(term, Container):
            if is_sutta_parent(container):
                print(" " * depth, "<Sutta>:", term.mulu, sep="")
            else:
                print(" " * depth, term.mulu, sep="")
            print_title2(term, depth + 4)


def check_x_first_term(sn):
    for pian in sn.terms:
        term = pian.terms[0]
        print(pian.mulu)
        if not isinstance(term, Container):
            print(term)


def main():
    sn = get_tree()
    print_title2(sn, 0)
    check_x_first_term(sn)


if __name__ == "__main__":
    main()
