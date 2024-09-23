#!/usr/bin/env python3

# 饿鬼事

import os


import p5a_to_simple


xmls = [
    "N/N28/N28n0014.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_vv"))

if __name__ == "__main__":
    main()