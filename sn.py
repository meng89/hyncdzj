#!/usr/bin/env python3
import re
import os


import xl


class Container(object):
    def __init__(self, head=None):
        self.head = head or []
        self.subs = []
        self.body = []


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
    def __init__(self, enote: xl.Element):
        self.contents = enote.kids
        self.n = enote.attrs["n"]


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
        return True, Note(e)
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


def note_filter(objs: list):
    new_objs = []
    for i in range(len(objs)):
        obj = objs[i]
        if isinstance(obj, Note):
            if exist_same_note_n(obj.n, objs[i+1]):
                continue
        new_objs.append(obj)


def exist_same_note_n(n, objs):
    for obj in objs:
        if isinstance(obj, Note) and obj.n == n:
            return True
    return False


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
                assert left != []
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


if __name__ == "__main__":
    main()
