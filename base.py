#!/usr/bin/env python3
import copy
import sys
import dataclasses
from operator import index

sys.path.append("/mnt/data/projects/xl")

import re
import os

import xl
import config

def piece_key():
    from uuid import uuid4
    return str(uuid4())


dont_do_tags = ["dir", "h1", "s", "p"]

# SN/
# SN/_meta.xml
# SN/大篇/2 觉知相应/转轮品/SN 46.41
# SN/大篇/2 觉知相应/觉知总摄品/SN 46.51 食.xml


class Metadata:
    def __init__(self, term=None):
        if isinstance(term, str):
            xml = xl.parse(term)
            self._meta = xml.root
        elif isinstance(term, xl.Element):
            self._meta = term
        else:
            self._meta = xl.Element("meta")

    def __bool__(self):
        return bool(self._meta.kids)

    def get_element(self):
        return self._meta

    def to_str(self, *args, **kwargs):
        return self._meta.to_str(*args, **kwargs)


def match(name):
    m = re.match(r"^(\d+(?:\.\d+)?) (.*)$", name)
    return m

def filter_fun(name):
    if match(name):
        return True

def split_name(name):
    return match(name).group(2)

def split_xml_name(name):
    return match(name).group(2).removesuffix(".xml")

def split_float(name):
    return float(match(name).group(1))


class Dir:
    def __init__(self, path=None):
        self.list = []
        if path:
            entries = list(filter(filter_fun, os.listdir(path)))
            entries.sort(key=split_float)

            for entry in entries:
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    key = split_name(entry)
                    value = Dir(entry_path)
                elif os.path.isfile(entry_path) and entry.lower().endswith(".xml"):
                    key = split_name(entry)[:-4]
                    value = Doc(entry_path)
                else:
                    continue

                self.list.append((key, value))


    def append_piece_term(self, term):
        no_name_doc = None
        for k, v in self.list:
            if k == "" and isinstance(v, Doc):
                no_name_doc = v

        if not no_name_doc:
            no_name_doc = Doc()

        no_name_doc.append_term(term)
        self.list.append(("", no_name_doc))


    def write(self, path):
        os.makedirs(path, exist_ok=True)

        for index, (k, v) in enumerate(self.list):
            if isinstance(v, Dir):
                v.write(os.path.join(path, "{} {}".format(index + 1, k)))

            elif isinstance(v, Doc):
                v.write(os.path.join(path, "{} {}.xml".format(index + 1, k)))


doc_dont_do_tags = ["p", "s", "note", "h1"]
class Doc:
    def __init__(self, path=None):
        if path:
            self._xml = xl.parse(open(path).read())
            meta_e = self._xml.root.find_kids("meta")[0]
        else:
            self._xml = xl.Xml(root=xl.Element("doc"))
            meta_e = self._xml.root.ekid("meta")
            self._xml.root.kids.append(xl.Element("body"))
            self._xml.root.kids.append(xl.Element("notes"))
            self._xml.root.kids.append(xl.Element("ps"))

        self._meta = Metadata(meta_e)

    @property
    def body(self) -> xl.Element:
        return self._xml.root.find_kids("body")[0]

    @property
    def notes(self) -> xl.Element:
        return self._xml.root.find_kids("notes")[0]

    @property
    def ps(self) -> xl.Element:
        return self._xml.root.find_kids("ps")[0]

    def append_term(self, term):
        self.body.kids.append(term)

    def _get_simple_xml(self):
        new_xml = copy.copy(self._xml)
        root = new_xml.root
        body = root.find_kids("body")[0]
        new_body, notes = trans_ewn_to_simple(body)
        body.kids[:] = new_body.kids
        index = root.kids.index(body)
        root.kids.pop(index)
        root.kids.insert(index, new_body)
        root.kids.append(notes)
        return new_xml


    def write(self, path):
        simple_xml = self._get_simple_xml()
        open(path, "w").write(simple_xml.to_str(do_pretty=True, dont_do_tags=doc_dont_do_tags))

# 原始转Python Object
def trans_ewn_to_simple(body:xl.Element) -> tuple:
    new_body, notes_kids, _ = trans_ewn_to_simple2(body, 1)
    notes = xl.Element("notes", kids=notes_kids)

    return new_body, notes

def trans_ewn_to_simple2(e:xl.Element, note_index:int) -> tuple:
    if isinstance(e, xl.Element) and e.tag == "ewn":
        a = xl.Element("a")
        a.attrs["n"] = str(note_index)
        a.kids.extend(e.kids[0].kids)

        note = xl.Element("note")
        note.attrs["n"] = str(note_index)
        note.kids.extend(e.kids[1].kids)

        note_index += 1
        return a, [note], note_index

    elif isinstance(e, xl.Element):
        notes = []
        new_e = xl.Element(e.tag, e.attrs)
        for kid in e.kids:
            new_kid, new_notes, note_index = trans_ewn_to_simple2(kid, note_index)
            new_e.kids.append(new_kid)
            notes.extend(new_notes)

        return new_e, notes, note_index

    else:
        return e, [], note_index


def hit_note(notes, num):
    for note in notes:
        if note.attrs["n"] == num:
            new_note = xl.Element("note")
            new_note.kids.extend(note.kids)
            return new_note
    raise Exception

def trans_simple_to_ewn(body, notes):
    [new_body] = trans_simple_to_ewn2(body, notes)
    return new_body

def trans_simple_to_ewn2(e, notes):
    if isinstance(e, xl.Element) and e.tag == "a" and "n" in e.attrs.keys():
        num = e.attrs["n"]

        ewn = xl.Element("ewn")
        a = ewn.ekid("a")
        a.attrs["n"] = num

        note = hit_note(notes, num)
        ewn.kids.append(note)

        return [ewn]

    elif isinstance(e, xl.Element):
        new_e = xl.Element(e.tag, e.attrs)
        for kid in e.kids:
            new_kids = trans_simple_to_ewn2(kid, notes)
            new_e.kids.extend(new_kids)
        return [new_e]
    else:
        return [e]

class Piece(Doc):
    def __init__(self, element:xl.Element=None):
        super().__init__()
        self._xml.root.tag = "piece"
        if element:
            self._xml = xl.Xml(root=element)

    def get_element(self):
        return self._xml.root

    def write(self, *args, **kwargs):
        raise AttributeError # 禁用父类write属性，防止误用


########################################################################################################################

@dataclasses.dataclass
class Info:
    serial: int
    name: str
    authors: tuple[str, ...]
    abbr: str


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


def print_tree(d: Dir, ident=0):
    for name, obj in d.list:
        print("{}{}".format(" " * ident, name))
