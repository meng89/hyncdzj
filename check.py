#!/usr/bin/env python3
import os
import sys

sys.path.append("/mnt/data/projects/xl")

import xl
import config
import base


def eliminate_cbdiv(elements) -> list:
    new_elements = []
    for x in elements:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            new_elements.extend(eliminate_cbdiv(x.kids))
        else:
            new_elements.append(x)
    return new_elements


def check_head_and_mulu(e, body):
    result = []
    for x in e.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            result.extend(check_head_and_mulu_real(x, body))

    for lb in result:
        print(lb.to_str())
    print()

# 事实1：有的cbdiv下没有 head。
# 事实2: 极少 cbdiv下没有 mulu 也没有head。似乎应该删除此cb:div标签包裹


def check_head_and_mulu_real(cb_div, body) -> list:
    result = []

    mulus = []
    heads = []

    for x in cb_div.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            result.extend(check_head_and_mulu_real(x, body))
        elif isinstance(x, xl.Element) and x.tag == "cb:mulu":
            mulus.append(x)
        elif isinstance(x, xl.Element) and x.tag == "head":
            heads.append(x)
        else:
            pass

    result.extend({cb_div, mulus, heads})
    return result


def find_lb(e, e2):
    lb, findit = find_lb2(e, e2)
    assert lb is not None
    assert findit is True
    return lb


def find_lb2(e, e2):
    lb = None
    findit = False

    for x in e.kids:
        if x is e2:
            findit = True

        elif isinstance(x, xl.Element) and x.tag == "lb":
            lb = x

        elif isinstance(x, xl.Element):
            lb2, findit2 = find_lb2(x, e2)
            findit = findit2 or findit
            lb = lb2 or lb

        if findit:
            break

    return lb, findit


def check_no_head(body):
    cb_divs = get_cb_divs(body)
    for cb_div in cb_divs:
        if len_heads(cb_div) < 1:
            lb = find_lb(body, cb_div)
            print(lb.to_str())


def get_cb_divs(e):
    cb_divs = []
    for x in e.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            cb_divs.append(x)
            cb_divs.extend(get_cb_divs(x))

    return cb_divs


def len_mulus(cb_div) -> int:
    length = 0
    for x in cb_div.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:mulu":
            length += 1
    return length


def len_heads(cb_div) -> int:
    length = 0
    for x in cb_div.kids:
        if isinstance(x, xl.Element) and x.tag == "head":
            length += 1
    return length


MULU = "MULU"
HEAD = "HEAD"


def first_type(cb_div) -> MULU or HEAD or None:
    for x in cb_div.kids:
        if isinstance(x, xl.Element):
            if x.tag == "head":
                return HEAD
            elif x.tag == "cb:mulu":
                return MULU


def last_type(cb_div: xl.Element) -> MULU or HEAD or None:
    for x in cb_div.kids.reverse():
        if isinstance(x, xl.Element):
            if x.tag == "head":
                return HEAD
            elif x.tag == "cb:mulu":
                return MULU


def check_out_cbdiv_term(path: list, cb_div: xl.Element):
    # print(path)
    bit_map = []
    for x in cb_div.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            sub_path = path[:]
            sub_path.append(x)
            check_out_cbdiv_term(sub_path, x)
            bit_map.append((0, x))
        # metadata
        elif isinstance(x, xl.Element) and x.tag in ("cb:juan", "byline", "cb:mulu", "note"):
            pass
        else:
            bit_map.append((1, x))

    (_have_head, _head), (have_middle, middle), (_have_tail, _tail) = xxx(bit_map)

    if have_middle:
        print_path(path)
        if have_middle:
            print("  middles:")
            for x in middle:
                if isinstance(x, xl.Element):
                    print("      ", x.to_str())
                else:
                    print("      ", x)
        print()


def print_path(path: list, step=0):
    if len(path) == 0:
        return None

    cb_div = path.pop(0)
    for x in cb_div.kids:
        print(" " * step, end=""),
        if isinstance(x, xl.Element) and x.tag in ("cb:mulu", "head"):
            print(x.to_str())
        elif isinstance(x, str):
            print(x)
        break

    print_path(path, step + 4)


def xxx(bit_map: list):
    have_head = False
    head = []

    have_middle = False
    middle = []

    have_tail = False
    tail = []

    new_bit_map = bit_map[:]
    while True:
        if len(new_bit_map) > 0 and new_bit_map[0][0] == 1:
            head.append(new_bit_map[0][1])
            new_bit_map.pop(0)
            have_head = True

        else:
            break

    new_bit_map.reverse()
    while True:
        if len(new_bit_map) > 0 and new_bit_map[0][0] == 1:
            tail.append(new_bit_map[0][1])
            new_bit_map.pop(0)
            have_tail = True
        else:
            break

    new_bit_map.reverse()
    for x in new_bit_map:
        # print(x)
        if x[0] == 1:
            have_middle = True
            middle.append(x[1])

    return (have_head, head), (have_middle, middle), (have_tail, tail)


def get_body(filename):

    file = open(filename, "r")

    xmlstr = file.read()
    file.close()
    xml = xl.parse(xmlstr, strip=True)
    tei = xml.root
    text = tei.find_kids("text")[0]
    body = text.find_kids("body")[0]
    return body


def check(xmls, fun):
    for one in xmls:
        body = get_body(one)
        fun(body, body)


def test_xl(xmls):
    import difflib

    xmls2 = []
    filter_xmls = ["B25n0144.xml", "D41n8904.xml", "N64n0031.xm", "T25n1509.xml"]
    for xml in xmls:
        in_it = False
        for filter_xml in filter_xmls:
            if filter_xml in xml:
                in_it = True
                break
        if in_it:
            pass
        else:
            xmls2.append(xml)

    for one in xmls:

        filename = os.path.join(config.XMLP5A_DIR, one)
        print("xml:", filename, end="")
        file = open(filename, "r")
        xmlstr = file.read()
        file.close()

        xml = xl.parse(xmlstr)
        xmlstr2 = xml.to_str()

        xmlstr_noblank = (xmlstr.replace(" ", "").replace("\t", "")
                          .replace("\n", "").replace("\r", "").replace("　", ""))
        xmlstr2_noblank = (xmlstr2.replace(" ", "").replace("\t", "")
                           .replace("\n", "").replace("\r", "").replace("　", ""))

        print(", check:", end="")
        if xmlstr == xmlstr2:
            print("succeed")
        else:
            print("fail")
            f = open("/mnt/data/t1.xml", "w")
            f.write(xmlstr)
            f.close()

            f = open("/mnt/data/t2.xml", "w")
            f.write(xmlstr2)
            f.close()

            for x in difflib.context_diff(xmlstr_noblank, xmlstr2_noblank):
                print(x)
            input()


def main():
    no_prefix_xmls = []
    for one2 in sorted(base.all_xmls(config.XMLP5A_DIR)):
        if one2.startswith(config.XMLP5A_DIR):
            no_prefix_xmls.append(one2.removeprefix(config.XMLP5A_DIR))
        else:
            raise Exception

    for xml in base.n_xmls():
        filename = os.path.join(config.XMLP5A_DIR, xml)
        # print("\n"*2)
        print("xml:", xml.removeprefix(config.XMLP5A_DIR))

        body = get_body(filename)
        # check_no_head(body)
        check_out_cbdiv_term([], body)
        # check(base.n_xmls(), check_head_and_mulu)


if __name__ == "__main__":
    main()
