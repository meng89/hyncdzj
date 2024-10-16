#!/usr/bin/env python3

# 自说经

import os


import load_from_p5a


xmls = [
    "N/N26/N26n0010.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_ud"))

if __name__ == "__main__":
    main()
