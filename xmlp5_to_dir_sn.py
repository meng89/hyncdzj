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


def change_artcle_name(k):
    m = re.match(r"〔(.*)〕", k)


def change_name_add_range(dir_):
    new_dir = {}
    # pian
    for k, v in dir_.items():
        # xiangying
        new_v = {}
        for k2, v2 in v.items():
            # pin or something else
            if isinstance(v2, dict):
                new_v2 = change_name_add_range2(v2)
            else:
                new_v2 = v2

            new_v[k2] = new_v2

        new_dir[k] = new_v

    return new_dir


def change_name_add_range2(dir_):
    new_dir = {}
    for k, v in dir_.items():
        new_k = change_name_add_range3(k, v)
        new_v = change_name_add_range2(v)
        new_dir[new_k] = new_v
    return new_dir


def change_name_add_range3(k, v):
    if re.match(r"^\d+\.", k):
        return k, v
    else:
        begin, end = get_begin(v), get_end(v)
        return k + "(" + begin + "-" + end + ")", v


def get_begin(dir_):
    k = list(dir_.keys())[0]
    v = dir_[k]
    if isinstance(v, dict):
        return get_begin(v)
    else:
        _, seril, _ = unpack_artilc_name(k)
        return seril.split(".")[-1]


def get_end(dir_):
    k = list(dir_.keys())[-1]
    v = dir_[k]
    if isinstance(v, dict):
        return get_end(v)
    else:
        _, seril, _ = unpack_artilc_name(k)
        return seril.split(".")[-1]


def unpack_artilc_name(name):
    m = re.match(r"^([a-z]+) (\d+(?:\.\d+)?) ?(.*)$", name)
    if m:
        return m.group(1), m.group(2), m.group(2), m.group(3), m.group(4)
    else:
        raise Exception




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

    book = base.load_from_xmlp5(xmls)

    base.change_dirname(book, 1, change_pian_mulu_fun)
    base.change_dirname(book, 2, change_xy_mulu_fun)

    base.change_dirname(book, 3, change_pin_mulu_fun)
    base.change_dirname(book, 4, change_pin_mulu_fun)
    base.change_dirname(book, 5, change_pin_mulu_fun)

    return book


# def is_sutta_parent(parent_container: base.Container):
#     len_of_container = 0
#     lot_of_match = 0
#     for sub in parent_container.terms:
#         if isinstance(sub, base.Container):
#             len_of_container += 1
#
#             if not isinstance(sub.mulu, str):
#                 input(sub.mulu)
#
#             m = re.match(r"^〔[、～〇一二三四五六七八九十]+〕.*$", sub.mulu)
#             if m:
#                 lot_of_match += 1
#
#     if lot_of_match:
#         if lot_of_match == len_of_container:
#             return True
#         else:
#             print("需要检查子div:{}".format(parent_container.mulu, 1))
#             print("len_of_container:", len_of_container)
#             print("lot_of_match:", lot_of_match)
#             input()
#             return False
#     else:
#         return False
#
#
# def print_title(container, depth):
#     for term in container.terms:
#         if isinstance(term, base.Container):
#             if is_sutta_parent(container):
#                 print(" " * depth, "<Sutta>:", term.mulu, sep="")
#             else:
#                 print(" " * depth, term.mulu, sep="")
#             print_title(term, depth + 2)
#         else:
#             print(" " * depth, term, sep="")
#
#
# def is_container_in_it(term):
#     if isinstance(term, base.Container):
#         for sub_term in term.terms:
#             if isinstance(sub_term, base.Container):
#                 return True
#
#         return False
#     else:
#         return False
#
#
# def check_x_first_term(nikaya):
#     for pian in nikaya.terms:
#         term = pian.terms[0]
#         print(pian.mulu)
#         if not isinstance(term, base.Container):
#             input("hehe")
#             print(term._e.to_str())
#

def main():
    book = base.load_from_xmlp5(xmls)
    # nikaya = get_nikaya()
    # print_title(nikaya, 0)
    # check_x_first_term(book)


if __name__ == "__main__":

    main()
