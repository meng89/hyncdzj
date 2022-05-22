#!/usr/bin/env python3
import re
import os


import xl


class Container(object):
    def __init__(self, head=None):
        self.head = head or []
        self.subs = []
        self.body = []


class Pian(Container):
    def __init__(self, head):
        super().__init__(head)


class SN(object):
    def __init__(self):
        self.pians = []


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
xmlp5_dir = os.path.join(PROJECT_ROOT, "xml-p5a")


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


class Note(object):
    def __init__(self, text):
        self.text = text


class P(object):
    def __init__(self, atoms=None):
        self.atoms = atoms or []


class G(object):
    def __init__(self, ref):
        self.ref = ref


class Ref(object):
    def __init__(self, cref):
        self.cref = cref


class Lg(object):
    def __init__(self, lg_element):
        self.speaker = None
        self.body = []

        for le in lg_element.find_kids("l"):
            line = []
            sentence = []
            for _lkid in le.kids:
                if isinstance(_lkid, str):
                    m = re.match(r"^(〔.+〕)(.+)$", _lkid)
                    if m:
                        assert self.speaker is None
                        self.speaker = m.group(1)
                        sentence.append(m.group(2))
                    else:
                        sentence.append(_lkid)

                elif isinstance(_lkid, xl.Element):
                    if _lkid.tag == "caesura":
                        line.append(sentence)
                        sentence = []
                        continue

                    match do_atom(e=_lkid, funs=[do_note, do_g, do_ref, do_app]):
                        case True, atom:
                            sentence.append(atom)
                        case False, _:
                            raise Exception(_lkid)

            assert sentence
            line.append(sentence)
            self.body.append(line)


def do_str(e):
    if isinstance(e, str):
        return True, [e]
    else:
        return False, e


def do_note(e):
    if isinstance(e, xl.Element) and e.tag == "note":
        if e.attrs["type"] == "add":
            return True, []
        elif e.attrs["type"] == "orig":
            return True, [Note(e.kids[0])]
        elif e.attrs["mod"] == "mod":
            return True, [Note(e.kids[0])]
        else:
            raise Exception(e.attrs)
    else:
        return False, e


def do_g(e):
    if isinstance(e, xl.Element) and e.tag == "g":
        return True, [G(e.attrs["ref"])]
    else:
        return False, e


def do_ref(e):
    if isinstance(e, xl.Element) and e.tag == "ref":
        return True, [Ref(e.attrs["cRef"])]
    else:
        return False, e


def do_app(e):
    if isinstance(e, xl.Element) and e.tag == "app":
        lem = e.kids[0]
        if isinstance(lem.kids[0], str):
            return True, [lem.kids[0]]
        elif isinstance(lem.kids[0], xl.Element) and lem.kids[0].tag == "space":
            return True, []
    else:
        return False, e


def ignore_lb(e):
    if isinstance(e, xl.Element) and e.tag == "lb":
        return True, []
    else:
        return False, e


def ignore_pb(e):
    if isinstance(e, xl.Element) and e.tag == "pb":
        return True, []
    else:
        return False, e


def do_atoms(atoms, funs):
    new_atoms = []
    for i in range(len(atoms)):
        answer, value = do_atom(atoms[i], funs)
        if answer is True:
            new_atoms.append(value)
        else:
            return new_atoms, atoms[i:]

    return new_atoms, []


def do_atom(e, funs):
    for fun in funs:
        try:
            answer, x = fun(e)
            if answer is True:
                return True, x
        except TypeError:
            print((fun, e))
            exit()


    return False, None


class ElementError(Exception):
    pass


def make_tree(container, cbdiv):
    heads = cbdiv.find_kids("head")
    assert len(heads) == 1
    container.head = heads[0]

    for kid in cbdiv.kids:
        assert isinstance(kid, xl.Element)
        if kid.tag == "p":
            if len(kid.kids) == 1 and re.match(r"^[〇一二三四五六七八九十]+$", kid.kids[0]):
                pass
            else:
                atoms, left = do_atoms(kid.kids, funs=[ignore_pb, ignore_lb, do_str, do_note, do_g, do_ref])
                assert left == []
                container.body.append(P(atoms))

        elif kid.tag == "lg":
            lg = Lg(kid)
            container.body.append(lg)

        elif kid.tag == "lb":
            pass

    for sub_cbdiv in cbdiv.find_kids("cb:div"):
        sub_container = Container()
        make_tree(sub_container, sub_cbdiv)
        container.subs.append(sub_container)


def main():
    snikaya = SN()
    for one in xmls:
        xmlstr = open(os.path.join(xmlp5_dir, one), "r").read()

        xml = xl.parse(xmlstr, do_strip=True)

        tei = xml.root

        text = tei.find_kids("text")[0]
        body = text.find_kids("body")[0]
        print(one)

        for cb_div in body.find_kids("cb:div"):
            assert len(cb_div.find_kids("cb:mulu")) == 1
            cb_mulu = cb_div.find_kids("cb:mulu")[0]
            _pian_title = cb_mulu.kids[0]  # 篇

            m = re.match(r"^(.+篇).* \(\d+-\d+\)$", _pian_title)
            assert m

            if snikaya.pians and snikaya.pians[-1].head == m.group(1):
                pian = snikaya.pians[-1]
            else:
                pian = Pian(m.group(1))
                print(pian.head)
                snikaya.pians.append(pian)

            make_tree(pian, cb_div)


def sutta_title(text):
    # 相应部每篇经文，应该有 经号开始，经号结束，经名

    # 有偈篇, 諸天相應
    # 〔一〕瀑流
    m = re.match(r"^〔([〇一二三四五六七八九十]+)〕(?:第[〇一二三四五六七八九十]+\s)?(\S+)$", text)
    if m:
        return m.group(1), m.group(1), m.group(2)

    # 因緣篇, 因緣相應
    # 〔七二～八〇〕第二～第十　不知（之一）
    m = re.match(r"^〔([〇一二三四五六七八九十]+)～([〇一二三四五六七八九十]+)〕(?:第[〇一二三四五六七八九十]+～第?[〇一二三四五六七八九十]+)?\s(\S+)$", text)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 因緣篇, 迦葉相應
    # 第一\u3000滿足
    m = re.match(r"^第([〇一二三四五六七八九十]+)\s(.+)$", text)
    if m:
        return m.group(1), m.group(1), m.group(2)

    if text == "〔三八～四三〕第八　父、第九　兄弟、第十　姊妹、第十一　子、第十二　女、第十三　妻":
        return "三八", "四三", "父、兄弟、姊妹、子、女與妻"

    # 1. 因緣篇，羅睺羅相應，界韵品
    # 1. 〔一二～二〇〕第二～第十
    # 2. 犍度篇, 見相應, 重說品
    # 2. 〔二〇～三五〕第二～十七
    m = re.match(r"^〔([〇一二三四五六七八九十]+)～([〇一二三四五六七八九十]+)〕(第[〇一二三四五六七八九十]+～第?[〇一二三四五六七八九十]+)$", text)
    if m:
        return m.group(1), m.group(2), None  # todo

    # 犍度篇, 龍相應
    # 〔一一～二〇〕第十一　布施利益（一）
    m = re.match(r"^〔([〇一二三四五六七八九十]+)～([〇一二三四五六七八九十]+)〕第[〇一二三四五六七八九十]+\s(\S+)$", text)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 犍度篇, 婆蹉種相應
    # 〔一〕第一～五　無知（一～五）
    m = re.match(r"^〔[〇一二三四五六七八九十]+〕第([〇一二三四五六七八九十])+～([〇一二三四五六七八九十])+\s(\S+)$", text)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 犍度篇, 婆蹉種相應
    # 第五十二～五十四　不現見（二～四）
    m = re.match(r"^第([〇一二三四五六七八九十]+)～([〇一二三四五六七八九十]+)\s(\S+)$", text)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 犍度篇, 禪定相應
    if text == "第五十一～五十二〔引發〕":
        return "五十一", "五十二", "〔引發〕"

    # 六處篇, 六處相應
    # 〔五六、五七〕第四、第五　諸漏（一～二）
    m = re.match(r"^〔([〇一二三四五六七八九十]+)、([〇一二三四五六七八九十]+)〕第[〇一二三四五六七八九十]+、第[〇一二三四五六七八九十]+\s(\S+)$", text)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 六處篇, 六處相應
    # 〔一六八〕第四、五、六　欲念（四、五、六）
    m = re.match(r"^〔([〇一二三四五六七八九十]+)〕第\S+\s(\S+)$", text)
    if m:
        return m.group(1), m.group(1), m.group(2)

    # 六處篇, 沙門出家相應
    if text == "第二～第十五（與閻浮車相應之二～一五全部相同）":
        return "二", "十五", "（與閻浮車相應之二～一五全部相同）"

    input(("不能解析sutta_title", repr(text)))


def pin_title(text):
    m = re.match(r"^第[一二三四五六七八九十]\s+(\S+品.*)$", text)
    if m:
        return m.group(1)
    m = re.match(r"^第[一二三四五六七八九十]品$", text)
    if m:
        return text

    input(("不能解析pin_title", repr(text)))


if __name__ == "__main__":
    main()
