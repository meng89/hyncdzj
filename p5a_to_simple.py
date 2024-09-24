import re
import os
import sys
from copy import deepcopy

from base import find_parent_dir, has_sub_mulu, make_tree

sys.path.append("/mnt/data/projects/xl")

import xl

import base
import config


def transform_elements(elements) -> list:
    new_elements = []
    for e in elements:
        if isinstance(e, xl.Element):
            new_es = transform_element(e)
            new_elements.extend(new_es)
        elif isinstance(e, str):
            new_elements.append(e)
        else:
            raise Exception
    return new_elements


def transform_element(element):
    for fun in (body_fun, cbdiv_fun, cbmulu_fun, head_fun, string_fun, lg_fun, p_fun, note_fun, app_fun, space_fun, ref_fun, g_fun,
                label_fun, list_fun, item_fun):
        result = fun(element)
        if result is not None:
            return result
        else:
            continue

    print("cannot handle this element:", element.to_str())
    raise Exception


def list_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "list"):
            # and "rend" in e.attrs.keys() and e.attr["rand"] == "mo-marker"):
        return None

    new_list = xl.Element("list")
    new_list.kids.extend(transform_elements(e.kids))

    return [new_list]

def item_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "item"):
        return None

    new_item = xl.Element("item")
    for x in transform_elements(e.kids):
        if isinstance(x, xl.Element) and x.tag == "p":
            new_item.kids.extend(x.kids)
        else:
            new_item.kids.append(x)

    return [new_item]


# 意义不明
#<label type="translation-mark">a</label>
#「行」者，以〔男〕相對〔女〕相，以生支〔入其〕生支，即使入一胡麻

def label_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "label"):
        return None

    return []


def body_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "body"):
        return None

    es = transform_elements(e.kids)
    body = xl.Element("body", attrs=e.attrs, kids=es)
    return [body]


def cbdiv_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "cb:div"):
        return None

    es = transform_elements(e.kids)
    cbdiv = xl.Element("cb:div", attrs=e.attrs, kids=es)
    return [cbdiv]


def cbmulu_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "cb:mulu"):
        return None

    es = transform_elements(e.kids)
    cbmulu = xl.Element("cb:mulu", attrs=e.attrs, kids=es)
    return [cbmulu]


def head_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "head"):
        return None

    es = transform_elements(e.kids)
    head = xl.Element("head", attrs=e.attrs, kids=es)

    try:
        [cbmulu] = head.find_kids("cb:mulu")
    except ValueError:
        return [head]
    else:
        index = head.kids.index(cbmulu)
        head.kids.pop(index)
        return [cbmulu, head]


def string_fun(e):
    if isinstance(e, str):
        return [e]
    else:
        return None


# 禍從欲望生
# <note n="0032074" resp="NanChuan" place="foot" type="orig">禍（agha）Pañcakkhandha dukkha 註釋為（五蘊之苦）。</note>
# <note n="0032074" resp="CBETA" type="mod">
# 禍（agha）Pañcakkhandha dukkha 註釋為（五蘊之苦）。（CBETA 按：漢譯南傳大藏經此頁中缺相對應之註標[74]，今於此處加上[74]之註標。）
# </note>
# <caesura style="text-indent:5em;"/>
# 苦惱從欲生
##

# <note type="cf1">S. 1.72 (PTS 1990: I 41,23)</note>
# <note type="cf2">T02n0099_p0266b22</note>

# <note n="0062a1201" resp="CBETA" type="add" note_key="N13.0062a12.03">國【CB】，王【南傳】</note>

def note_fun(e):
    if isinstance(e, xl.Element) and e.tag == "note":
        if len(e.kids) == 0:
            return []

        elif len(e.kids) == 1 and isinstance(e.kids[0], xl.Element) and e.kids[0].tag == "space":
            return []

        elif "【CB】" in e.kids[0] and "【南傳】" in e.kids[0]:
            return []

        elif "add" in e.attrs.keys():
            return []

        else:
            ewn = xl.Element("ewn")
            ewn.ekid("a")
            _note = ewn.ekid("note")
            _note.kids.extend(e.kids)
            return [ewn]

    else:
        return None

# 〔一六〕睡
# <note n="0009a1201" resp="CBETA" type="add">眠【CB】，眼【南傳】</note>
# <app n="0009a1201">
#   <lem wit="【CB】" resp="CBETA.maha">眠</lem>
#   <rdg wit="【南傳】">眼</rdg>
# </app>
# 、懶惰
def app_fun(e):
    if isinstance(e, xl.Element) and e.tag == "app":
        lem = e.kids[0]
        return transform_elements(lem.kids)
    else:
        return None


def space_fun(e):
    if isinstance(e, xl.Element) and e.tag == "space":
        quantity = int(e.attrs["quantity"])
        return [" " * quantity]

    else:
        return None


# <head>
# <ref cRef="PTS.S.1.2"/>
# 〔二〕解脫
####
#
def ref_fun(e):
    if isinstance(e, xl.Element) and e.tag == "ref":
        return [e]
    else:
        return None


# <lg type="regular" xml:id="lgN13p0003a0101" style="margin-left:0em;text-indent:0em;">
# <l style="text-indent:2em">
# 〔世尊：〕有喜之滅盡
# <caesura style="text-indent:5em;"/>
# 亦盡想與識
# </l>
# <lb ed="N" n="0003a02"/>
# <l style="text-indent:7em">
# 受滅皆寂靜
# <caesura style="text-indent:5em;"/>
# 友我之如是
# </l>
# <lb ed="N" n="0003a03"/>
# <l style="text-indent:7em">
# 知眾生解脫
# <caesura style="text-indent:5em;"/>
# 令解脫遠離
# </l>
# </lg>
####
# 偈子
def lg_fun(e):
    if isinstance(e, xl.Element) and e.tag == "lg":
        person = None
        sentences = []

        for le in e.find_kids("l"):
            sentence = []

            for _lkid in le.kids:
                if isinstance(_lkid, str):
                    # 〔世尊：〕他醒於五眠
                    #          他眠於五醒
                    #          染塵依於五
                    #          依五而得清
                    m = re.match(r"^〔(.+)：〕(.+)$", _lkid)
                    if m:
                        assert person is None  # 预估每个偈子仅有一位咏颂人
                        person = m.group(1)
                        sentence.append(m.group(2))
                    else:
                        sentence.append(_lkid)

                elif isinstance(_lkid, xl.Element) and _lkid.tag == "caesura":
                    sentences.append(sentence)
                    sentence = []
                    continue

                else:
                    es = transform_element(_lkid)
                    sentence.extend(es)

            sentences.append(sentence)

        j = xl.Element("j")
        if person:
            j.attrs["p"] = person
        for s in sentences:
            j.kids.append(xl.Element("s", kids=s))

        return [j]

    else:
        return None


# 遠離於
# <g ref="#CB03020"/>
# 欲
# <caesura style="text-indent:5em;"/>
# 無欲修梵行
####
# 不在 Unicode 里的生僻字
g_map = {
    "#CB03020": "婬",
    "#CB00416": "箒",
    "#CB00819": "塔", # potanaṃ 地名音译中之 ta
    "#CB00597": "糠", # 谷物的外壳，庄春江译为糠
    "#CB00595": "麨",
    "#CB00144": "㝹",
}


def g_fun(e):
    if isinstance(e, xl.Element) and e.tag == "g":
        s = g_map[e.attrs["ref"]]
        return [s]
    else:
        return None


# 普通句子
def p_fun(e):
    element = xl.Element("p")
    if isinstance(e, xl.Element) and e.tag == "p":
        kids = transform_elements(e.kids)
        element.kids[:] = kids
        return [element]
    else:
        return None

########################################################################################################################

def get_body(filename) -> xl.Element:

    file = open(filename, "r")

    xmlstr = file.read()
    file.close()
    xml = xl.parse(xmlstr, strip=True)
    tei = xml.root
    text = tei.find_kids("text")[0]
    body = text.find_kids("body")[0]
    return body


def get_head_string(e):
    s = ""
    for x in e.kids:
        if isinstance(x, str):
            s += x
        else:
            pass
    return s


########################################################################################################################
#
# 删除没有mulu和head的div；添加缺失的mulu或head，使mulu和head成为一对

def unfold_meanless_div(div):
    new_kids = []

    first_div_index = None
    first_mulu_index = None

    for index, term in enumerate(div.kids):
        if isinstance(term, xl.Element) and term.tag == "cb:div":
            es = unfold_meanless_div(term)
            new_kids.extend(es)
            if first_div_index is None:
                first_div_index = index

        elif isinstance(term, xl.Element) and term.tag == "cb:mulu":
            new_kids.append(term)
            if first_div_index is None:
                first_div_index = index

        else:
            new_kids.append(term)


    if first_mulu_index is not None:


def unfold_meanless_div(div:xl.Element, div_level=-1):
    new_kids = []
    passed_mulu = False
    mulu = None
    mulu_index = None

    passed_head = False
    head = None
    head_index = None

    my_level = None

    for index, term in enumerate(div.kids):
        if isinstance(term, xl.Element) and term.tag == "cb:div":
            es = unfold_meanless_div(term, )
            new_kids.extend(es)
        elif isinstance(term, xl.Element) and term.tag == "cb:mulu":
            new_kids.append(term)
            mulu = term
            passed_mulu = True
            mulu_index = index
        elif isinstance(term, xl.Element) and term.tag == "head":
            new_kids.append(term)
            head = term
            passed_head = True
            head_index = index

        else:
            new_kids.append(term)

    if passed_head and not passed_mulu:
        assert head_index == 0
        mulu = xl.Element("cb:mulu")
        mulu.skid(get_head_string(head))
        new_kids.insert(0, mulu)

    elif passed_mulu and not passed_head:
        assert mulu_index == 0
        head = xl.Element("head")
        head.kids.extend(mulu.kids)
        new_kids.insert(1, head)

    # unflod
    elif passed_mulu is None and passed_head is None:
        return new_kids

    else:
        div = xl.Element("cb:div")
        div.kids.extend(new_kids)
        return [div]

########################################################################################################################
#
# 添加缺失的div，使每个mulu都有div包裹它
def add_missed_cbdiv(div):
    new_es = []
    i = 0
    while i < len(div.kids):
        if isinstance(div.kids[i], xl.Element) and div.kids[i].tag == "cb:div":
            new_es.append(add_missed_cbdiv(div.kids[i]))
            i += 1
            continue

        if isinstance(div.kids[i], xl.Element) and div.kids[i].tag == "cb:mulu":
            new_kid_div = xl.Element("cb:div")
            new_mulu = new_kid_div.ekid("cb:mulu")
            new_mulu.attrs.update(div.kids[i].attrs)
            i += 1
            sub_terms, i = read_till_next_mulu_or_div(div.kids, i)
            new_kid_div.kids.extend(sub_terms)
            new_es.append(new_kid_div)
        else:
            new_es.append(div.kids[i])
            i += 1

    return new_es

def read_till_next_mulu_or_div(kids, i):
    terms = []
    while i < len(kids):
        kid = kids[0]
        i += 1
        if isinstance(kid, xl.Element) and kid.tag.lower() in ("cb:div", "cb:mulu"):
            break
        else:
            terms.append(kid)

    return terms, i

########################################################################################################################
#
# 让 cbdiv 按照 mulu level 值回到正确的地方

def move_place_by_level(book_div):
    move_place_by_level2(book_div, {})

def move_place_by_level2(div:xl.Element, divs:dict):
    mulu = div.kids[0]
    level = mulu.attrs["level"]
    parent_level = str(int(level) - 1)

    if parent_level != -1:
        parent = divs[parent_level]
        parent.kids.append(div)

    divs[level] = div
    kid_divs = div.kids[2:]
    div.kids[2:] = []

    for term in kid_divs:
        move_place_by_level2(term, divs)

########################################################################################################################
#
# 让游离元素有 div、空mulu 和 空head
#
def pack_piece_in_div(div): # book = div
    mulu = div.kids[0]
    level = mulu.attrs["level"]

    if has_sub_dir_simple(div) is False:
        return div

    new_kids = [div.kids[0], div.kids[1]]

    i = 2 # 越过 mulu 和 head
    while i < len(div.kids):
        if isinstance(div.kids[i], xl.Element) and div.kids[i].tag == "cb:div":
            new_kids.append(pack_piece_in_div(div.kids[i]))
            i += 1
        else:
            pieces, i = read_till_next_mulu_or_div(div.kids, i)
            sub_div = xl.Element("cb:div")
            mulu = sub_div.ekid("cb:mulu")
            mulu.attrs["level"] = str(int(level) + 1)

            sub_div.ekid("head")
            sub_div.kids.extend(pieces)
            new_kids.append(sub_div)
            i += 1
    div.kids = new_kids
    return div


def has_sub_dir_simple(div):
    for x in div.kids:
        if isinstance(x, xl.Element) and x.tag == "cb:div":
            return True
    return False

########################################################################################################################

# 1. 增加缺失的head，复制于mulu
# 2. head里提取mulu
# 3.

def load_from_p5a(xmls, name) -> base.Dir:
    book_div = xl.Element("cb:div")
    mulu = book_div.ekid("cb:mulu")
    mulu.attrs["level"] = "0"
    mulu.kids.append(name)
    head = book_div.ekid("head")
    head.kids.append(name)

    for xml in xmls:
        filename = os.path.join(config.xmlp5a_dir, xml)
        print("xml:", xml.removeprefix(config.xmlp5a_dir))
        file = open(filename, "r")
        xmlstr = file.read()
        file.close()
        xml = xl.parse(xmlstr)
        tei = xml.root
        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]
        book_div.kids.extend(body.kids)


    book = make_book(book_div)

    return book
