import base


xmls = [
    "N/N02/N02n0001.xml",
    "N/N02/N02n0001.xml"
]


class SV(base.Book):
    def __init__(self):
        super(SV, self).__init__()
        self._abbr = "SV"
        self._name_pali = "Suttavibhaṅga"
        self._name_hant = "經分別"


_book = None


def get_book():
    global _book
    if _book:
        return _book

    book = SV()
    base.make_nikaya(book, xmls)

    base.change_dirname(book, 1, change_pian_mulu_fun)
    base.change_dirname(book, 2, change_pin_mulu_fun)

    base.merge_terms(book)

    _book = book
    return _book
