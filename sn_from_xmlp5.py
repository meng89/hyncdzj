#!/usr/bin/env python3
import re

import base


xmls = [
    "N/N13/N13n0006.xml",
    "N/N14/N14n0006.xml",
    "N/N15/N15n0006.xml",
    "N/N16/N16n0006.xml",
    "N/N17/N17n0006.xml",
    "N/N18/N18n0006.xml"
]


class SN(base.Book):
    def __init__(self):
        super().__init__()
        self._abbr = "SN"
        self._name_hant = "相應部"
        self._name_pali = "Saṃyutta Nikāya"


def is_pin_sub(xy_cbdiv):
    pin_count = 0
    for div in xy_cbdiv.find_kids("cb:div"):
        mulu = div.find_kids("cb:mulu")[0]
        mulu_text = mulu.kids[0]
        m = re.match("^第[一二三四五六七八九十]+.*品.*$", mulu_text)
        if m:
            pin_count += 1

    if pin_count == 1 and len(xy_cbdiv.find_kids("cb:div")) == 1:
        return True
    if pin_count > 1:
        return True
    return False


_nikaya = None


def change_pian_mulu_fun(mulu: str):
    m = re.match(r"^(.+篇).* \(\d+-\d+\)$", mulu)
    if m:
        return m.group(1)
    else:
        return mulu


def change_xy_mulu_fun(mulu: str):
    m = re.match(r"^\S+　(\S+)$", mulu)
    if m:
        return m.group(1)
    else:
        return mulu


def change_pin_mulu_fun(mulu: str):
    # 第一　葦品
    # 一　遠離依止
    m = re.match("第?[一二三四五六七八九十]+　(.+)$", mulu)
    if m:
        return m.group(1)
    else:

        # 第一品
        # 異學廣說
        m = re.match(r"^(\S+)$", mulu)
        if m:
            return m.group(1)
        else:
            return mulu


def get_nikaya():
    global _nikaya
    if _nikaya:
        return _nikaya
    else:
        book = base.Book()
        base.load_from_xmlp5(book, xmls)

        base.change_dirname(snikaya, 1, change_pian_mulu_fun)
        base.change_dirname(snikaya, 2, change_xy_mulu_fun)

        base.change_dirname(snikaya, 3, change_pin_mulu_fun)
        base.change_dirname(snikaya, 4, change_pin_mulu_fun)
        base.change_dirname(snikaya, 5, change_pin_mulu_fun)

        base.merge_terms(snikaya)

        _nikaya = snikaya
        return snikaya


def is_sutta_parent(parent_container: base.Container):
    len_of_container = 0
    lot_of_match = 0
    for sub in parent_container.terms:
        if isinstance(sub, base.Container):
            len_of_container += 1

            if not isinstance(sub.mulu, str):
                input(sub.mulu)

            m = re.match(r"^〔[、～〇一二三四五六七八九十]+〕.*$", sub.mulu)
            if m:
                lot_of_match += 1

    if lot_of_match:
        if lot_of_match == len_of_container:
            return True
        else:
            print("需要检查子div:{}".format(parent_container.mulu, 1))
            print("len_of_container:", len_of_container)
            print("lot_of_match:", lot_of_match)
            input()
            return False
    else:
        return False


def print_title(container, depth):
    for term in container.terms:
        if isinstance(term, base.Container):
            if is_sutta_parent(container):
                print(" " * depth, "<Sutta>:", term.mulu, sep="")
            else:
                print(" " * depth, term.mulu, sep="")
            print_title(term, depth + 2)
        else:
            print(" " * depth, term, sep="")


def is_container_in_it(term):
    if isinstance(term, base.Container):
        for sub_term in term.terms:
            if isinstance(sub_term, base.Container):
                return True

        return False
    else:
        return False


def check_x_first_term(nikaya):
    for pian in nikaya.terms:
        term = pian.terms[0]
        print(pian.mulu)
        if not isinstance(term, base.Container):
            input("hehe")
            print(term._e.to_str())


def main():
    nikaya = get_nikaya()
    print_title(nikaya, 0)
    # check_x_first_term(nikaya)


if __name__ == "__main__":
    main()
