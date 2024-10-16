#!/usr/bin/env python3

# Maha Niddesa
# 大义释

import os


import load_from_p5a


xmls = [
    "N/N45/N45n0022.xml",
    "N/N46/N46n0022.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_niddesa"))

if __name__ == "__main__":
    main()
