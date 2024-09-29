import re

import base

info = (6, "相應部", ("通妙", "雲庵"), "SN")



def ld_get(list_dict, key):
    for k, v in list_dict:
        if k == key:
            return v


# 原始 p5a 转换成的 simple, 调用此函数处理一下
def change(book:base.Dir):
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
    return book

#处理过后的
def change2(book_div):
    return book_div


def write2pdf(book_div):
    pass

def write2epub(book_div):
    pass
