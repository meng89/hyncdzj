#!/usr/bin/env python3

# 长老偈

import os


import p5a_to_simple


xmls = [
    "N/N28/N28n0015.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_thag"))

if __name__ == "__main__":
    main()
