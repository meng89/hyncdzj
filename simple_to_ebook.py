#!/usr/bin/env python3
import io
import os
import tempfile


import opencc


import base
import config


def load_from_dir(book_name):
    path = os.path.join(config.SIMPLE_DIR, book_name)
    book = base.Dir(path)
    return book

def load_from_dir_sc(book_name):
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
        c = opencc.OpenCC("t2s.json")
        sc_path = os.path.join(dst, c.convert(path))

        if os.path.isfile(path) and file.lower().endswith(".xml"):
            f = open(path, "r")
            xml_str = f.read()
            f.close()
            f = open(sc_path, "w")
            f.write(c.convert(xml_str))
            f.close()

        elif os.path.isdir(path):
            os.makedirs(sc_path)
            cover_to_sc(path, sc_path)



def write2pdf(book, book_name, module):
    write_tree(book, 1, f, module)


def write_tree(d: base.Dir, level, f:io.TextIOWrapper, module):

    for name, obj in d.list:
        bookmark_name = name
        if hasattr(module, "pdf_bookmark_name"):
            bookmark_name = module.pdf_bookmark_name(name, obj, d)

        f.write("\\title{{}}{{}}".format(name, " "))



def write2epub(book, module):
    pass

