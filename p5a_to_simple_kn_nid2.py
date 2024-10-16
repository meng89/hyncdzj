#!/usr/bin/env python3

# Cula Niddesa
# 小义释

import os


import load_from_p5a


xmls = [
    "N/N47/N47n0023.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_niddesa"))

if __name__ == "__main__":
    main()
