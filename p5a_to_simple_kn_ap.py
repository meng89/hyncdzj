#!/usr/bin/env python3

# Apadāna
# 譬喻/本行

import os


import p5a_to_simple


xmls = [
    "N/N29/N29n0017.xml",
    "N/N30/N30n0017.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_thig"))

if __name__ == "__main__":
    main()
