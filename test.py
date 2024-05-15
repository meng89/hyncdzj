#!/usr/bin/env python3
import os

import re

filename = "sn 1.22 保留"


m = re.match(r"^([a-zA-Z]+) (\d+(?:\.\d+)?) (\S+)$", filename)
if m:
    print(m.group(1), m.group(2), m.group(3))


