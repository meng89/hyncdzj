#!/usr/bin/env python3

import re


def han_num_to_hindu_nume(s:str):
    (s.replace("一", "1").replace("二", "2").replace("三", "3")
     .replace("四", "4").replace("五"))


def main():
    name = '〔七二～八〇〕第二～第十\u3000不知（之一）'
    m = m = re.match(r"^〔([一二三四五六七八九十〇]+)〕～〔([一二三四五六七八九十〇]+)〕"
                     r"第二+～第十+　(\S+)$", name)

    print(repr(m.group(1)), repr(m.group(2)), repr(m.group(3)))


if __name__ == "__main__":
    main()
