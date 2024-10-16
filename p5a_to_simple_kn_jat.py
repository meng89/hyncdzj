#!/usr/bin/env python3

# Jātaka
# 本生

import os


import load_from_p5a


xmls = [
    "N/N31/N31n0018.xml",
    "N/N32/N32n0018.xml",
    "N/N33/N33n0018.xml",
    "N/N34/N34n0018.xml",
    "N/N35/N35n0018.xml",
    "N/N36/N36n0018.xml",
    "N/N37/N37n0018.xml",
    "N/N38/N38n0018.xml",
    "N/N39/N39n0018.xml",
    "N/N40/N40n0018.xml",
    "N/N41/N41n0018.xml",
    "N/N42/N42n0018.xml",
]


def main():
    book = p5a_to_simple.load_from_p5a(xmls)
    import tempfile

    print(tempfile.gettempdir())
    book.write(os.path.join(tempfile.gettempdir(), "kn_thig"))

if __name__ == "__main__":
    main()
