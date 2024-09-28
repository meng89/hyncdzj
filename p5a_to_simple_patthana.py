#!/usr/bin/env python3


import os


import p5a_to_simple


xmls = [
    "N/N54/N54n0029.xml",
    "N/N55/N55n0029.xml",
    "N/N56/N56n0029.xml",
    "N/N57/N57n0029.xml",
    "N/N58/N58n0029.xml",
    "N/N59/N59n0029.xml",
    "N/N60/N60n0029.xml",
    
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "dt"))

if __name__ == "__main__":
    main()
