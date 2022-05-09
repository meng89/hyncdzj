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
    def __init__(self, title=None):
        super().__init__(title)
        self.suttas = self.subs


class Sutta(object):
    def __init__(self, title):
        self.ps = []


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

            if snikaya.pians and snikaya.pians[-1].title == m.group(1):
                pian = snikaya.pians[-1]
            else:
                pian = Pian(m.group(1))
                print(pian.title)
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

                do_pins_(snikaya, pian, xy, cb_div2)


def do_pins_(snikaya, pian, xiangying, xy_cbdiv):
    # 六处篇 六处相应
    if snikaya.pians.index(pian) == 3 and pian.xiangyings.index(xiangying) == 0:
        for sub_cb_div in xy_cbdiv.find_kids("cb:div"):
            do_pins(snikaya, pian, xiangying, sub_cb_div)
    else:
        do_pins(snikaya, pian, xiangying, xy_cbdiv)


def do_pins(snikaya, pian, xiangying, xy_cbdiv):
    if is_pin_sub(xy_cbdiv):
        for pin_cbdiv in xy_cbdiv.find_kids("cb:div"):
            mulu = pin_cbdiv.find_kids("cb:mulu")[0]
            title = pin_title(mulu.kids[0])
            pin = Pin(title)
            xiangying.pins.append(pin)
            do_suttas_(snikaya, pian, xiangying, pin, pin_cbdiv)
    else:
        pin = Pin()
        xiangying.pins.append(pin)
        do_suttas_(snikaya, pian, xiangying, pin, xy_cbdiv)


def do_suttas_(snikaya, pian, xiangying, pin, pin_cbdiv):
    # 犍度篇 见相应 重新说品: 第一章，第二章...
    print(snikaya.pians.index(pian),
          pian.xiangyings.index(xiangying),
          xiangying.pins.index(pin))
    if snikaya.pians.index(pian) == 2 and pian.xiangyings.index(xiangying) == 2 and xiangying.pins.index(pin) == 1:
        for zhang_cbdiv in pin_cbdiv.find_kids("cb:div"):
            do_suttas(snikaya, pian, xiangying, pin, zhang_cbdiv)

    else:
        do_suttas(snikaya, pian, xiangying, pin, pin_cbdiv)


def do_suttas(snikaya, pian, xiangying, pin, pin_cbdiv):
    for sutta_cbdiv in pin_cbdiv.find_kids("cb:div"):
        mulu = sutta_cbdiv.find_kids("cb:mulu")[0]
        title = sutta_title(mulu.kids[0])
        #todo


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
