#!/usr/bin/env python3

# 小诵经

import os


import p5a_to_simple


xmls = [
    "N/N26/N26n0008.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_khp"))

if __name__ == "__main__":
    main()
