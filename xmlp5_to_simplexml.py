import re

import xl


def trans_elements(elements, note_index) -> tuple:
    new_elements = []
    notes = []
    new_note_index = note_index
    for e in elements:
        new_es, notes2, new_note_index = trans_element(e, new_note_index)
        new_elements.extend(new_es)
        notes2.extend(notes2)

    return new_elements, notes, new_note_index


def trans_element(element, note_index):
    for fun in (head, string, lg, p):
        try:
            return fun(element, note_index)

        except TypeError:
            continue

    print("cannot handle this element:", element.tag)
    raise Exception


# pass
def head(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "head":
        es, notes, new_note_index = trans_elements(e.kids, note_index)
        h1 = xl.Element("h1", kids=es)
        return [h1], notes, new_note_index
    else:
        raise TypeError


def string(e, note_index):
    if isinstance(e, str):
        return [e], [], note_index
    else:
        raise TypeError


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

def note(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "note":

        if len(e.kids) == 0:
            return [], [], note_index

        if "【CB】" in e.kids[0] and "【南傳】" in e.kids[0]:
            return [], [], note_index

        if "add" in e.attrs.keys():
            return [], [], note_index

        else:
            new_note_index = note_index + 1
            twn = xl.Element(tag="twn",
                             attrs={"n": str(new_note_index)},
                             kids=["[{}]".format(new_note_index)])
            note_ = xl.Element(tag="note",
                               attrs={"n": str(new_note_index)},
                               kids=e.kids)
            return [twn], [note_], new_note_index

    else:
        raise TypeError


# 〔一六〕睡
# <note n="0009a1201" resp="CBETA" type="add">眠【CB】，眼【南傳】</note>
# <app n="0009a1201">
#   <lem wit="【CB】" resp="CBETA.maha">眠</lem>
#   <rdg wit="【南傳】">眼</rdg>
# </app>
# 、懶惰
def app(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "app":
        lem = e.kids[0]
        return trans_element(lem, note_index)
    else:
        raise TypeError


def space(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "space":
        quantity = int(e.attrs["quantity"])
        return [" " * quantity], [], note_index

    else:
        raise TypeError


# <head>
# <ref cRef="PTS.S.1.2"/>
# 〔二〕解脫
####
#
def ref(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "ref":
        return [e], [], note_index
    else:
        raise TypeError


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
def lg(e, note_index):
    notes = []
    new_note_index = note_index
    if isinstance(e, xl.Element) and e.tag == "lg":
        person = None
        sentences = []

        for le in e.find_kids("l"):
            sentence = []
            for _lkid in le.kids:
                if isinstance(_lkid, str):
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
                    es, notes2, new_note_index = trans_element(_lkid, note_index)
                    sentence.extend(es)
                    notes.append(notes2)

                sentences.append(sentence)

        j = xl.Element("j")
        if person:
            j.attrs["p"] = person
        for s in sentences:
            j.kids.append(xl.Element("s", kids=s))

        return [j], notes, new_note_index

    else:
        raise TypeError


# 遠離於
# <g ref="#CB03020"/>
# 欲
# <caesura style="text-indent:5em;"/>
# 無欲修梵行
####
# 不在 Unicode 里的生僻字
def g(e, note_index):
    if isinstance(e, xl.Element) and e.tag == "g":
        return [e], [], note_index
    else:
        raise TypeError


# 普通句子
def p(e, note_index):
    element = xl.Element("p")
    if isinstance(e, xl.Element) and e.tag == "p":
        kids, notes, new_note_index = trans_elements(e.kids, note_index)
        element.kids[:] = kids
        return [element], notes, new_note_index
    else:
        raise TypeError
