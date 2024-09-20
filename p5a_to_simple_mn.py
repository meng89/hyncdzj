#!/usr/bin/env python3

# 中部

import os


import p5a_to_simple


xmls = [
    "N/N09/N09n0005.xml",
    "N/N10/N10n0005.xml",
    "N/N11/N11n0005.xml",
    "N/N12/N12n0005.xml"
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "mn"))

if __name__ == "__main__":
    main()
