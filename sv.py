# 律藏/经分别
import re

import load_public
import base
info = base.Info(1, "經分別", ("通妙", ), "SV")


def change(d: base.Dir):
    pass


def change_name(name):
    m = re.match(r"^(經分別)[一二]", name)
    if m:
        return m.group(1)

    m = re.match(r"(大分別〔比丘戒〕)[一二]", name)
    if m:
        return m.group(1)

    return name


def change_name_(d: base.Dir, change_name_fun):
    new_list = []
    for name, obj in d.list:
        if name in ("", None):
            new_list.append((name, obj))
            continue

        new_name = change_name_fun(name)
        if isinstance(obj, base.Dir):
            change_name_(obj, change_name_fun)
        new_list.append((new_name, obj))

    d.list = new_list


def merge_same_name2(d: base.Dir):
    new_list = []
    for name, obj in d.list:
        if name in ("", None):
            new_list.append((name, obj))
            continue
        v = load_public.ld_get(new_list, name)
        if isinstance(v, base.Dir) and isinstance(obj, base.Dir):
            v.list.extend(obj.list)
            merge_same_name2(v)
        else:
            new_list.append((name, v))
    d.list = new_list