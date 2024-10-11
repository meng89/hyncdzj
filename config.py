# 如果只是想自己制作电子书而不是开发此程序的话，需复制这个文件为 user_config.py，再修改复制后的文件。
import sys
import os.path

sys.path.append("/mnt/data/projects/xl")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# EPUBCheck 路径
EPUBCHECK = "/mnt/data/software/epubcheck-4.2.6/epubcheck.jar"
# EPUBCHECK = r"D:\epubcheck-4.2.6\epubcheck.jar"

# 电子书存放目录
BOOKS_DIR = os.path.join(PROJECT_ROOT, "_books")

# xmlp5_dir = os.path.join(PROJECT_ROOT, "~/projects/xml-p5a")
XMLP5A_DIR = "/mnt/data/projects/xml-p5a/"

_SOURCES = os.path.join(os.path.join(PROJECT_ROOT, "simple_sources"))
SIMPLE_DIR = os.path.join(_SOURCES, "ncdzj")
os.makedirs(SIMPLE_DIR, exist_ok=True)

OVERLAYS_DIR = os.path.join(_SOURCES, "overlays")
os.makedirs(OVERLAYS_DIR, exist_ok=True)
