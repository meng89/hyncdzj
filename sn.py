#!/usr/bin/env python3
import re


import os

import xl


class Node(object):
    def __init__(self, title):
        self.title = title
        self.subs = []
        self.ps = []


class Pian(Node):
    def __init__(self, title):
        super().__init__(title)
        self.xiangyings = self.subs


class Xiangying(Node):
    def __init__(self, title):
        super().__init__(title)
        self.pins = self.subs


class Pin(Node):
    def __init__(self, title):
        super().__init__(title)
        self.suttas = self.subs


class Sutta(object):
    def __init__(self, title):
        self.ps = []


class SN(object):
    def __init__(self):
        self.pians = []


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
xmlp5_dir = os.path.join(PROJECT_ROOT, "xml-p5")


xmls = [
    "N/N13/N13n0006.xml",
    "N/N14/N14n0006.xml",
    "N/N15/N15n0006.xml",

    "N/N16/N16n0006.xml",
    "N/N17/N17n0006.xml",

    "N/N18/N18n0006.xml"
]


def is_pin(cbdiv3s):
    for div in cbdiv3s:
        for mulu in div.find_kids("cb:mulu"):
            m = re.match("^第[一二三四五六七八九十]+.+品.*$", mulu.kids[0])
            if m:
                return True
    return False


for one in xmls:
    xmlstr = open(os.path.join(xmlp5_dir, one), "r").read()

    xml = xl.parse(xmlstr, do_strip=True)

    tei = xml.root

    text = tei.find_kids("text")[0]
    body = text.find_kids("body")[0]
    print(one)

    snikaya = SN()

    for cb_div in body.find_kids("cb:div"):
        assert len(cb_div.find_kids("cb:mulu")) == 1
        cb_mulu = cb_div.find_kids("cb:mulu")[0]
        _pian_title = cb_mulu.kids[0]  # 篇

        m = re.match(r"^(.+篇).* \(\d+-\d+\)$", _pian_title)
        assert m

        if snikaya.pians and snikaya.pians[-1].title != m.group(1):
            pian = snikaya.pians[-1]
        else:
            pian = Pian(m.group(1))
            snikaya.pians.append(pian)

        for cb_div2 in cb_div.find_kids("cb:div"):
            assert len(cb_div2.find_kids("cb:mulu")) == 1
            cb_mulu2 = cb_div2.find_kids("cb:mulu")[0]
            print(" 2", cb_mulu2.kids[0])  # 相应

            _xy_title = cb_mulu2.kids[0]
            m2 = re.match(r"^.*(\S相應)$", _xy_title)
            assert m2
            xy = Xiangying(m2.group(1))
            pian.xiangyings.append(xy)

            for cb_div3 in cb_div2.find_kids("cb:div"):
                x = "品" if is_pin(cb_div2.find_kids("cb:div")) else "经"
                assert len(cb_div3.find_kids("cb:mulu")) == 1
                cb_mulu3 = cb_div3.find_kids("cb:mulu")[0]
                print("  3[{}]".format(x), cb_mulu3.kids[0])  # 品/经


                for cb_div4 in cb_div3.find_kids("cb:div"):
                    if len(cb_div4.find_kids("cb:mulu")) != 1:
                        input(cb_div4.find_kids("cb:mulu"))
                    cb_mulu4 = cb_div4.find_kids("cb:mulu")[0]
                    #print("   4", cb_mulu4.kids[0])  # 品/经/节

                    for cb_div5 in cb_div4.find_kids("cb:div"):
                        assert len(cb_div5.find_kids("cb:mulu")) == 1
                        cb_mulu5 = cb_div5.find_kids("cb:mulu")[0]
                        # print("    5", cb_mulu5.kids[0])  # 经/节
                        pass


def do_pin_(snikaya, pian, xiangying, cb_div):
    if snikaya.pians.index(pian) == x and pian.xiangyings.index(xiangying) == y:
        for sub_cb_div in cb_div2.find_kids("cb:div"):
            do_pins(snikaya, pian, xiangying, sub_cb_div)


def do_pins(snikaya, pian, xiangying, _cbdiv):
    for pin_cbdiv in _cbdiv.find_kids("cb:div"):
        title = pin_title(pin_cbdiv.find_kids("cb:mulu")[0])
        pin = Pin(title)
        xiangying.pins.append(pin)

        do_suttas(snikaya, pian, xiangying, pin, pin_cbdiv)


def do_suttas(snikaya, pian, xiangying, pin, pin_cbdiv):
    for sutta_cbdiv in pin_cbdiv.find_kids("cb:div"):
        mulu = sutta_cbdiv.find_kids("cb:mulu")[0]
        title = sutta_title(mulu)



def sutta_title(text):
    pass


def pin_title(text):
    m = re.match(r"^第[一二三四五六七八九十]\s+(\S+品.*)$", text)
    if m:
        return m.group(1)
    else:
        input(text)
