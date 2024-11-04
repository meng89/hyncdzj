import base
import make_ebooks

import kn_khp as khp
import kn_dhp as dhp
import kn_ud as ud
import kn_iti as iti
import kn_snp as sn
import kn_vv as vv
import kn_pv as pv
import kn_thag as thag
import kn_thig as thig
import kn_ap as ap
import kn_jat as jat
import kn_ps as ps
import kn_bv as bv
import kn_cp as cp
import kn_nid1 as nid1
import kn_nid2 as nid2

_ms = (khp, dhp, ud, iti, sn, vv, pv, thag, thig, ap, jat, ps, bv, cp, nid1, nid2)
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

