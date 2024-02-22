#!/usr/bin/env python3
import os

import re

filename = "sn 1.2.3.4 保留"
m = re.match(r"^([a-z]+) (\d(?:\.\d)*) (.*)$", filename)

if m:
    print(m.groups())
