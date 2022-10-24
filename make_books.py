#!/usr/bin/env python3
import os
import tempfile

from book_public import SC, TC

import sn2epub

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

EPUBCHECK = "/mnt/data/software/epubcheck-4.2.6/epubcheck.jar"

BOOKS_DIR = os.path.join(PROJECT_ROOT, "books")


def main():
    # run_abo.make_sure_is_runing()
    # domain = run_abo.get_domain()

    # note_thing.load_global(domain, uc.CACHE_DIR)

    # for xn in "sn", "mn", "dn", "an":
    #    nikayas.load(xn, domain, uc.CACHE_DIR)

    temprootdir_td = tempfile.TemporaryDirectory(prefix="ncdzj_")

    def print_temprootdir():
        print("temprootdir: {}".format(temprootdir_td.name))

    # books_dir = os.path.join(uc.PROJECT_ROOT, "books", time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime()))

    os.makedirs(BOOKS_DIR, exist_ok=True)

    print_temprootdir()

    for xc in (SC(), TC()):
        sn2epub.make(xc, temprootdir_td.name, BOOKS_DIR, EPUBCHECK)
    #    mn2epub.make(xc, temprootdir_td.name, BOOKS_DIR, uc.EPUBCHECK)
    #    dn2epub.make(xc, temprootdir_td.name, BOOKS_DIR, uc.EPUBCHECK)
    #    an2epub.make(xc, temprootdir_td.name, BOOKS_DIR, uc.EPUBCHECK)

    while input("input e and press enter to exit:").rstrip() != "e":
        pass


if __name__ == "__main__":
    main()
