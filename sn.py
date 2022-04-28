#!/usr/bin/env python3
import os

import xl


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
xmlp5_dir = os.path.join(PROJECT_ROOT, "xml-p5")

xmls = [
    "N/N13/N13n0006.xml",
    "N/N14/N14n0006.xml",
    "N/N15/N15n0006.xml",

    "N/N16/N16n0006.xml",
    "N/N17/N17n0006.xml",

    "N/N18/N18n0006.xml",
    "N/N19/N19n0006.xml"
]


for one in xmls:
    xmlstr = open(os.path.join(xmlp5_dir, one), "r").read()

    xml = xl.parse(xmlstr, do_strip=True)

    tei = xml.root

    text = tei.find_kids("text")[0]
    body = text.find_kids("body")[0]
    cb_div1 = body.find_kids("cb:div")[0]
    p = cb_div1.find_kids("p")[0]
    print(p.kids)
