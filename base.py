#!/usr/bin/env python3
import sys

from check import last_type
from xl import Element

sys.path.append("/mnt/data/projects/xl")

import abc
import datetime
import re
import os
from uuid import uuid4
from typing import List

import epubpacker
import xl
import config

import p5a_to_simple


# SN/
# SN/_meta.xml
# SN/大篇/2 觉知相应/转轮品/SN 46.41
# SN/大篇/2 觉知相应/觉知总摄品/SN 46.51 食.xml

class Dir(dict):
    def __init__(self, path=None):
        super().__init__()
        self._xml = xl.Xml()

        if path is not None:
            xml_path = os.path.join(path, "_.xml")
            if os.path.exists(xml_path):
                self._xml = xl.parse(open(xml_path).read())
                root = self._xml.root
                assert isinstance(root, xl.Element)
                entries = root.find_kids("entries")
                for kid in entries.kids:
                    if kid.tag == "piece":
                        Piece()
                    elif kid.tag == "artcle":
                        key = os.path.splitext(kid.kids[0])[0]
                        self[key] = Artcle(os.path.join(path, kid.kids[0]))
                    elif kid.tag == "dir":
                        self[kid.kids[0]] = Dir(os.path.join(path, kid.kids[0]))
            else:
                self._xml = xl.Xml()
                root = xl.Element("dir")
                root.ekid("meta")
                root.ekid("entries")

                for entry in os.listdir(path):
                    entry_path = os.path.join(path, entry)
                    if os.path.isdir(entry_path):
                        self[entry] = Dir(entry_path)
                    elif os.path.isfile(entry_path) and entry.lower().endswith(".xml"):
                        key = os.path.splitext(entry)[0]
                        self[key] = Artcle(entry_path)

    def append_piece(self, piece):
        while True:
            key = uuid4()
            if key not in self.keys():
                break
        self[key] = piece

    def get_meta(self, key):
        meta = self._xml.root.find_kids("meta")[0]
        try:
            return meta.find_kids(key)[0].kids[0]
        except IndexError:
            return None

    def set_meta(self, key, value):
        meta = self._xml.root.find_kids("meta")[0]
        try:
            key_e = meta.find_kids(key)[0]
        except IndexError:
            key_e = meta.ekid(key)
        key_e.kids[:] = value

    def write(self, path):
        os.makedirs(path, exist_ok=True)
        has_piece = False
        enties = self._xml.root.find_kids("enties")[0]

        for k, v in self:
            if isinstance(v, Dir):
                v.write(os.path.join(path, k))
                enties.kids.append(Element("dir", kids=[k]))
            elif isinstance(v, Artcle):
                v.write(os.path.join(path, k))
                enties.kids.append(Element("artcle", kids=[k]))
            elif isinstance(v, Piece):
                enties.kids.append(Element("piece", kids=[v]))
                has_piece = True

        if not has_piece:
            enties.kids.clear()

        has_meta = bool(self._xml.root.find_kids("meta")[0].kids)
        if has_meta:
            open(os.path.join(path, "_.xml"), "w").write(self._xml.to_str())


class Book(Dir):

    @property
    def abbr(self):
        return self.get_meta("abbr")
    @abbr.setter
    def abbr(self, value):
        self.set_meta("abbr", value)

    @property
    def name_hant(self):
        return self.get_meta("name_hant")
    @name_hant.setter
    def name_hant(self, value):
        self.set_meta("name_hant", value)

    @property
    def name_pali(self):
        return self.get_meta("name_pali")
    @name_pali.setter
    def name_pali(self, value):
        self.set_meta("name_pali", value)


class Artcle:
    def __init__(self, path=None):
        if path:
            self._xml = xl.parse(open(path).read())
        else:
            self._xml = xl.Xml(root=xl.Element("root"))
            self._xml.root.kids.append(xl.Element("body"))
            self._xml.root.kids.append(xl.Element("notes"))
            self._xml.root.kids.append(xl.Element("ps"))

    @property
    def body(self) -> xl.Element:
        return self._xml.root.find_kids("body")[0]

    @property
    def notes(self) -> xl.Element:
        return self._xml.root.find_kids("notes")[0]

    @property
    def ps(self) -> xl.Element:
        return self._xml.root.find_kids("ps")[0]

    def append_note_from_text(self, string: str) -> int:
        index = len(self.notes.kids) + 1
        note = xl.Element("note", attrs={"n": str(index)})
        note.kids.append(string)
        self.notes.kids.append(note)
        return index

    def get_note_text_by_index(self, index: int) -> str:
        for note in self.notes.kids:
            note: xl.Element
            if int(note.attrs["n"]) == index:
                return note.kids[0]

    def get_next_note_index(self) -> int:
        return len(self.notes.kids) + 1


    def write(self, path):
        open(path, "w").write(self._xml.to_str())


class Piece(Artcle):
    def __init__(self, element:xl.Element=None):
        super().__init__()
        if element:
            self._xml = xl.Xml(root=element)

    def get_element(self):
        return self._xml.root

    def write(self, *args, **kwargs):
        raise AttributeError # 禁用父类write属性，防止误用


########################################################################################################################

def dir_to_book():
    pass

def book_to_dir():
    pass

def book_to_pdf():
    pass

def book_to_epub():
    pass


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


# <cb:mulu type="其他" level="1">有偈篇 (1-11)</cb:mulu><head>
def does_it_have_sub_mulu(elements: xl.Element) -> bool:
    level = get_level(elements)
    for kid in elements.kids[2:]:
        if isinstance(kid, xl.Element) and kid.tag == "cb:div":
            if get_level(kid) > level:
                return True
            else:
                return False
    return False


def has_sub_mulu(e: xl.Element, next_index: int, level) -> bool or None:
    for x in e.kids[next_index: ]:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            match has_sub_mulu(x, 0, level):
                case True:
                    return True
                case False:
                    return False
                case None:
                    pass

        elif isinstance(x, xl.Element) and x.tag == "cb:mulu":
            x_level = int(x.attrs["level"])
            if level < x_level:
                return True
            else:
                return False

    return None


# get level, mulu, head
def get_lmh(cb_div: xl.Element) -> tuple:
    kid1 = cb_div.kids[0]
    kid2 = cb_div.kids[1]
    if not (isinstance(kid1, xl.Element) and kid1.tag == "cb:mulu" and len(kid1.kids) == 1 and isinstance(kid1.kids[0],
                                                                                                          str)):
        raise Exception

    assert isinstance(kid2, xl.Element) and kid2.tag == "head"

    return int(kid1.attrs["level"]), kid1.kids[0], kid2.kids[:],


def get_level(cb_div: xl.Element) -> int: return get_lmh(cb_div)[0]


def get_mulu(cb_div: xl.Element) -> str: return get_lmh(cb_div)[1]


def get_head(cb_div: xl.Element) -> str: return get_lmh(cb_div)[2]

########################################################################################################################

def find_parent_dir(book, level):
    return find_parent_dir2(book, 0, level)

def find_parent_dir2(dir_like: Dir | Artcle, dir_like_level: int, level: int):
    if isinstance(dir_like, Dir):
        if dir_like_level + 1 == level:
            return dir_like
        else:
            keys = list(dir_like.keys())
            if len(keys) > 0:
                last_item = dir_like[keys[-1]]
                return find_parent_dir2(last_item, dir_like_level + 1, level)
            else:
                raise Exception
    else:
        raise Exception

########################################################################################################################

def find_last_entry(entry: Book or Artcle or Piece or Dir):
    keys = list(entry.keys())
    if isinstance(entry, dict) and keys:
        return find_last_entry(entry[keys[-1]])
    else:
        return entry

########################################################################################################################

def set_entry(book, key, entry, level):
    set_entry2(book, 0, key, entry, level)

def set_entry2(dire: dict, dire_level, key, entry: Dir or Artcle or Piece, level):
    if dire_level + 1 == level:
        if isinstance(dire, Artcle):
            print(dire.body.to_str())

        assert key not in dire.keys()

        dire[key] = entry

    else:
        keys = list(dire.keys())
        set_entry2(dire[keys[-1]], dire_level + 1, key, entry, level)

########################################################################################################################

def make_tree(book, e: xl.Element):
    my_has_new_entry = False
    current_entry = None

    current_dir = None
    current_piece = None
    current_artcle = None

    for index, term in enumerate(e.kids):
        if isinstance(term, xl.Element) and term.tag == "cb:mulu":
            assert len(term.kids) == 1
            level = int(term.attrs["level"])
            mulu_str = term.kids[0]

            # 检查用途
            parent_dir = find_parent_dir(book, level)

            if has_sub_mulu(e, index + 1, level) is True:
                current_dir = Dir()
                _entry = current_dir
            else:
                current_artcle = Artcle()
                _entry = current_artcle

            set_entry(book, mulu_str, _entry, level)
            my_has_new_entry = True

        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            has_new_entry = make_tree(book, term)
            if has_new_entry is True:
                current_artcle = None
                current_piece = None

        else:
            if current_piece is None and current_artcle is None:
                _piece = Piece()
                current_dir.append_piece(_piece)
                current_piece = _piece

            _piece_like = current_artcle or current_piece

            new_note_index = _piece_like.get_next_note_index()

            new_elements, new_notes, new_note_index = p5a_to_simple.trans_element(term, new_note_index)
            _piece_like.body.kids.extend(new_elements)
            _piece_like.notes.kids.extend(new_notes)

    return my_has_new_entry


def get_last_parent_dir(dir_, level):
    if level == 1:
        return dir_
    elif level > 1:
        sub_dir = list(dir_.values())[-1]
        return get_last_parent_dir(sub_dir, level - 1)


def change_dirname(dir_, fun):
    change_dirname2([], dir_, fun)


def change_dirname2(path, dir_, fun):
    new_dir = {}
    for k, v in dir_.items():
        new_k = fun(path.append(k))
        if isinstance(v, dict):
            new_v = change_dirname2(path.append(new_k), v, fun)
        else:
            new_v = v
        new_dir[new_k] = new_v

    return new_dir


def filter_(term: xl.Element or str):
    if isinstance(term, str):
        return term

    e = term
    new_e = xl.Element(tag=e.tag)
    new_e.attrs.update(e.attrs)
    for kid in e.kids:
        # if isinstance(kid, xl.Element):
        #    print("debug:", kid.to_str())

        if isinstance(kid, xl.Element) and kid.tag in ("lb", "pb", "milestone"):
            pass

        elif isinstance(kid, xl.Element) and kid.tag == "p" \
                and len(kid.kids) == 1 and isinstance(kid.kids[0], str) and re.match(r"^[〇一二三四五六七八九十※～]+$",
                                                                                     kid.kids[0]):
            pass

        elif isinstance(kid, str) and kid in ("\n", "\n\r"):
            pass

        elif isinstance(kid, xl.Comment):
            pass

        else:
            new_e.kids.append(filter_(kid))

    return new_e


def all_xmls(dir_=config.xmlp5a_dir):
    xmls = []
    for one in os.listdir(dir_, ):
        path = os.path.join(dir_, one)
        if os.path.isfile(path) and one.lower().endswith(".xml"):
            xmls.append(path)
        elif os.path.isdir(path):
            xmls.extend(all_xmls(path))

    return sorted(xmls)


def n_xmls():
    xmls = []
    for x in all_xmls():
        if "/N/" in x:
            xmls.append(x)
    return xmls


def main():
    pass


if __name__ == "__main__":
    pass
