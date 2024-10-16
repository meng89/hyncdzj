#!/usr/bin/env python3

# Buddhavaṃsa
# 佛种姓

import os


import load_from_p5a


xmls = [
    "N/N44/N44n0020.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_bv"))

if __name__ == "__main__":
    main()
