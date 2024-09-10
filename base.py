#!/usr/bin/env python3
import sys

from check import last_type
from xl import Element

sys.path.append("/mnt/data/projects/xl")

import abc
import datetime
import re
import os
from typing import List

import epubpacker
import xl
import config

import xmlp5a_to_simple_xml


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
    @abbr.setattr
    def abbr(self, value):
        self.set_meta("abbr", value)

    @property
    def name_hant(self):
        return self.get_meta("name_hant")
    @name_hant.setattr
    def abbr(self, value):
        self.set_meta("name_hant", value)

    @property
    def name_pali(self):
        return self.get_meta("name_pali")
    @name_pali.setattr
    def abbr(self, value):
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
        self.notes.kids.append(note)
        return index

    def get_note_text_by_index(self, index: int) -> str:
        for note  in self.notes.kids:
            note: xl.Element
            if int(note.attrs["n"]) == index:
                return note.kids[0]


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


def xmlp5a_to_book(xmls):
    book = Book()
    for one in xmls:
        filename = os.path.join(config.xmlp5a_dir, one)
        file = open(filename, "r")

        xmlstr = file.read()
        file.close()
        xml = xl.parse(xmlstr)
        tei = xml.root
        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]

        body = filter_(body)
        for cb_div in body.find_kids("cb:div"):
            make_tree(book, cb_div)

    return book


def book_to_simple_xml(book: Book):
    pass


# <cb:mulu type="其他" level="1">有偈篇 (1-11)</cb:mulu><head>
def does_it_have_sub_mulu(cb_div: xl.Element) -> bool:
    level = get_level(cb_div)
    for kid in cb_div.kids[2:]:
        if isinstance(kid, xl.Element) and kid.tag == "cb:div":
            if get_level(kid) > level:
                return True
            else:
                return False
    return False


def has_sub_mulu(elements: list, level: int) -> bool:
    return bool(has_sub_mulu_(elements, level))

def has_sub_mulu_(elements, level) -> bool or None:
    for x in elements:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            match has_sub_mulu_(x.kids, level):
                case True:
                   return True
                case False:
                    return False
                case None:
                    pass

        elif isinstance(x, xl.Element) and x.tag == "cb:mulu":
            x_level = int(x.attrs["level"])
            if level > x_level:
                return True
            else:
                return False
        else:
            pass
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

def find_entry_from_last_branch(book, level):
    return find_entry_from_last_branch2(book, 0, level)

def find_entry_from_last_branch2(directory: dict, directory_level: int, level: int):
    if directory_level == level:
        return directory
    else:
        last_item = directory[list(directory.keys())[-1]]
        return find_entry_from_last_branch2(last_item, directory_level + 1, level)

########################################################################################################################

def find_last_entry(book):
    return find_last_entry2(book)

def find_last_entry2(directory):
    if isinstance(directory, dict):
        keys = list(directory.keys())
        return find_last_entry2(directory[keys[-1]])
    else:
        return directory

########################################################################################################################

def set_entry(book, level, key, entry):
    set_entry2(book, 1, level, key, entry)

def set_entry2(dire: dict, dire_level, key, entry: Dir or Artcle or Piece, level):
    if dire_level == level:
        dire[key] = entry

    else:
        keys = list(dire.keys())
        set_entry2(dire[keys[-1]], dire_level + 1, key, entry, level)

########################################################################################################################


def make_tree(book, cb_div: xl.Element):
    level = get_level(cb_div)
    mulu = get_mulu(cb_div)
    head = get_head(cb_div)

    dire = find_entry_from_last_branch(book, level)
    if dire is None:
        if does_it_have_sub_mulu(cb_div) is True:
            dire = {}
        else:
            dire = Artcle()
        set_entry(book, 1, mulu, dire, level)

    note_index = 1
    notes = []
    for kid in cb_div.kids[2:]:
        if isinstance(kid, xl.Element) and kid.tag == "cb:div":
            make_tree(book, kid)

        else:
            # 如果不是底层, 这些片段属于目录
            if does_it_have_sub_mulu(cb_div) is True:

                print("debug")
                print(type(kid))
            else:
                new_elements, new_notes, note_index = xmlp5a_to_simple_xml.trans_element(kid, note_index)
                notes.extend(new_notes)
                dire.body.kids.extend(new_elements)
                dire.notes.kids.extend(notes)


def make_tree2(book, elements):
    for term in elements:
        if isinstance(term, xl.Element) and term.tag == "cb:mulu":
            assert len(term.kids) == 1
            level = int(term.attrs["level"])
            mulu_str = term.kids[0]

            entry = find_entry_from_last_branch(book, level)

            if entry is None:
                if has_sub_mulu(elements, level) is True:
                    new_entry = Dir()
                else:
                    new_entry = Artcle()

                set_entry(book, level, mulu_str, new_entry)

            else:
                raise Exception

        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            make_tree2(book, term.kids)

        else:
            entry = find_last_entry(book)
            if not isinstance(entry, (Artcle, Piece)):
                raise Exception

            entry.attach(term)


def feed(book, mulu_element: xl.Element):
    level = int(mulu_element.attrs["level"])


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
