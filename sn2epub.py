import epubpacker

import epub_public


import sn


def write_suttas(nikaya, epub: epubpacker.Epub, bns, xc, _test=False):
    for pian in nikaya.terms:




def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub_public.make(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
