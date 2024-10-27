import re
import os
import types

import p5a

import xl

import base
import config


def filter_(term: xl.Element or str):
    if isinstance(term, str):
        return term

    e = term
    new_e = xl.Element(tag=e.tag)
    new_e.attrs.update(e.attrs)
    for kid in e.kids:
        # if isinstance(kid, xl.Element):
        #    print("debug:", kid.to_str())

        if isinstance(kid, xl.Element) and kid.tag in ("lb", "pb", "milestone"):
            pass

        elif isinstance(kid, xl.Element) and kid.tag == "p" \
                and len(kid.kids) == 1 and isinstance(kid.kids[0], str) and re.match(r"^[〇一二三四五六七八九十※～]+$",
                                                                                     kid.kids[0]):
            pass

        elif isinstance(kid, str) and kid in ("\n", "\n\r"):
            pass

        elif isinstance(kid, str):
            new_e.kids.append(kid.strip())

        elif isinstance(kid, xl.Comment):
            pass

        else:
            new_e.kids.append(filter_(kid))

    return new_e


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
    for fun in (unclear_fun, cbdiv_fun, cbmulu_fun, head_fun, string_fun,
                lg_fun, p_fun, note_fun, app_fun, space_fun, ref_fun, g_fun,
                label_fun, list_fun, item_fun):
        result = fun(element)
        if result is not None:
            return result
        else:
            continue

    raise Exception("Cannot handle this element:", element.to_str())

def unclear_fun(e):
    if not (isinstance(e, xl.Element) and e.tag == "unclear"):
        return None
    assert e.kids == []
    assert e.attrs == {}
    return [e]

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

        elif isinstance(e.kids[0], str) and "【CB】" in e.kids[0] and "【南傳】" in e.kids[0]:
            return []

        elif "add" in e.attrs.keys():
            return []

        else:
            ewn = xl.Element("ewn")
            ewn.ekid("a")
            _note = ewn.ekid("note")
            _note.kids.extend(transform_elements(e.kids))
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
        ewn = xl.Element("ewn")
        a = ewn.ekid("a")
        a.self_closing=False
        ewn.ekid("note", kids=[e.attrs["cRef"]])
        return [ewn]
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

        ji = xl.Element("j")
        if person:
            ji.kids.append(xl.Element("p", kids=[person]))
        for s in sentences:
            ji.kids.append(xl.Element("s", kids=s))

        return [ji]

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
    "#CB05989": "䁆",
    "#CB00551": "窻",
    "#CB04775": "櫈",
    "#CB22010": "癩",
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


def is_head(x):
    if isinstance(x, xl.Element) and x.tag == "head":
        return True
    else:
        return False

def is_mulu(x):
    if isinstance(x, xl.Element) and x.tag == "cb:mulu":
        return True
    else:
        return False

def is_div(x):
    if isinstance(x, xl.Element) and x.tag == "cb:div":
        return True
    else:
        return False


# 1. head 里提取 mulu
def move_out_mulu_from_head(div:xl.Element):
    new_kids = []
    for kid in div.kids:

        if is_head(kid):
            head_kids = []
            for head_kid in kid.kids:
                if is_mulu(head_kid):
                    new_kids.append(head_kid)
                else:
                    head_kids.append(head_kid)
            kid.kids = head_kids

            new_kids.append(kid)

        elif is_div(kid):
            new_kids.append(move_out_mulu_from_head(kid))

        else:
            new_kids.append(kid)
    div.kids = new_kids

    return div

# 2. 增加缺失的 head，复制于 mulu
def create_missing_head_by_mulu(div:xl.Element):
    insert_list = []
    for index, kid in enumerate(div.kids):
        if is_mulu(kid):
            if not (index + 1 <= len(div.kids) and is_head(div.kids[index + 1])):
                head = xl.Element("head", kids=kid.kids)
                insert_list.append((kid, head))
        elif is_div(kid):
            create_missing_head_by_mulu(kid)

    for mulu, head in insert_list:
        div.kids.insert(div.kids.index(mulu) + 1, head)

    return div


# 2.5 增加缺失的 mulu, 复制于 head
def create_missing_mulu_by_head(div, parent_level: int = None):
    first_kid = div.kids[0]
    if is_head(first_kid):
        s = ""
        for kid in first_kid.kids:
            if isinstance(kid, str):
                s += kid
        mulu = xl.Element("cb:mulu")
        mulu.attrs["level"] = str(parent_level + 1)
        if s:
            mulu.kids.append(s)
        div.kids.insert(0, mulu)

    mulu = div.kids[0]
    parent_level = int(mulu.attrs["level"])
    for kid in div.kids[2:]:
        if is_div(kid):
            create_missing_mulu_by_head(kid, parent_level)

    return div


# 3. 删除不包含 mulu 的 div:
def remove_no_mulu_div(book_div):
    return remove_no_mulu_div2(book_div)[0]

def remove_no_mulu_div2(div):
    terms = []
    for kid in div.kids:
        if is_div(kid):
            terms.extend(remove_no_mulu_div2(kid))
        else:
            terms.append(kid)

    if is_mulu(terms[0]):
        div.kids = terms
        return [div]
    else:
        return terms

# 4. 添加缺失的 div，使每个 mulu 都有 div 包含它
def add_missing_div(book_div):
    return add_missed_cbdiv2(book_div)

def add_missed_cbdiv2(div):
    new_es = div.kids[:2]
    i = 2
    while i < len(div.kids):
        if is_div(div.kids[i]):
            new_es.append(add_missed_cbdiv2(div.kids[i]))
            i += 1
            continue

        if is_mulu(div.kids[i]):
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

    div.kids = new_es
    return div

def read_till_next_mulu_or_div(kids, i):
    terms = []
    while i < len(kids):
        kid = kids[i]
        if is_mulu(kid) or is_div(kid):
            break
        else:
            terms.append(kid)
            i += 1
    return terms, i

# 5. 让游离元素有 div、空 mulu 和空 head
def create_div_for_pieces(div): # book = div
    mulu = div.kids[0]
    assert is_mulu(mulu)
    level = mulu.attrs["level"]

    if has_sub_div(div) is False:
        return div

    new_kids = div.kids[:2]

    i = 2 # 越过 mulu 和 head
    while i < len(div.kids):
        if is_div(div.kids[i]):
            new_kids.append(create_div_for_pieces(div.kids[i]))
            i += 1

        else:
            pieces, i = read_till_next_mulu_or_div(div.kids, i)
            sub_div = xl.Element("cb:div")
            mulu = sub_div.ekid("cb:mulu")
            mulu.attrs["level"] = str(int(level) + 1)

            sub_div.ekid("head")
            sub_div.kids.extend(pieces)
            new_kids.append(sub_div)

    div.kids = new_kids
    return div


def has_sub_div(div):
    for x in div.kids:
        if is_div(x):
            return True
    return False


# 6. 让 div 按照 mulu level 的值回到正确的地方
def reset_right_place_by_level(book_div):
    move_place_by_level2(book_div, {})
    return book_div

def move_place_by_level2(div:xl.Element, divs:dict):
    mulu = div.kids[0]
    level = mulu.attrs["level"]
    parent_level = str(int(level) - 1)

    if parent_level != "-1":
        parent = divs[parent_level]
        parent.kids.append(div)

    if has_sub_div(div):
        divs[level] = div
        kid_divs = div.kids[2:]
        div.kids[2:] = []

        for term in kid_divs:
            move_place_by_level2(term, divs)

########################################################################################################################

def make_tree(div: xl.Element):
    if has_sub_div(div):
        obj = base.Dir()
        for kid in div.kids[2:]:
            mulu, kid_obj = make_tree(kid)
            obj.list.append((mulu, kid_obj))
    else:
        obj = base.Doc()
        # obj.body.meta.head = div.kids[1]
        for kid in div.kids[2:]:
            obj.body.kids.append(kid)

    return get_mulu_str(div), obj


def get_mulu_str(div):
    assert is_mulu(div.kids[0])
    try:
        return div.kids[0].kids[0]
    except IndexError:
        return ""

def get_head_kids(div):
    return div.kids[1].kids


########################################################################################################################

def change_book_name_by_given_fun(d: base.Dir, change_name_fun):
    new_list = []
    for name, obj in d.list:
        if name in ("", None):
            new_list.append((name, obj))
            continue

        new_name = change_name_fun(name)
        if isinstance(obj, base.Dir):
            change_book_name_by_given_fun(obj, change_name_fun)
        new_list.append((new_name, obj))

    d.list = new_list
    return d


def ld_get(list_dict, key):
    for k, v in list_dict:
        if k == key:
            return v


def merge_same_name(d: base.Dir):
    new_list = []
    for name, obj in d.list:
        if name in ("", None):
            new_list.append((name, obj))
            continue

        v = ld_get(new_list, name)
        if isinstance(v, base.Dir) and isinstance(obj, base.Dir):
            v.list.extend(obj.list)
            merge_same_name(v)
        else:
            new_list.append((name, obj))
    d.list = new_list
    return d


def remove_single_root(d: base.Dir):
    if len(d.list) == 1:
        name, single = d.list[0]
        d.list = single.list
    return d

########################################################################################################################

def merge_jing_if_name_is_abbr(d: base.Dir):
    new_list = []
    for name, obj in d.list:
        if isinstance(obj, base.Dir):
            if re.match(r"[a-zA-Z]+ \d", name):
                new_obj = merge(obj)
            else:
                new_obj = merge_jing_if_name_is_abbr(obj)
        else:
            new_obj = obj
        new_list.append((name, new_obj))
    d.list = new_list
    return d

########################################################################################################################
def merge_jing_in_one_doc_by_no_number_name(d: base.Dir):
    if is_all_number_name(d) is True:
        #names = []
        #for name, _ in d.list:
        #    names.append(name)
        return merge(d)

    new_list = []
    for name, obj in d.list:
        if isinstance(obj, base.Dir):
            new_obj = merge_jing_in_one_doc_by_no_number_name(obj)
            new_list.append((name, new_obj))
        else:
            new_list.append((name, obj))
    d.list = new_list
    return d

def is_all_number_name(d: base.Dir):
    result_list = []
    for name, obj in d.list:
        if name in ("", None, "攝頌"):
            continue
        m = re.match(r"^（?[一二三四五六七八九十〇]+）?$", name)
        if m:
            result_list.append(True)
        else:
            result_list.append(False)

        if isinstance(obj, base.Dir):
            result_list.append(is_all_number_name(obj))

    if False in result_list:
        return False
    else:
        return True


def merge(d, doc=None, level=0):
    doc = doc or base.Doc()

    for name, obj in d.list:
        h = xl.Element("h{}".format(level + 2))
        h.kids.append(name or "-")
        doc.body.kids.append(h)
        if isinstance(obj, base.Doc):
            doc.body.kids.extend(obj.body.kids)
        elif isinstance(obj, base.Dir):
            merge(obj, doc, level + 1)
        else:
            raise Exception

    return doc

########################################################################################################################

def load_book_by_module(m: types.ModuleType) -> base.Dir:
    xmls = p5a.get_xmls_by_serial(m.info.serial)

    book_div = xl.Element("cb:div")
    mulu = book_div.ekid("cb:mulu")
    mulu.attrs["level"] = "0"
    _head = book_div.ekid("head")

    for xml in xmls:
        filename = os.path.join(config.XMLP5A_DIR, xml)
        print("xml:", xml.removeprefix(config.XMLP5A_DIR))
        file = open(filename, "r")
        xmlstr = file.read()
        file.close()
        xml = xl.parse(xmlstr)
        tei = xml.root
        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]
        body = filter_(body)
        book_div.kids.extend(body.kids)

    [book_div] = transform_element(book_div)

    book_div = move_out_mulu_from_head(book_div)
    book_div = create_missing_mulu_by_head(book_div)
    book_div = create_missing_head_by_mulu(book_div)
    book_div = remove_no_mulu_div(book_div) #;write_div(book_div)
    book_div = add_missing_div(book_div)
    book_div = create_div_for_pieces(book_div)
    book_div = reset_right_place_by_level(book_div)
    name, book = make_tree(book_div)

    if hasattr(m, "change"):
        book = m.change(book)

    if hasattr(m, "change_name_fun"):
        book = change_book_name_by_given_fun(book, m.change_name_fun)

    book = merge_same_name(book)

    book = remove_single_root(book)

    book = merge_jing_if_name_is_abbr(book)
    book = merge_jing_in_one_doc_by_no_number_name(book)

    return book
