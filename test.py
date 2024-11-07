#!/usr/bin/env python3

import config
import os
import xl


def main():
    shuoming_filename = "电子书制作说明.xhtml"
    shuoming_path = os.path.join(config.PROJECT_ROOT, shuoming_filename)
    xml = xl.parse(open(shuoming_path).read())
    print(xml.to_str())

main()
