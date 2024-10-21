# 律藏/经分别
import re

import load_public
import base
info = base.Info(1, "經分別", ("通妙", ), "SV")

def change_name(name):
    m = re.match(r"^(經分別)[一二]", name)
    if m:
        return m.group(1)

    m = re.match(r"(大分別〔比丘戒〕)[一二]", name)
    if m:
        return m.group(1)

    return name


def merge_same_name(d: base.Dir, change_name_fun):
    new_list = []
    for name, obj in d.list:
        if name in ("", None):
            new_list.append((name, obj))
            continue

        new_name = change_name_fun(name)
        v = load_public.ld_get(new_list, name)
        if v:
            v.list.extend(obj)
        else:
            new_list.append((new_name, ))