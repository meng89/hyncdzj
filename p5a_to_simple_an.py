#!/usr/bin/env python3


import os


import p5a_to_simple


xmls = [
    "N/N19/N19n0007.xml",
    "N/N20/N20n0007.xml",
    "N/N21/N21n0007.xml",
    "N/N22/N22n0007.xml",
    "N/N23/N23n0007.xml",
    "N/N24/N24n0007.xml",
    "N/N25/N25n0007.xml"
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "an"))

if __name__ == "__main__":
    main()
