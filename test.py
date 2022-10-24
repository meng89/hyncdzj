#!/usr/bin/env python3
import os

cover_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cover_images")

print(os.path.dirname(os.path.abspath(__file__)))
print(cover_dir)