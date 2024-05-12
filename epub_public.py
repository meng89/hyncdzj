import os
import datetime
import posixpath
import shutil
import subprocess
import string
import uuid
from urllib.parse import urlsplit

import cn2an
import xl
import epubpacker

import base
import book_public
import config

import notice
import css
import js
import xu



def relpath(path1, path2):
    """
     ("note/note0.xhtml", "sn/sn01.xhtml") -> "../note/note0.xhtml"
     ("sn/sn21.xhtml#SN.21.1, "sn/sn21.xhtml") -> "#SN.21.1"
    """

    path1_2 = posixpath.normpath(urlsplit(path1).path)
    fragment = urlsplit(path1).fragment

    path2_2 = posixpath.normpath(path2)

    if path1_2 == path2_2:
        if not fragment:
            raise ValueError("How to link to self without a tag id?")
        else:
            return "#" + fragment
    else:
        return posixpath.relpath(path1_2, posixpath.dirname(path2_2)) + (("#" + fragment) if fragment else "")


def get_uuid(s):
    return uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meng89/hyncdzj_ebook" + " " + s)


def make(nikaya, write_fun, xc: book_public.XC, temprootdir, books_dir, epubcheck):
    bn = nikaya.abbr.lower()
    mytemprootdir = os.path.join(temprootdir, "{}_epub_{}".format(bn, xc.enlang))
    os.makedirs(mytemprootdir, exist_ok=True)

    ebook = create_ebook(nikaya, xc)
    bns = [nikaya.abbr]

    write_cover(ebook, nikaya, xc)
    # fanli.write_fanli(ebook, xc)
    # homage.write_homage(ebook, xc, book.homage_line)

    xu.write_xu(ebook, xc)
    note_collection: base.NoteCollection = write_fun(nikaya=nikaya, ebook=ebook, xc=xc)

    note_collection.write2ebook(ebook, xc)

    notice.write_notice(ebook, xc)

    mytemprootdir, epub_path = write2file(epub=ebook, mytemprootdir=mytemprootdir, bn=bn)

    check_result = False
    if is_java_exist() and os.path.exists(epubcheck):
        check_result = check_epub(epub_path=epub_path, epubcheck=epubcheck, mytemprootdir=mytemprootdir)

    if is_java_exist() and os.path.exists(epubcheck) and check_result:
        copy2booksdir(epub_path=epub_path, nikaya=nikaya, xc=xc, books_dir=books_dir)




def is_java_exist():
    from shutil import which
    return which("java") is not None


def check_epub(epub_path, epubcheck, mytemprootdir):
    compile_cmd = "java -jar {} {} -q".format(epubcheck, epub_path)

    stdout_file = open(os.path.join(mytemprootdir, "cmd_stdout"), "w")
    stderr_file = open(os.path.join(mytemprootdir, "cmd_stderr"), "w")

    check_result = False

    def _run():
        nonlocal check_result
        print("执行检查", repr(compile_cmd), end=" ", flush=True)
        p = subprocess.Popen(compile_cmd, cwd=mytemprootdir, shell=True,
                             stdout=stdout_file, stderr=stderr_file)
        p.communicate()
        if p.returncode != 0:
            check_result = False
        else:
            check_result = True
    _run()
    if check_result:
        print("✔")
    else:
        print("✘")
    return check_result


def copy2booksdir(epub_path, nikaya, xc, books_dir):
    shutil.copy(epub_path,
                os.path.join(books_dir, "{}_{}_{}{}_{}.epub".format(xc.c(nikaya.name_hant),
                                                                    xc.zhlang,
                                                                    "元亨寺",
                                                                    nikaya.mtime.strftime("%y%m"),
                                                                    datetime.datetime.now().strftime("%Y%m%d"))))


def write2file(epub, mytemprootdir, bn):
    epub_path = os.path.join(mytemprootdir, "{}.epub".format(bn))
    epub.write(epub_path)
    return mytemprootdir, epub_path


def create_ebook(nikaya: base.Book, xc: book_public.XC):
    epub = epubpacker.Epub()

    epub.meta.titles = [xc.c(nikaya.name_hant)]
    epub.meta.creators = ["元亨寺"]
    epub.meta.date = nikaya.mtime.strftime("%Y-%m-%dT%H:%M:%SZ")
    epub.meta.languages = [xc.xmlang, "pi", "en-US"]

    my_uuid = get_uuid(xc.c(nikaya.name_hant) + xc.enlang)
    epub.meta.identifier = my_uuid.urn

    epub.meta.others.append(xl.Element("meta", {"property": "belongs-to-collection", "id": "c01"},
                                       [xc.c("漢譯南傳大藏經")]))
    epub.meta.others.append(xl.Element("meta", {"refines": "#c01", "property": "collection-type"}, ["series"]))

    epub.userfiles[css.css1_path] = css.css1[xc.enlang]
    # epub.userfiles[css.css2_path] = css.css2[xc.enlang]
    # epub.userfiles[js.js1_path] = js.js1
    epub.userfiles["_css/user_css1.css"] = "/* 第一个自定义 CSS 文件 */\n\n"
    epub.userfiles["_css/user_css2.css"] = "/* 第二个自定义 CSS 文件 */\n\n"
    epub.userfiles["_js/user_js1.js"] = "// 第一个自定义 JS 文件\n\n"
    epub.userfiles["_js/user_js2.js"] = "// 第二个自定义 JS 文件\n\n"

    return epub


def _make_note_doc(title, xc: book_public.XC, doc_path):
    html, body = make_doc(doc_path, xc, title)
    body.attrs["class"] = "note"
    sec = xl.sub(body, "section", {"epub:type": "endnotes", "role": "doc-endnotes"})
    ol = xl.sub(sec, "ol")
    return html, ol


def _doc_str(e):
    return xl.Xml(root=e).to_str(do_pretty=True, dont_do_tags=["p"])


def _make_css_link(head, href, id_=None):
    link = xl.sub(head, "link", {"rel": "stylesheet", "type": "text/css", "href": href})
    if id_:
        link.attrs["id"] = id_
    return link


def _make_js_link(head, src, id_=None):
    script = xl.sub(head, "script", {"type": "text/javascript", "src": src})
    if id_:
        script.attrs["id"] = id_
    return script


def make_doc(doc_path, xc, title=None):
    html = xl.Element("html", {"xmlns:epub": "http://www.idpf.org/2007/ops",
                               "xmlns": "http://www.w3.org/1999/xhtml",
                               "xml:lang": xc.xmlang,
                               "lang": xc.xmlang})
    head = xl.sub(html, "head")

    if title:
        _title = xl.sub(head, "title", kids=[title])

    _make_css_link(head, relpath(css.css1_path, doc_path), "css1")
    _make_css_link(head, relpath("_css/user_css1.css", doc_path), "user_css1")
    _make_css_link(head, relpath("_css/user_css2.css", doc_path), "user_css2")
    _make_js_link(head, relpath(js.js1_path, doc_path), "js1")
    _make_js_link(head, relpath("_js/user_js1.js", doc_path), "user_js1")
    _make_js_link(head, relpath("_js/user_js2.js", doc_path), "user_js2")

    body = xl.sub(html, "body")
    return html, body


def write_cover(ebook, nikaya: base.Book, xc: book_public.XC):

    cover_img_filename = "{}_{}_cover.png".format(nikaya.abbr, xc.enlang)
    cover_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover_images")
    cover_img_path = os.path.join(cover_dir, cover_img_filename)

    if not os.path.exists(cover_img_path):
        _template_str = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover.xhtml")).read()
        if isinstance(xc, book_public.SC):
            template_str = _template_str.replace("CJK TC", "CJK SC")
        else:
            template_str = _template_str
        t = string.Template(template_str)

        if len(nikaya.name_hant) == 2:
            name_hant = nikaya.name_hant[0] + "&nbsp;&nbsp;" + nikaya.name_hant[1]
        else:
            name_hant = nikaya.name_hant
        doc_str = \
            t.substitute(bookname_han=xc.c(name_hant),
                         bookname_pi=nikaya.name_pali,
                         han_version=xc.han_version,
                         translator="元亨寺",
                         date=nikaya.mtime.strftime("%Y年%m月")
                         )
        from html2image import Html2Image as HtI
        hti = HtI(browser_executable="google-chrome-stable", output_path=cover_dir)
        hti.screenshot(html_str=doc_str, size=(1600, 2560), save_as=cover_img_filename)
    assert os.path.exists(cover_img_path)

    cover_img_path_in_ebook = posixpath.join(nikaya.abbr, cover_img_filename)
    ebook.userfiles[cover_img_path_in_ebook] = open(cover_img_path, "rb").read()
    ebook.cover_img_path = cover_img_path_in_ebook

    cover_doc_path = nikaya.abbr + "/cover.xhtml"
    html, body = make_doc(cover_doc_path, xc, "封面")
    body.attrs["style"] = "text-align: center;"

    _img = xl.sub(body, "img", {"src": relpath(cover_img_path_in_ebook, cover_doc_path),
                                "alt": "Cover Image",
                                "title": "Cover Image"})
    htmlstr = xl.Xml(root=html).to_str()
    ebook.userfiles[cover_doc_path] = htmlstr
    ebook.root_toc.append(epubpacker.Toc("封面", cover_doc_path))
    ebook.spine.append(cover_doc_path)


class TermNotFoundError(Exception):
    pass


def get_html_id(container, term, prefix=None):
    prefix = prefix or "id"
    serial = 0
    for _term in container.terms:
        serial += 1

        current_prefix = "{}-{}".format(prefix, serial)

        if _term is term:
            return current_prefix

        if isinstance(_term, base.Container):
            try:
                return get_html_id(_term, term, current_prefix)
            except TermNotFoundError:
                pass

    raise TermNotFoundError()


def transform_digit(han_digit: str):
    return cn2an.cn2an(han_digit, "smart")
