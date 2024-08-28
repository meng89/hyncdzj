#!/usr/bin/env python3
import sys

sys.path.append("/mnt/data/projects/xl")

import abc
import datetime
import re
import os
from typing import List

import epubpacker
import xl
import config

import xmlp5a_to_simplexml


# SN/
# SN/_meta.xml
# SN/大篇/2 觉知相应/转轮品/SN 46.41
# SN/大篇/2 觉知相应/觉知总摄品/SN 46.51 食.xml

class _Dir(dict):
    def __init__(self, path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path is not None:
            xml_path = os.path.join(path, "_.xml")

        self._e = xl.Xml()

    def head(self):
        pass

    def tail(self):
        pass

    def notes(self):
        pass

    def write(self, path):
        pass


class Book(dict):

    @staticmethod
    def dir2entries(path: str):
        entries = {}

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
                entries[no_prefix_entry] = __class__.dir2entries(entry_path)

            elif os.path.isfile(entry_path):
                if entry.lower().endswith(".xml"):
                    entries[no_prefix_entry] = Artcle(entry_path)

            return entries

    def __init__(self, path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path:
            xmlstr = open(os.path.join(path, "_meta.xml")).read()
            self._xml = xl.parse(xmlstr)
            self.update(__class__.dir2entries(os.path.join(path, "entries")))
        else:
            self._xml = xl.Xml()

    @property
    def abbr(self):
        return self._xml.root.find_kids("abbr")[0]

    @property
    def name_hant(self):
        return self._xml.root.find_kids("name_hant")[0]

    @property
    def name_pali(self):
        return self._xml.root.find_kids("name_pali")[0]


    def write(self, path):
        os.makedirs(path, exist_ok=True)

        filename = "x"
        path = os.path.join(path, filename)
        xmlstr = self._xml.to_str()
        f = open(path, "w")
        f.write(xmlstr)
        f.close()

        os.makedirs(os.path.join(path, "entries"), exist_ok=True)

        for k, v in self.items():
            if isinstance(v, dict):
                pass # todo
            else:
                entry.write(os.path.join(path, "entries"))


class _Artcle(object):
    def _make_new_xml(self):
        self._xml = xl.Xml(root=xl.Element("root"))
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
                self._xml = xl.parse(xmlstr)

                # 非SN 1.1 这样的经文，可能是礼敬偈子，或助记词
            else:
                self._is_piece = True

                xmlstr = open(filepath).read()
                self._xml = xl.parse(xmlstr)
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
                self._xml = xl.parse(xmlstr)
            else:
                raise Exception("无法解析文件名")
        else:
            self._serial = serial
            self._make_new_xml()

    def _get_filename(self):
        return self._serial


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


def does_it_have_sub_mulu2(elements: list, term: xl.Element) -> bool:
    level = int(term.attrs["level"])
    for x in elements:
        if x == term:
            pass
        # todo


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


def find_node(data: dict, data_level, key, level):
    keys = list(data.keys())
    if data_level == level:
        if key in keys:
            if key == keys[-1]:
                input("重复的key: {}, 回车继续运行".format(repr(key)))
                return data[key]
            else:
                raise Exception("非切割同级目录出现")
        else:
            return None
    else:
        sub = data[keys[-1]],
        if isinstance(sub, dict):
            return find_node(sub, level, key, data_level + 1)
        else:
            return None


def make_node(data: dict, data_level, key, node: Artcle or dict, level):
    if data_level == level:
        data[key] = node
    else:
        keys = list(data.keys())
        make_node(data[keys[-1]], data_level + 1, key, node, level)


def make_tree(book, cb_div: xl.Element):
    level = get_level(cb_div)
    mulu = get_mulu(cb_div)
    head = get_head(cb_div)

    node = find_node(book.entries, 1, mulu, level)
    if node is None:
        if does_it_have_sub_mulu(cb_div) is True:
            node = {}
        else:
            node = Artcle()
        make_node(book.entries, 1, mulu, node, level)

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
                new_elements, new_notes, note_index = xmlp5a_to_simplexml.trans_element(kid, note_index)
                notes.extend(new_notes)
                node.body.kids.extend(new_elements)
                node.notes.kids.extend(notes)


def make_tree2(book, elements):
    for term in elements:
        if isinstance(term, xl.Element) and term.tag == "cb:mulu":
            assert len(term.kids) == 1
            level = int(term.attrs["level"]),
            mulu_str = term.kids[0]

            node = find_node(book.entries, 1, mulu_str, level)
            if node is None:
                if does_it_have_sub_mulu2(elements, term) is True:
                    node = {}
                else:
                    node = Artcle()
                make_node(book.entries, 1, mulu, node, level)

        elif isinstance(term, xl.Element) and term.tag == "cb:div":
            make_tree2(book, term.kids)

        else:
            node = get_node()
            attach(node, x)


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
