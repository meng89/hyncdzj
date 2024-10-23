#!/usr/bin/env python3
import io
import os
import tempfile
import subprocess
import uuid
import datetime
import re

import opencc

import config

import epubpacker

import base

import xl
import load_from_p5a
from load_from_p5a import note_fun


def trans_sc(s: str) -> str:
    c = opencc.OpenCC("t2s.json")
    return c.convert(s)


def load_book_from_dir(m):
    book = load_from_p5a.load_book_by_module(m)
    return book


def cover_to_sc(src, dst):
    for file in os.listdir(src):
        path = os.path.join(src, file)
        dst_path = os.path.join(dst, trans_sc(file))

        if os.path.isfile(path) and file.lower().endswith(".xml"):
            f = open(path, "r")
            xml_str = f.read()
            f.close()
            f = open(dst_path, "w")
            f.write(trans_sc(xml_str))
            f.close()

        elif os.path.isdir(path):
            os.makedirs(dst_path)
            cover_to_sc(path, dst_path)


def create_identifier(s):
    return uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meng89/ncdzj" + s)


def write_epub(path, book, module, lang):
    epub = epubpacker.Epub()
    identifier_string = "元亨寺南傳大藏經" + module.info.name + lang
    title = "南傳大藏經·" + module.info.name
    if lang == "zh-Hans":
        identifier_string = trans_sc(identifier_string)
        title = trans_sc(title)

    epub.meta.identifier = identifier_string
    epub.meta.titles = [title]
    epub.meta.creators = module.info.authors
    epub.meta.languages.append(lang)
    epub.meta.date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%SZ")

    epub_notes = EpubNotes()
    write_epub_tree(book, epub_notes, epub, [], epub.mark, 0, module, lang)
    for name, xml_str in epub_notes.pages(lang):
        epub.userfiles[name] = xml_str
        epub.spine.append(name)
    epub.write(path)


def create_page(lang, title):
    html = xl.Element(
        "html",
        {
            "xmlns:epub": "http://www.idpf.org/2007/ops",
            "xmlns": "http://www.w3.org/1999/xhtml",
            "xml:lang": lang,
            "lang": lang
        }
    )
    head = html.ekid("head")
    head.ekid("title", kids=[title or "-"])
    html.ekid("body")
    return html


def write_epub_tree(d: base.Dir, epub_notes, epub, no_href_marks, parent_mark, doc_count, module, lang):
    for name, obj in d.list:
        mark = epubpacker.Mark(name)
        parent_mark.kids.append(mark)

        if isinstance(obj, base.Doc):
            html = write_doc(name, obj, lang, epub_notes, parent_mark)
            doc_count += 1
            doc_path = str(doc_count) + ".xhtml"
            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p", "h1", "h2", "h3", "h4", "a", "sen", "aside"])

            epub.userfiles[doc_path] = htmlstr
            epub.spine.append(doc_path)
            mark.href = doc_path
            for _mark in no_href_marks:
                _mark.href = doc_path
            no_href_marks = []

        elif isinstance(obj, base.Dir):
            no_href_marks.append(mark)
            doc_count, no_href_marks = write_epub_tree(obj, epub_notes, epub, no_href_marks, mark, doc_count, module, lang)

    return doc_count, no_href_marks


def write_doc(name, doc: base.Doc, lang, epub_notes, parent_mark):
    html = create_page(lang, name)
    body = html.find_kids("body")[0]
    epub_es, note_count = trans_machine_to_epub_es(doc.body.kids, epub_notes, 0)
    for epub_e in epub_es:

        body.kids.append(epub_e)
    return html


def make_mark_from_es(es, index):
    while index != len(es):
        if isinstance(e, xl.Element):




def trans_machine_to_epub_es(es, epub_notes, note_count):
    note_count = note_count
    new_es = []
    for e in es:
        _es, note_count = trans_machine_to_epub_e(e, epub_notes, note_count)
        new_es.extend(_es)
    return new_es, note_count

def trans_machine_to_epub_e(e, epub_notes, note_count):
    for fun in [fun_ewn, fun_j, fun_list, fun_everything]:
        result = fun(e, epub_notes, note_count)
        if result is not None:
            return result
        else:
            continue

    raise Exception


def fun_ewn(e: xl.Element, epub_notes, note_count):
    if not isinstance(e, xl.Element) or e.tag != "ewn":
        return None

    href = epub_notes.add_note(e.kids[1].kids)
    note_count += 1
    a = e.ekid("a", {"epub:type": "noteref", "href" : href})
    a.kids.extend(e.kids[0].kids)
    if not a.kids:
        a.attrs["class"] = "notext"
        a.kids.append(str(note_count))
    return [a], note_count


def fun_j(e: xl.Element, epub_notes, note_count):
    if not isinstance(e, xl.Element) or e.tag != "j":
        return None

    div_j = xl.Element("div", {"class": "ji"})
    for term in e.kids:
        if term.tag == "p":
            div_j.ekid("div", {"class": "person"}, kids=term.kids)
        elif term.tag == "s":
            div_s = div_j.ekid("div", {"class": "sentence"})
            es, note_count = trans_machine_to_epub_es(term.kids, epub_notes, note_count)
            div_s.kids.extend(es)
    return [div_j], note_count

def fun_list(e: xl.Element, epub_notes, note_count):
    if not isinstance(e, xl.Element) or e.tag != "list":
        return None

    div_list = xl.Element("div", {"class": "list"})
    for term in e.kids:
        assert term.tag == "item"
        div_item = div_list.ekid("div", {"class": "item"})
        es, note_count = trans_machine_to_epub_es(term.kids, epub_notes, note_count)
        div_item.kids.extend(es)
    return [div_list], note_count



def fun_everything(e, epub_notes, note_count):
    note_count = note_count
    if isinstance(e, xl.Element):
        new_e = xl.Element(e.tag, e.attrs)
        new_es, note_count = trans_machine_to_epub_es(e.kids, epub_notes, note_count)
        new_e.kids.extend(new_es)
        return [new_e], note_count
    else:
        return [e], note_count


class EpubNotes:
    def __init__(self):
        self._pages = []

    def add_note(self, es):
        match len(self._pages):
            case 0:
                page = []
                self._pages.append(page)
            case _:
                page = self._pages[-1]

        if len(page) == 100:
            page = []
            self._pages.append(page)

        page_index = self._pages.index(page)
        page.append(es)
        note_index = page.index(es)

        return "note_page{}.xhtml#note{}".format(page_index + 1, note_index + 1)

    def pages(self, lang):
        _pages = []
        for page_index, page in enumerate(self._pages):
            _page_html = create_page(lang, "Note {}".format(page_index + 1))
            _body = _page_html.find_kids("body")[0]
            _section = _body.ekid("section", {"epub:type": "endnotes", "role": "doc-endnotes"})
            ol = _section.ekid("ol")
            for note_index, note_es in enumerate(page):
                li = ol.ekid("li", {"id": "note{}".format(note_index + 1)})
                p = li.ekid("p")
                p.kids.extend(note_es)
            _pages.append(
                (
                    "note_page{}.xhtml".format(page_index + 1),
                    _page_html.to_str(do_pretty=True, dont_do_tags=["title", "link", "script", "p"])
                    )
            )
        return _pages


# 短小的合并之类操作应该修改dir对象来完成

def check_epub(epub_path):
    stdout_file = open("{}_{}".format(epub_path, "stdout"), "w")
    stderr_file = open("{}_{}".format(epub_path, "stderr"), "w")

    def _run():
        nonlocal check_result
        compile_cmd = "java -jar {} {} -q".format(config.EPUBCHECK, epub_path)
        cwd = os.path.split(epub_path)[0]
        # print("运行:", compile_cmd, end=" ", flush=True)
        print("检查", os.path.split(epub_path)[1], ": ", end="", flush=True)
        p = subprocess.Popen(compile_cmd, cwd=cwd, shell=True, stdout=stdout_file, stderr=stderr_file)
        p.communicate()
        if p.returncode != 0:
            return False
        else:
            return True

    check_result = _run()
    if check_result:
        print("Passed")
    else:
        print("Failed")
    return check_result


def main():
    # zh-Hans: 简体中文
    # zh-Hant: 传统中文
    td = tempfile.TemporaryDirectory(prefix="ncdzj_")
    import sn, sv
    for m in (sv, sn):

        book = load_book_from_dir(m)
        if hasattr(m, "change2"):
            book = m.change2(book)

        path = os.path.join(td.name, "元_{}_TC.epub".format(m.info.name))
        write_epub(path, book, m, "zh-Hant")
        check_epub(path)

        path = path.replace(".epub", ".pdf")
        #write_pdf(path, book, m, "zh-Hant")

        ################################################################################################################

        book = book.trans_2_sc()
        path = os.path.join(td.name, "元_{}_SC.epub".format(trans_sc(m.info.name)))
        write_epub(path, book, m, "zh-Hans")
        check_epub(path)

        path = path.replace(".epub", ".pdf")
        #write_pdf(path, book, m, "zh-Hans")

    input("Any key to exit:")


if __name__ == '__main__':
    main()
