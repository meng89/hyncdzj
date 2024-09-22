#!/usr/bin/env python3

import re


def match(name):
    return re.match(r"^(\d+.?\d*) *(\S*)$", name)


def filter_fun(name):
    if match(name):
        return True


def split_float(name):
    m = match(name)
    if m:
        return float(m.group(1))
    else:
        return -9


def main():
    import os

    a = os.listdir("/mnt/data/tmp/新建文件夹/")
    a.sort()

    a = list(filter(filter_fun, a))

    a.sort(key=split_float)
    print(a)




if __name__ == "__main__":
    main()
