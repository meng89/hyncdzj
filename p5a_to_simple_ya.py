#!/usr/bin/env python3


import os


import p5a_to_simple


xmls = [
    "N/N51/N51n0028.xml",
    "N/N52/N52n0028.xml",
    "N/N53/N53n0028.xml",

]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "dt"))

if __name__ == "__main__":
    main()
