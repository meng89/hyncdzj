#!/usr/bin/env python3

# Parivāra
# 附隨

import os


import p5a_to_simple


xmls = [
    "N/N05/N05n0003.xml"
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "sv"))

if __name__ == "__main__":
    main()
