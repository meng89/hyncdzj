#!/usr/bin/env python3
import io
import os
import tempfile


import opencc

import config

import epubpacker

import base

import xl

def trans_sc(s: str) -> str:
    c = opencc.OpenCC("t2s.json")
    return c.convert(s)


def load_book_from_dir(book_name):
    path = os.path.join(config.SIMPLE_DIR, book_name)
    book = base.Dir(path)
    return book

def load_sc_book_from_dir(book_name):
    src = os.path.join(config.SIMPLE_DIR, book_name)
    prefix = book_name + "_sc_"
    sc_dir = tempfile.TemporaryDirectory(prefix=prefix)
    book_name_sc = opencc.OpenCC("t2s.json").convert(book_name)
    dst = os.path.join(sc_dir.name, book_name_sc)
    os.makedirs(dst)
    cover_to_sc(src, dst)
    book = base.Dir(dst)
    return book


def cover_to_sc(src, dst):
    for file in os.listdir(src):
        path = os.path.join(src, file)

        sc_path = os.path.join(dst, trans_sc(path))

        if os.path.isfile(path) and file.lower().endswith(".xml"):
            f = open(path, "r")
            xml_str = f.read()
            f.close()
            f = open(sc_path, "w")
            f.write(trans_sc(xml_str))
            f.close()

        elif os.path.isdir(path):
            os.makedirs(sc_path)
            cover_to_sc(path, sc_path)


def write_pdf(book, book_name, module, lang):
    pass #todo


def write_tree_(d: base.Dir, level, f: io.TextIOWrapper, module):
    for name, obj in d.list:
        bookmark_name = name
        if hasattr(module, "pdf_bookmark_name"):
            bookmark_name = module.pdf_bookmark_name(name, obj, d)

        f.write("\\title{{}}{{}}".format(name, " "))



def write_epub(path, book, module, lang):
    epub = epubpacker.Epub()
    write_epub_tree(book, 0, epub, [], None, 0, module, lang)
    file_path = os.path.join(path, module.info[1])
    epub.write(file_path)


def write_epub_tree(d: base.Dir, level, epub, marks, parent_mark, doc_count, module, lang):
    for name, obj in d.list:
        bookmark_name = name
        if hasattr(module, "bookmark_name"):
            bookmark_name = module.bookmark_name(name, obj, d)
        toc = epubpacker.Mark(name)

        if isinstance(obj, base.Doc):
            html = trans_epub_page(obj, lang)
            doc_count += 1
            doc_path = str(doc_count) + ".xhtml"
            htmlstr = xl.Xml(root=html).to_str(do_pretty=True, dont_do_tags=["title", "p", "h1", "h2", "h3", "h4"])

            epub.userfiles[doc_path] = htmlstr
            epub.spine.append(doc_path)

        elif isinstance(obj, base.Dir):
            marks.append(toc)
            write_epub_tree(obj, level + 1, epub, marks, toc, doc_count, module, lang)


def trans_epub_page(obj: base.Doc, lang):
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

    notes = write_(obj.body, body, [])

    for index, note in notes:
        body.ekid("aside", {"epub:type": "footnote", "id": "n" + str(index + 1)})

    return html


def write_(obj, e, notes):
    for x in obj.kids:
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
                notes = write_(x, e, notes)
    return notes

# 短小的合并之类操作应该修改dir对象来完成


def main():
    # zh-Hans: 简体中文
    # zh-Hant: 传统中文
    td = tempfile.TemporaryDirectory(prefix="ncdzj_")
    import sn
    for m in (sn, ):

        book = load_book_from_dir(m.info.name)
        path = os.path.join(td.name, "元_{}_TC.epub".format(m.info.name))
        write_epub(path, book, m, "zh-Hant")

        path = path.replace(".epub", ".pdf")
        write_pdf(path, book, m, "zh-Hant")

        ################################################################################################################

        book = load_sc_book_from_dir(m.info.name)
        path = os.path.join(td.name, "元_{}_SC.epub".format(trans_sc(m.info.name)))
        write_epub(path, book, sn, "zh-Hans")

        path = path.replace(".epub", ".pdf")
        write_pdf(path, book, m, "zh-Hans")


if __name__ == '__main__':
    main()