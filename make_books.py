#!/usr/bin/env python3
import os
import tempfile

from book_public import SC, TC

import sn2epub


try:
    import user_config as uc
except ImportError:
    import _user_config as uc


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
    books_dir = uc.BOOKS_DIR
    os.makedirs(books_dir, exist_ok=True)

    print_temprootdir()

    sn2epub.make(temprootdir_td.name, books_dir)

    for xc in (SC(), TC()):
        sn2epub.make(xc, temprootdir_td.name, books_dir, uc.EPUBCHECK)
    #    mn2epub.make(xc, temprootdir_td.name, books_dir, uc.EPUBCHECK)
    #    dn2epub.make(xc, temprootdir_td.name, books_dir, uc.EPUBCHECK)
    #    an2epub.make(xc, temprootdir_td.name, books_dir, uc.EPUBCHECK)

    while input("input e and press enter to exit:").rstrip() != "e":
        pass


if __name__ == "__main__":
    main()
