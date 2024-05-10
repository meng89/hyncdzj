import os
import datetime
import re


import xl


import base
import config


_nikaya = None


xmls = [
    "N/N09/N09n0005.xml",
    "N/N10/N10n0005.xml",
    "N/N11/N11n0005.xml",
    "N/N12/N12n0005.xml",
]


class MNikaya(base.Book):
    def __init__(self):
        super().__init__()
        self._abbr = "MN"
        self._name_hant = "中部"
        self._name_pali = "Majjhima Nikāya"


def change_pian_mulu_fun(mulu: str):
    m = re.match(r"^\S+　(\S+)[上下]$", mulu)
    return m.group(1)


def change_pin_mulu_fun(mulu: str):
    m = re.match(r"^\S+　(.+?)[上下]?$", mulu)
    return m.group(1).replace("　", "")


def get_nikaya():
    global _nikaya
    if _nikaya:
        return _nikaya

    mnikaya = MNikaya()
    base.load_from_xmls(mnikaya, xmls)

    base.change_dirname(mnikaya, 1, change_pian_mulu_fun)
    base.change_dirname(mnikaya, 2, change_pin_mulu_fun)

    base.merge_terms(mnikaya)

    _nikaya = mnikaya
    return mnikaya


def print_title(container, depth):
    for term in container.terms:
        if isinstance(term, base.Container):
            print(" " * depth, term.mulu, sep="")
            print_title(term, depth + 4)


if __name__ == '__main__':
    print_title(get_nikaya(), 0)
