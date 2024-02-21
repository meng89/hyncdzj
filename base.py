import abc
import datetime
import re
import os
from typing import List

import epubpacker
import xl
import config

g_map = {"#CB03020": "婬"
         }


class Book(object):
    def __init__(self):
        self._abbr = None
        self._name_hant = None
        self._name_pali = None
        self._mtime = None
        self._terms = []

    @property
    def abbr(self) -> str:
        return self._abbr

    @property
    def name_hant(self) -> str:
        return self._name_hant

    @property
    def name_pali(self) -> str:
        return self._name_pali

    @property
    def mtime(self) -> datetime.datetime:
        return self._mtime

    @mtime.setter
    def mtime(self, value: datetime.datetime):
        self._mtime = value

    @property
    def terms(self):
        return self._terms


class Container(object):
    def __init__(self, mulu=None):
        self.mulu = mulu
        self.head = None
        self.level = None
        self.terms: List[Container or Term] = []


class Term(object):
    @abc.abstractmethod
    def to_xml(self, *args, **kwargs) -> list:
        pass


class Head(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "head":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, *args, **kwargs) -> list:
        return []


class Str(Term):
    def __init__(self, string):
        if isinstance(string, str):
            self._s = string
        else:
            raise TypeError

    def to_xml(self, c, *args, **kwargs):
        return [c(self._s)]


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
        import epub_public

        toc = epubpacker.Toc(xc.c("註解"))

        for notes in self._lists_of_notes:
            doc_path = "{}{}.xhtml".format(self.path_prefix, self._lists_of_notes.index(notes))
            html, body = epub_public.make_doc(doc_path, xc, xc.c("註解"))
            body.attrs["class"] = "note"
            sec = body.ekid("section", {"epub:type": "endnotes", "role": "doc-endnotes"})
            ol = sec.ekid("ol")
            for note in notes:

                if toc.href:
                    pass
                else:
                    toc.href = doc_path
                    ebook.root_toc.append(toc)

                id_ = "{}{}".format(self.id_prefix, notes.index(note))
                li = ol.ekid("li", {"id": id_})
                p = li.ekid("p")
                for x in note.kids:
                    term = do_atom(x)
                    p.kids.extend(term2xml(term, xc.c, self, doc_path))
            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p"])
            ebook.userfiles[doc_path] = htmlstr
            ebook.spine.append(doc_path)


class Note(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "note":
            self._e = e
            self.n = e.attrs["n"]
            self._terms = []
            for x in e.kids:
                self._terms.append(do_atom(x))
        else:
            raise TypeError

    def to_xml(self, c: callable, note_collection: NoteCollection, doc_path, *args, **kwargs):
        import epub_public
        note_href = note_collection.add(self._e)
        href = epub_public.relpath(note_href, doc_path)
        a = xl.Element("a", {"epub:type": "noteref", "href": href, "class": "noteref"})
        a.kids.append("[注]")
        return [a]


class Space(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "space":
            self._e = e

    def to_xml(self, *args, **kwargs) -> list:
        return []


class P(Term):
    def __init__(self, e):
        if isinstance(e, xl.Element) and e.tag == "p":
            self._e = e
            self._terms = []
            for x in e.kids:
                self._terms.append(do_atom(x))
        else:
            raise TypeError

    def to_xml(self, *args, **kwargs) -> list:
        p = xl.Element("p")
        for x in self._terms:
            p.kids.extend(x.to_xml(*args, **kwargs))

        return [p]


class G(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "g":
            self._e: xl.Element = e
        else:
            raise TypeError

    def to_xml(self, c, *args, **kwargs) -> list:
        return [c(g_map[self._e.attrs["ref"]])]


class Ref(Term):
    def __init__(self, e: xl.Element):
        if isinstance(e, xl.Element) and e.tag == "ref":
            self._e = e
        else:
            raise TypeError

    def to_xml(self, *args, **kwargs) -> list:
        return []


class Lg(Term):
    def __init__(self, e):
        if isinstance(e, xl.Element) and e.tag == "lg":
            self._e = e
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
            div.ekid("p", {"class": "poet"}, term2xml(self._poet, c, *args, **kwargs))
        for line in self._body:
            for sentence in line:
                p = div.ekid("p", {"class": "sentence"})
                for term in sentence:
                    if isinstance(term, str):
                        term = term.replace("「", "").replace("」", "")
                    p.kids.extend(term2xml(term, c, *args, **kwargs))

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


def term2xml(term: Term or str, c, note_collection, doc_path):
    if isinstance(term, str):
        return [c(term)]
    elif isinstance(term, Term):
        return term.to_xml(c, note_collection, doc_path)
    raise Exception


class NoteNotFoundError(Exception):
    pass


def do_atom(atom: any):
    for Class in (Head, Str, Lg, P, G, Ref, Note, App, Space):
        try:
            return Class(atom)
        except TypeError:
            continue
    print(("ddd", type(atom), atom.tag, atom.attrs, atom.kids))
    raise TypeError


class ElementError(Exception):
    pass


def get_last_container(container):
    for term in container.terms:
        if isinstance(term, Container) or isinstance(term, Book):
            return get_last_container(term)
    return container


def get_parent_container(tree: Book or Container, level):
    if level == 1:
        assert isinstance(tree, Book)
        return tree
    else:
        for term in reversed(tree.terms):
            if isinstance(term, Container):
                if term.level == level - 1:
                    return term
                else:
                    return get_parent_container(term, level)
    raise Exception


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


def is_pts_ref(x):
    if isinstance(x, xl.Element):
        if x.tag == "ref":
            if "cRef" in x.attrs.keys():
                if re.match("^PTS", x.attrs["cRef"]):
                    if len(x.kids) == 0:
                        return True
    return False


def is_num_p(x):
    if isinstance(x, xl.Element):
        if x.tag == "p":
            if len(x.kids) == 1:
                if re.match(r"^[〇一二三四五六七八九十※～]+$", x.kids[0]):
                    return True
    return False


def is_milestone(x):
    if isinstance(x, xl.Element):
        if x.tag == "milestone":
            if x.attrs["unit"] == "juan":
                if "n" in x.attrs.keys():
                    if re.match(r"^\d+$", x.attrs["n"]):
                        return True
    return False


def _filter_kids(x, fun):
    new_e = xl.Element(tag=x.tag, attrs=x.attrs)
    for kid in x.kids:
        if fun(kid):
            continue
        if isinstance(kid, xl.Element):
            new_e.kids.append(_filter_kids(kid, fun))
        else:
            new_e.kids.append(kid)
    return new_e


def filter_kids(x: xl.Element or str, funs=None):
    funs = funs or [is_lb, is_pb, is_pts_ref, is_num_p, is_milestone]
    new_e = x
    for fun in funs:
        new_e = _filter_kids(new_e, fun)
    return new_e


def make_nikaya(nikaya, xmls):
    for one in xmls:
        filename = os.path.join(config.xmlp5_dir, one)
        file = open(filename, "r")
        mtime = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
        if nikaya.mtime:
            if nikaya.mtime < mtime:
                nikaya.mtime = mtime
        else:
            nikaya.mtime = mtime

        xmlstr = file.read()
        file.close()
        xml = xl.parse(xmlstr, do_strip=True)
        tei = xml.root
        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]

        body = filter_kids(body)
        delete_old_note(body)
        make_tree(nikaya, None, body.kids)


def make_tree(nikaya, container, xes):
    for xe in xes:
        if isinstance(xe, xl.Element):
            if xe.tag == "cb:div":
                make_tree(nikaya, container, xe.kids)

            elif xe.tag == "cb:mulu":
                new_container = Container()
                assert len(xe.kids) == 1
                new_container.mulu = xe.kids[0]
                new_container.level = int(xe.attrs["level"])
                parent_container = get_parent_container(nikaya, new_container.level)
                parent_container.terms.append(new_container)

                container = new_container

            elif xe.tag == "head":
                if not container.head:
                    container.head = Head(xe)
                else:
                    print(xe.kids)
                    raise Exception

            else:
                try:
                    container.terms.append(do_atom(xe))
                except AttributeError:
                    print(xe, xe.tag, xe.attrs, xe.kids)

        else:
            container.terms.append(do_atom(xe))


def delete_old_note(e: xl.Element):
    new_kids = []
    for kid in e.kids:
        if isinstance(kid, xl.Element):
            if kid.tag == "note" and "n" in kid.attrs.keys():
                if new_kids:
                    last = new_kids[-1]
                    if isinstance(last, xl.Element) and last.tag == "note" and "n" in last.attrs.keys():
                        if new_kids[-1].attrs["n"] == kid.attrs["n"]:
                            new_kids.pop()
            else:
                delete_old_note(kid)
        new_kids.append(kid)
    e.kids[:] = new_kids


def change_mulu(container, level, fun):
    for term in container.terms:
        if isinstance(term, Container):
            if term.level < level:
                change_mulu(term, level, fun)
            elif term.level == level:
                term.mulu = fun(term.mulu)
            else:
                raise Exception
        else:
            pass


def merge_terms(container):
    last_container = None
    new_terms = []

    for term in container.terms:
        if isinstance(term, Container):

            if last_container:
                if term.mulu == last_container.mulu:
                    last_container.terms.extend(term.terms)
                else:
                    new_terms.append(term)
                    last_container = term

            else:
                new_terms.append(term)
                last_container = term

        else:
            new_terms.append(term)

    for term in new_terms:
        if isinstance(term, Container):
            merge_terms(term)

    container.terms[:] = new_terms


class Artcle(object):
    def __init__(self, filename=None):

        if filename:
            self._filename = filename
            self._serial =
            xmlstr = open(filename).read()
            self._xml = xl.parse(xmlstr, do_strip=True)




    @property
    def body(self):
        for kid in self._xml.root.kids:
            if kid.tag == "body":
                return kid.kids

    @property
    def notes(self):
        for kid in self._xml.root.kids:
            if kid.tag == "ns":
                return kid.kids

    @property
    def ps(self):
        for kid in self._xml.root.kids:
            if kid.tag == "ps":
                return kid.kids

    def write(self, filename=None):
        #todo