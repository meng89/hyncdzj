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


def dir2entries(path):
    entries = {}

    have_sub_dir = False
    for entry in os.listdir():
        if os.path.isdir(os.path.join(path, entry)):
            have_sub_dir = True
            break

    have_num_prefix = True
    for entry in os.listdir():
        if not re.match(r"^\d+_", entry):
            have_num_prefix = False
            break


    for entry in sorted(os.listdir()):

        if have_num_prefix:
            m = re.match(r"^\d+_(.*)$", entry)
            no_prefix_entry = m.group(1)
        else:
            no_prefix_entry = entry

        entry_path = os.path.join(path, entry)

        if os.path.isdir(entry_path):
            entries[no_prefix_entry] = dir2entries(entry_path)

        elif os.path.isfile(entry_path):
            if entry.lower().endswith(".xml"):

                entries[no_prefix_entry] = Artcle(entry_path)

    return entries



class Book(object):
    def __init__(self, path=None):
        if path:
            xmlstr = open(os.path.join(path, "sn.xml")).read()
            self._xml = xl.parse(xmlstr, do_strip=True)
            self._entries = dir2entries(os.path.join(path, "entries"))
        else:
            self._xml = None
            self._entries = []

    @property
    def abbr(self):
        return self._xml.root.find_kids("abbr")[0]

    @property
    def name_hant(self):
        return self._xml.root.find_kids("name_hant")[0]

    @property
    def name_pali(self):
        return self._xml.root.find_kids("name_pali")[0]

    @property
    def entries(self):
        return self._entries

    def write(self, path):
        os.makedirs(path, exist_ok=True)

        filename = "x"
        path = os.path.join(path, filename)
        xmlstr = self._xml.to_str()
        f = open(path, "w")
        f.write(xmlstr)
        f.close()

        os.makedirs(os.path.join(path, "entries"), exist_ok=True)
        for entry in self._entries:
            entry.write(os.path.join(path, "entries"))


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


def load_from_xmlp5(book, xmls):
    for one in xmls:
        filename = os.path.join(config.xmlp5_dir, one)
        file = open(filename, "r")

        xmlstr = file.read()
        file.close()
        xml = xl.parse(xmlstr, do_strip=True)
        tei = xml.root
        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]

        body = filter_kids(body)
        delete_old_note(body)
        make_tree(book, None, body.kids)


def is_have_sub_mulu(xes):
    for i in range(len(xes)):
        xe = xes[i]
        if isinstance(xe, xl.Element):
            if xe.tag == "cb:div":
                if is_have_sub_mulu(xes[i + 1:]):
                    return True
                else:
                    pass
            elif xe.tag == "cb:mulu":
                return True
    return False


# not every cb:mulu include in cb:div, like: pN14p0006a0301
def make_tree(book, dir_, xes):
    for i in range(len(xes)):
        xe = xes[i]
        if isinstance(xe, xl.Element):

            if xe.tag == "cb:div":
                make_tree(book, dir_, xe.kids)

            elif xe.tag == "cb:mulu":
                assert len(xe.kids) == 1
                mulu_name = xe.kids[0]

                if is_have_sub_mulu(xes[i + 1:]) is True:
                    new_dir = {}

                    level = int(xe.attrs["level"])
                    parent_dir = get_last_parent_dir(book.entries, level)

                    if mulu_name in parent_dir.keys():
                        raise Exception(mulu_name)

                    parent_dir[mulu_name] = new_dir
                    dir_ = new_dir

                else:
                    if mulu_name in dir_.keys():
                        raise Exception(mulu_name)
                    artcle = Artcle()
                    dir_[mulu_name] = artcle

            elif xe.tag == "head":
                pass

            else:
                last_entry = list(dir_.values())[-1]
                assert isinstance(last_entry, Artcle)
                last_entry.body.append(do_atom(xe))

        else:
            print(xe)
            raise Exception
            # container.terms.append(do_atom(xe))


def get_last_parent_dir(dir_, level):
    if level == 1:
        return dir_
    elif level > 1:
        sub_dir = list(dir_.values())[-1]
        return get_last_parent_dir(sub_dir, level - 1)


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


def change_dirname(container, level, fun):
    for term in container.terms:
        if isinstance(term, container):
            if term.level < level:
                change_dirname(term, level, fun)
            elif term.level == level:
                term.mulu = fun(term.mulu)
            else:
                raise Exception
        else:
            pass


class _Artcle(object):
    def _make_new_xml(self):
        self._xml = xl.Xml()
        self._xml.root.kids.append(xl.Element("body"))
        self._xml.root.kids.append(xl.Element("notes"))
        self._xml.root.kids.append(xl.Element("ps"))

    @property
    def body(self):
        return self._xml.root.find_kids("body")[0]

    @property
    def notes(self):
        return self._xml.root.find_kids("notes")[0]

    @property
    def ps(self):
        return self._xml.root.find_kids("ps")[0]

    @abc.abstractmethod
    def _get_filename(self):
        pass

    def write(self, parentpath):
        filename = self._get_filename()
        path = os.path.join(parentpath, filename)
        xmlstr = self._xml.to_str()
        f = open(path, "w")
        f.write(xmlstr)
        f.close()


class Artcle(_Artcle):
    def __init__(self, filepath=None, no_num_prefix_path=None, book_abbr=None, serial=None, title=None):
        super().__init__()

        if filepath:
            filename = os.path.splitext(os.path.split(no_num_prefix_path)[1])[0]
            m = re.match(r"^([a-z]+) (\d(?:\.\d)*) (.*)$", filename)
            if m:
                self._is_piece = False

                serial = tuple([int(s) for s in m.group(2).split(".")])
                self._book_abbr = m.group(1)
                self._serial = serial
                self._title = m.group(3)

                xmlstr = open(filepath).read()
                self._xml = xl.parse(xmlstr, do_strip=True)

                #非SN 1.1 这样的经文，可能是礼敬偈子，或串联
            else:
                self._is_piece = True

                xmlstr = open(filepath).read()
                self._xml = xl.parse(xmlstr, do_strip=True)
        else:
            self._book_abbr = book_abbr
            self._serial = serial
            self._title = title
            self._make_new_xml()

    def _get_filename(self):
        filename = " ".join([self._book_abbr,
                             ".".join([str(x) for x in self._serial]),
                             self._title]
                            ) + ".xml"
        return filename


class Piece(_Artcle):
    def __init__(self, filepath=None, serial=None):
        super().__init__()
        if filepath:
            filename = os.path.splitext(os.path.split(filepath)[1])[0]
            m = re.match(r"^(\d+)$", filename)
            if m:
                self._serial = m.group(1)
                xmlstr = open(filepath).read()
                self._xml = xl.parse(xmlstr, do_strip=True)
            else:
                raise Exception("无法解析文件名")
        else:
            self._serial = serial
            self._make_new_xml()

    def _get_filename(self):
        return self._serial
