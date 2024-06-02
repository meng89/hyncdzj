#!/usr/bin/env python3
import os


class A(object):
    pass


class B(A):
    pass


b = B()

print(type(b) is type(B))
