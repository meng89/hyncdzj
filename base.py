#!/usr/bin/env python3
import copy
import sys
import dataclasses


import re
import os

import opencc


sys.path.append("/mnt/data/projects/xl")
import xl
import config


def to_sc(s):
    return opencc.OpenCC("t2s.json").convert(s)


def piece_key():
    from uuid import uuid4
    return str(uuid4())


dont_do_tags = ["dir", "h1", "s", "p"]

# SN/
# SN/_meta.xml
# SN/大篇/2 觉知相应/转轮品/SN 46.41
# SN/大篇/2 觉知相应/觉知总摄品/SN 46.51 食.xml


class Meta:
    def __init__(self, e):
        self._e = e


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

    def trans_2_sc(self):
        new_d = Dir()
        for name, obj in self.list:
            new_name = to_sc(name)
            new_obj = obj.trans_2_sc()
            new_d.list.append((new_name, new_obj))
        return new_d

    def append_piece_term(self, term):
        no_name_doc = None
        for k, v in self.list:
            if k == "" and isinstance(v, Doc):
                no_name_doc = v

        if not no_name_doc:
            no_name_doc = Doc()

        no_name_doc.append_term(term)
        self.list.append(("", no_name_doc))

    def write_for_machine(self, path):
        self._write("machine", path)

    def write_for_human(self, path):
        self._write("human", path)

    def _write(self, fun_name, path):
        os.makedirs(path, exist_ok=True)

        for index, (k, v) in enumerate(self.list):
            if fun_name == "machine":
                fun = v.write_for_machine
            elif fun_name == "human":
                fun = v.write_for_human
            else:
                raise Exception

            if isinstance(v, Dir):
                fun(os.path.join(path, "{} {}".format(index + 1, k)))
            elif isinstance(v, Doc):
                fun(os.path.join(path, "{} {}.xml".format(index + 1, k)))


_doc_dont_do_tags = ["p", "s", "note", "h1"]

def cover_element(old_e: xl.Element, cover_fun):
    new_e = xl.Element(cover_fun(old_e.tag))
    for key, value in old_e.attrs.items():
        new_e.attrs[cover_fun(key)] = cover_fun(value)

    for kid in old_e.kids:
        if isinstance(kid, xl.Element):
            new_kid = cover_element(kid, cover_fun)
        else:
            new_kid = cover_fun(kid)
        new_e.kids.append(new_kid)
    return new_e


class Doc:
    def __init__(self, path=None, xml=None):
        if path:
            _xml = xl.parse(open(path).read())
            doc = _xml.root
            match doc.attrs["type"]:
                case "for_human":
                    self._xml = human_to_machine(_xml)
                case "for_machine":
                    self._xml = _xml
                case _:
                    raise Exception

        elif xml:
            self._xml = xml

        else:
            root = xl.Element("doc")
            root.attrs["type"] = "for_machine"
            self._xml = xl.Xml(root=root)
            body = root.ekid("body")
            body.self_closing = False
            ps = root.ekid("ps")
            ps.self_closing = False

    def trans_2_sc(self):
        new_root = cover_element(self._xml.root, to_sc)
        new_xml = xl.Xml(root = new_root)
        return Doc(xml=new_xml)

    @property
    def body(self) -> xl.Element:
        return self._xml.root.find_kids("body")[0]

    def append_term(self, term):
        self.body.kids.append(term)

    def write_for_machine(self, path):
        open(path, "w").write(self._xml.to_str(do_pretty=True, dont_do_tags=_doc_dont_do_tags))


    def write_for_human(self, path):
        simple_xml = copy.copy(self._xml)
        root = simple_xml.root
        body = root.find_kids("body")[0]
        new_body, notes = _split_note(body)
        body.kids[:] = new_body.kids
        index = root.kids.index(body)
        root.kids.pop(index)
        root.kids.insert(index, new_body)
        root.kids.append(notes)
        open(path, "w").write(simple_xml.to_str(do_pretty=True, dont_do_tags=_doc_dont_do_tags))


# 原始转Python Object
def _split_note(body:xl.Element) -> tuple:
    new_body, notes_kids, _ = _split_note2(body, 1)
    notes = xl.Element("notes", kids=notes_kids)

    return new_body, notes

def _split_note2(e:xl.Element, note_index:int) -> tuple:
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
            new_kid, new_notes, note_index = _split_note2(kid, note_index)
            new_e.kids.append(new_kid)
            notes.extend(new_notes)

        return new_e, notes, note_index

    else:
        return e, [], note_index


def human_to_machine(xml):
    _doc = xml.root
    body = _doc.find_kids("body")[0]
    notes = _doc.find_kids("notes")[0]
    ps = _doc.find_kids("ps")[0]

    new_body = _merge_note(body, notes)

    new_root = xl.Element("doc")
    new_xml = xl.Xml(new_root)
    new_root.kids.append(new_body)
    new_root.kids.append(ps)

    return new_xml


def _merge_note(e: xl.Element, notes):
    new_e = xl.Element(e.tag, attrs=e.attrs)
    for term in e.kids:
        if isinstance(term, xl.Element):
            if term.tag == "a" and "n" in term.attrs.keys():
                ewn = xl.Element("ewn")
                a = ewn.ekid("a")
                a.kids.extend(term.kids)

                note = _hit_note(notes, term.attrs["n"])
                ewn.kids.append(note)
            else:
                new_e.kids.append(_merge_note(term, notes))

        if isinstance(term, str):
            new_e.kids.append(term)
    return new_e

def _hit_note(notes, num):
    for note in notes:
        if note.attrs["n"] == num:
            new_note = xl.Element("note")
            new_note.kids.extend(note.kids)
            return new_note
    raise Exception


########################################################################################################################

@dataclasses.dataclass
class Info:
    serial: int or None
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



