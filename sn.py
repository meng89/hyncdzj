#!/usr/bin/env python3
import os

import xl


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
xmlp5_dir = os.path.join(PROJECT_ROOT, "xml-p5")

xmlstr = open(os.path.join(xmlp5_dir, "N/N13/N13n0006.xml"), "r").read()

xml = xl.parse(xmlstr, do_strip=True)
xmlstr2 = xml.to_str(do_pretty=True)

open(os.path.join(PROJECT_ROOT, "1.xml"), "w").write(xmlstr2)
