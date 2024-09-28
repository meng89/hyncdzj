#!/usr/bin/env python3

# 经集

import os


import p5a_to_simple


xmls = [
    "N/N27/N27n0012.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_sn"))

if __name__ == "__main__":
    main()
