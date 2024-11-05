from . import sv, pv, kd

lv = ("律藏", (sv, kd, pv))

from . import dn, mn, sn, an, kn
jing = ("經藏", (dn, mn, sn, an, kn))

from . import ds, vb, dt, pp, ya, patthana, kv
lun = ("論藏", (ds, vb, dt, pp, ya, patthana, kv))

from . import mil, dipavamsa, mahavamsa, culavamsa, visuddhimagga, samantapasadika, abhidhammatthasangaha, dhammalipi
zangwai = ("藏外", (mil, dipavamsa, mahavamsa, culavamsa, visuddhimagga, samantapasadika, abhidhammatthasangaha, dhammalipi))

categories = (lv, jing, lun, zangwai)