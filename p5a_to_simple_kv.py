#!/usr/bin/env python3


import os


import load_from_p5a


xmls = [
    "N/N61/N61n0030.xml",
    "N/N62/N62n0030.xml",

]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "sv"))

if __name__ == "__main__":
    main()
