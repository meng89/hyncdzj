#!/usr/bin/env python3
import copy
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

import p5a_to_simple


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
    return re.match(r"^(\d+.?\d*) *(\S*)$", name)


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
        super().__init__()

        # 空 Dir
        if path is None:
            self._metadata = Metadata()
            self.list = []
        else:
            xml_path = os.path.join(path, "_.xml")
            # 载入非空 Dir, 目录中有 _.xml 文件
            if xml_path:
                self._metadata = Metadata(open(xml_path).read())
            # 目录中没有 _.xml
            else:
                self._metadata = Metadata()

            self.list = []

            entries = list(filter(filter_fun, os.listdir(path)))
            entries.sort(key=split_float)

            for entry in entries:
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    key = split_name(entry)
                    value = Dir(entry_path)
                elif os.path.isfile(entry_path) and entry.lower().endswith(".xml"):
                    key = os.path.splitext(split_name(entry))[0]
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
        if self._metadata:
            filepath = os.path.join(path, "_.xml")
            open(filepath, "w").write(self._metadata.to_str())

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


def find_parent_dir(dir_, level):
    return find_parent_dir2(dir_, 0, level)

def find_parent_dir2(dir_: Dir, dir_level, level):
    if dir_level + 1 == level:
        return dir_
    last_dir = None
    for (k, v) in dir_.list:
        if isinstance(v, Dir):
            last_dir = v
    if last_dir is None:
        raise Exception
    find_parent_dir2(last_dir, dir_level + 1, level)


########################################################################################################################

def find_last_entry(entry: Dir or Doc):
    keys = list(entry.keys())
    if isinstance(entry, dict) and keys:
        return find_last_entry(entry[keys[-1]])
    else:
        return entry

########################################################################################################################

def set_entry(book, key, entry, level):
    set_entry2(book, 0, key, entry, level)

def set_entry2(dire: Dir, dire_level, key, entry: Dir or Doc, level):
    if dire_level + 1 == level:
        if isinstance(dire, Doc):
            print(dire.body.to_str())

        if key in dire.keys():
            print("same key: ", repr(key))

        dire[key] = entry

    else:
        keys = list(dire.keys())
        set_entry2(dire[keys[-1]], dire_level + 1, key, entry, level)

########################################################################################################################

def make_tree(book, div):
    terms_list = []
    terms = []

    my_type = None

    level = None
    mulu_str = None

    head = None

    passed_mulu = False

    for index, term in enumerate(div.kids):
        if isinstance(term, xl.Element) and term.tag == "cb:mulu":
            assert len(term.kids) == 1
            level = int(term.attrs["level"])
            mulu_str = term.kids[0]

            if has_sub_mulu(term, index + 1, level) is True:
                current = Dir()
            else:
                current = Doc()

            parent_dir = find_parent_dir(book, level)
            parent_dir.list.append( (mulu_str, current) )
            passed_mulu = True

        elif isinstance(term, xl.Element) and term.tag == "head":
            if passed_mulu is False:
                parent_dir = find_last_dir(book)

            if has_sub_mulu(term, index + 1, level) is True:
                current = Dir()
            else:
                current = Doc()

            parent_dir = 


        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            make_tree(book, term)

        else:
            x = mulu_str or head
            if mulu_str is None:
                if head is None:
                    my_type = "dir"




def make_tree(book, e: xl.Element):
    my_has_new_entry = False

    current_dir = None
    current_doc = None

    parent_dir = None



    level = None
    mulu_str = None
    parent_dir = find_parent_dir(book, level)



    if e.tag == "body":
        current_dir = book

    for index, term in enumerate(e.kids):
        if isinstance(term, xl.Element) and term.tag == "cb:mulu":
            assert len(term.kids) == 1
            level = int(term.attrs["level"])
            mulu_str = term.kids[0]
            parent_dir = find_parent_dir(book, level)

            if has_sub_mulu(e, index + 1, level) is True:
                current_dir = Dir()
                _entry = current_dir
            else:
                current_doc = Doc()
                _entry = current_doc

            parent_dir.list.append((mulu_str, _entry))
            # set_entry(book, mulu_str, _entry, level)
            my_has_new_entry = True

        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            has_new_entry = make_tree(book, term)

            if has_new_entry is True:
                current_doc = None

        else:
            if current_doc is None:
                _piece = Piece()
                try:
                    current_dir.append_piece(_piece)
                except AttributeError:
                    print(term.to_str())
                    print(e.to_str())
                    exit()
                current_piece = _piece

            _piece_like = current_doc

            _piece_like.body.kids.append(term)

    return my_has_new_entry


def make_tree_(book, e: xl.Element):
    my_has_new_entry = False

    current_dir = None
    current_piece = None
    current_doc = None

    if e.tag == "body":
        current_dir = book

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
                current_doc = Doc()
                _entry = current_doc

            set_entry(book, mulu_str, _entry, level)
            my_has_new_entry = True

        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            has_new_entry = make_tree(book, term)
            if has_new_entry is True:
                current_doc = None
                current_piece = None

        else:
            if current_piece is None and current_doc is None:
                _piece = Piece()
                try:
                    current_dir.append_piece(_piece)
                except AttributeError:
                    print(term.to_str())
                    print(e.to_str())
                    exit()
                current_piece = _piece

            _piece_like = current_doc or current_piece

            _piece_like.body.kids.append(term)

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

        elif isinstance(kid, str):
            new_e.kids.append(kid.strip())

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
