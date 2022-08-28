import epubpacker

import epub_public


import sn


class TermsType:
    pin = "pin"
    sutta = "sutta"


def pin_or_sutta(terms):
    pin_count = 0
    sutta_count = 0
    for term in terms:
        if isinstance(term, sn.Container):
            if term.mulu[-1] == "品":
                pin_count += 1
            elif term.mulu[-1] == ""




def write_suttas(nikaya, epub: epubpacker.Epub, bns, xc, _test=False):
    for pian in nikaya.terms:
        for xy in pian.terms:
            match pin_or_sutta(xy.terms):
                case TermsType.pin:
                    pass
                case TermsType.sutta:
                    pass







def make(xc, temprootdir, books_dir, epubcheck):
    snikaya = sn.get_tree()
    epub_public.make(snikaya, write_suttas, xc, temprootdir, books_dir, epubcheck)
