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


def trans_sc(s: str) -> str:
    c = opencc.OpenCC("t2s.json")
    return c.convert(s)


def load_book_from_dir(m):
    book = load_from_p5a.load_book_by_module(m)
    return book

def load_sc_book_from_dir(m):
    src = os.path.join(config.SIMPLE_DIR, m.info.name)
    prefix = m.info.name + "_sc_"
    sc_dir = tempfile.TemporaryDirectory(prefix=prefix)
    book_name_sc = opencc.OpenCC("t2s.json").convert(m.info.name)
    dst = os.path.join(sc_dir.name, book_name_sc)
    os.makedirs(dst)
    cover_to_sc(src, dst)
    book = base.Dir(dst)
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


def write_pdf(book, book_name, module, lang):
    pass #todo


def write_tree_(d: base.Dir, level, f: io.TextIOWrapper, module):
    for name, obj in d.list:
        bookmark_name = name
        if hasattr(module, "pdf_bookmark_name"):
            bookmark_name = module.pdf_bookmark_name(name, obj, d)

        f.write("\\title{{}}{{}}".format(name, " "))


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

    write_epub_tree(book, epub, [], epub.mark, 0, module, lang)
    epub.write(path)


def write_epub_tree(d: base.Dir, epub, no_href_marks, parent_mark, doc_count, module, lang):
    for name, obj in d.list:
        mark = epubpacker.Mark(name)
        parent_mark.kids.append(mark)



        if isinstance(obj, base.Doc):
            html = create_page(obj, lang)
            doc_count += 1
            doc_path = str(doc_count) + ".xhtml"
            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p", "h1", "h2", "h3", "h4"])

            epub.userfiles[doc_path] = htmlstr
            epub.spine.append(doc_path)
            mark.href = doc_path
            for _mark in no_href_marks:
                _mark.href = doc_path
            no_href_marks = []

        elif isinstance(obj, base.Dir):
            no_href_marks.append(mark)
            doc_count, no_href_marks = write_epub_tree(obj, epub, no_href_marks, mark, doc_count, module, lang)

    return doc_count, no_href_marks


def create_page(obj: base.Doc, lang):
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
    body = html.ekid("body")

    notes = write_(obj.body, body)

    for index, note in enumerate(notes):
        body.ekid("aside", {"epub:type": "footnote", "id": "n" + str(index + 1)})

    return html


def write_(obj_body, e):
    notes = []
    for x in obj_body.kids:
        if isinstance(x, str):
            e.kids.append(x)
        elif isinstance(x, xl.Element):
            if x.tag == "ewn":
                notes.append(x.kids[1])
                count = str(len(notes))
                a = e.ekid("a", {"epub:type": "noteref", "href" : "#n" + count})
                a.kids.extend(x.kids[0].kids)
                if not a.kids:
                    a.attrs["class"] = "notext"
                    a.kids.append(count)
            else:
                notes.extend(write_(x, e))
    return notes

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
    for m in (sn, sv):

        book = load_book_from_dir(m)
        if hasattr(m, "change2"):
            book = m.change2(book)

        path = os.path.join(td.name, "元_{}_TC.epub".format(m.info.name))
        write_epub(path, book, m, "zh-Hant")
        check_epub(path)

        path = path.replace(".epub", ".pdf")
        write_pdf(path, book, m, "zh-Hant")

        ################################################################################################################

        book = load_sc_book_from_dir(m)
        path = os.path.join(td.name, "元_{}_SC.epub".format(trans_sc(m.info.name)))
        write_epub(path, book, sn, "zh-Hans")

        path = path.replace(".epub", ".pdf")
        write_pdf(path, book, m, "zh-Hans")

    input("Any key to exit:")


if __name__ == '__main__':
    main()
