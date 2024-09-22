#!/usr/bin/env python3

# Khandhaka
# 犍度

import os


import p5a_to_simple


xmls = [
    "N/N03/N03n0002.xml",
    "N/N04/N04n0002.xml"
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "sv"))

if __name__ == "__main__":
    main()
