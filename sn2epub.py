import epubpacker

import public


import sn


def write_suttas(nikaya, epub: epubpacker.Epub, bns, xc, _test=False):

def write_suttas(sn_obj, epub: epubpacker.Epub):
    pass


def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub = public.create_epub(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
