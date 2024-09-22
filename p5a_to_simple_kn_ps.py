#!/usr/bin/env python3

# 无碍解道

import os


import p5a_to_simple


xmls = [
    "N/N43/N43n0019.xml",
    "N/N44/N44n0019.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_ps"))

if __name__ == "__main__":
    main()
