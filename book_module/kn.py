import base
import make_ebooks

from . import kn_khp, kn_dhp, kn_ud, kn_iti, kn_snp, kn_vv, kn_pv, kn_thag, kn_thig, kn_ap, kn_jat, kn_ps, kn_bv, kn_cp, kn_nid1, kn_nid2

_ms = (kn_khp, kn_dhp, kn_ud, kn_iti, kn_snp, kn_vv, kn_pv, kn_thag, kn_thig, kn_ap, kn_jat, kn_ps, kn_bv, kn_cp, kn_nid1, kn_nid2)
author_set = set()
for _m in _ms:
    author_set.update(_m.info.translators)

info = base.Info(None, "小部", tuple(author_set), "KN")


def get_book():
    d = base.Dir()
    for m in _ms:
        book = make_ebooks.load_book_from_dir(m)
        d.list.append((m.info.name, book))
    return d
