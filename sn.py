import re

import cn2an

import base

info = base.Info(6, "相應部", ("通妙", "雲庵"), "SN")



def ld_get(list_dict, key):
    for k, v in list_dict:
        if k == key:
            return v


# 原始 p5a 转换成的 simple, 调用此函数处理一下
def change(book:base.Dir):

    # 合并上下部，剪除所包含的相应的序号
    new_list = []
    for name, obj in book.list:
        m = re.match(r"(\S+篇)", name)
        key = m.group(1)
        v = ld_get(new_list, key)
        if v:
            v.list.extend(obj.list)
        else:
            new_list.append((key, obj))

    book.list = new_list

    xy_seril_map = []
    doc_seril_map = []

    change_name(book, 1, xy_seril_map, doc_seril_map)

    change_j_name(xy_seril_map, book, doc_seril_map)

    return book


def change_name(d: base.Dir, xy_index, xy_seril_map: list, j_seril_map: list):
    new_list = []
    for name, obj in d.list:
        #print(repr(name))
        if isinstance(obj, base.Dir):
            xy_index = change_name(obj, xy_index, xy_seril_map, j_seril_map)

        if name == "":
            new_name = name
        elif name.endswith("篇"):
            new_name = name
        else:
            m = re.match(r"^第[一二三四五六七八九十〇]+　(\S+)$", name)
            if m:
                new_name = m.group(1)
                if new_name.endswith("相應"):
                    xy_seril_map.append((obj, xy_index))
                    new_name = str(xy_index) + " " + new_name
                    xy_index += 1
            elif re.match("〔[一二三四五六七八九十〇～、]+〕", name):

                # '〔一〕瀑流'
                m = re.match(r"^〔([一二三四五六七八九十〇]+)〕　?(\S+)?$", name)
                if m:
                    #print(repr(m.group(1)), repr(m.group(2)))
                    start = end = cn2an.cn2an(m.group(1), "normal")
                    new_name = m.group(2) or ""
                    j_seril_map.append((obj, start, end))
                else:
                    # '〔二一〕第一\u3000依劍'
                    # '〔一六八〕第四、五、六\u3000欲念（四、五、六）'
                    # '〔一七四〕第廿二～廿四\u3000過去（四～六）'
                    # '〔三〕第三\u3000舍利弗——拘絺羅\u3000第一（住者）'
                    m = re.match(r"^〔([一二三四五六七八九十〇]+)〕"
                                 r"第[一二三四五六七八九十〇、～廿卅]+　?(.+)?$", name)
                    if m:
                        #print(repr(m.group(1)), repr(m.group(2)))
                        start = end = cn2an.cn2an(m.group(1), "normal")
                        new_name = m.group(2) or ""
                        j_seril_map.append((obj, start, end))
                    else:
                        #'〔七二～八〇〕第二～第十\u3000不知（之一）'
                        #'〔二五～二六〕第三～四\u3000無常（一～二）'
                        #'〔一一～二〇〕第十一\u3000布施利益（一）'
                        #'〔五六、五七〕第四、第五\u3000諸漏（一～二）'
                        m = m = re.match(r"^〔([一二三四五六七八九十〇]+)[～、]([一二三四五六七八九十〇]+)〕"
                                         r"[第一二三四五六七八九十〇～、]+　?(\S+)?$", name)
                                         # r"第[一二三四五六七八九十〇]+～第?[一二三四五六七八九十〇]+　?(\S+)?$", name)
                        if m:
                            start = cn2an.cn2an(m.group(1), "normal")
                            end = cn2an.cn2an(m.group(2), "normal")
                            new_name = m.group(3) or ""
                            j_seril_map.append((obj, start, end))
                        else:
                            if name == "〔三八～四三〕第八　父、第九　兄弟、第十　姊妹、第十一　子、第十二　女、第十三　妻":
                                start = 38
                                end = 43
                                new_name = "父、兄弟、姊妹、子、女、妻"
                                j_seril_map.append((obj, start, end))
                            else:
                                raise Exception(repr(name))
            else:
                if "〔" in name:
                    # print(repr(name))
                    pass
                new_name = name

        new_list.append((new_name, obj))

    d.list = new_list
    return xy_index


def change_j_name(xy_seril_map: list, d: base.Dir, j_seril_map: list):
    new_list = []
    for name, obj in d.list:
        result = find_j_range(obj, j_seril_map)
        if result is not None:
            start, end = result
            xy_index = find_xy_index(xy_seril_map, obj)
            new_name = "SN {}.{}".format(xy_index, start)
            if end != start:
                new_name = new_name + "~" + str(end)
            new_name += " " + name
            new_list.append((new_name, obj))
        else:
            new_list.append((name, obj))

        if isinstance(obj, base.Dir):
            change_j_name(xy_seril_map, obj, j_seril_map)
    d.list = new_list


def find_j_range(obj, j_seril_map):
    for j_obj, start, end in j_seril_map:
        if j_obj == obj:
            return start, end
    return None

def find_xy_index(xy_seril_map, obj):
    for xy, index in xy_seril_map:
        if is_contain(xy, obj):
            return index
    assert Exception

def is_contain(obj: base.Dir, j: base.Dir):
    for name, x in obj.list:
        if x == j:
            return True
        elif isinstance(x, base.Dir):
            result = is_contain(x, j)
            if result is True:
                return True
            else:
                continue
    return False


def add_range_to_name(branch, d: base.Dir):
    new_list = []
    for name, obj in d.list:
        if not isinstance(obj, base.Dir):
            new_list.append((name, obj))
            continue

        new_branch = branch.append(name, obj)
        new_obj = add_range_to_name(new_branch, obj)

        obj_type = _type(branch, name)
        if  obj_type == "PIAN":
            xy_min, xy_max = get_xy_serial(obj)
            new_name = "{}({}～{})".format(name, xy_min, xy_max)
        elif obj_type == "PIN":
            jing_min, jing_max = get_jing_serial(obj)
            new_name = "{}({}～{})".format(name, jing_min, jing_max)
        else:
            new_name = name

        new_list.append((new_name, new_obj))
    d.list = new_list
    return d


def _type(branch, name):
    types = [_type2(s) for s in branch]
    my_type = _type2(name)

    if my_type == "PIAN" and "PIAN" not in types:
        return "PIAN"
    elif my_type == "XY" and "PIAN" in types and "XY" not in types:
        return "XY"
    elif my_type == "JING" and "PIAN" in types and "XY" in types and "JING" not in types:
        return "JING"
    elif my_type is None and "PIAN" in types and "XY" in types and "JING" not in types:
        return "PIN"
    elif my_type is None and "PIAN" in types and "XY" in types and "JING" in types:
        return "SUB"

def _type2(name):
    if name.endswith("篇"):
        return "PIAN"
    elif re.match(r"^\d+ \S+相應$", name):
        return "XY"
    elif re.match(r"^SN \d+", name):
        return "JING"
    else:
        return None

def get_xy_serial(d: base.Dir):
    serials = []
    for name, obj in d.list:
        m = re.match(r"^(\d+) \S+相應$", name)
        if m:
            serials.append(int(m.group(1)))
        if isinstance(obj, base.Dir):
            serials.extend(get_xy_serial(obj))
    return min(serials), max(serials)


def get_jing_serial(d: base.Dir):
    serials = []
    for name, obj in d.list:
        m = re.match(r"^SN \d+\.(\d+)(?:～(\d+))?", name)
        serials.append(int(m.group(1)))
        if m.group(m.group(2)):
            serials.append(int(m.group(2)))

        if isinstance(obj, base.Dir):
            serials.extend(get_jing_serial(obj))
    return min(serials), max(serials)


def add_range_xiangying(name, d: base.Dir):
    for name, obj in d.list:
        if isinstance(obj, base.Dir) and is_pin_kind(name, obj):


def add_range_pin_kind(d: base.Dir):
    pass

def is_pian(name, _obj):
    return name.endswith("篇")



def has_xiangying(d):
    for name, obj in d.list:
        if re.match("^\d+ \S+相應$", name):
            return True
        if isinstance(obj, base.Dir):
            if has_xiangying(d) is True:
                return True
    return False


def get_xiangying_serial(name):
    serials = []
    m = re.match("^\d+ \S+相應$", name)
    return int(m.group(1))



def is_pin_kind(name, obj) -> bool:
    pass

def get_pin_name(name, obj):
    pass

def get_sutta_range(d):
    serials = []
    for name, obj in d.list:
        m = re.match("^[a-zA-z]+ (\d+)(?:\.(\d+))? ", name)
        if m:
            serials.append(int(m.group(1)))
            if m.group(2):
                serials.append(int(m.group(2)))
        else:
            if isinstance(obj, base.Dir):
                serials.extend(get_sutta_range(d))
    return min(serials), max(serials)


def merge(d:base.Dir):
    pass
