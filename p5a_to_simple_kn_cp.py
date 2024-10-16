#!/usr/bin/env python3

# Cariyāpiṭaka
# 所行藏

import os


import load_from_p5a


xmls = [
    "N/N44/N44n0021.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_cp"))

if __name__ == "__main__":
    main()
