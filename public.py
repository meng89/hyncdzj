import uuid

import epubpacker

import opencc
import abc

# TC = "tc"
# SC = "sc"


def do_nothing(x):
    return x


_table = [
    ("「", "“"),
    ("」", "”"),
    ("『", "‘"),
    ("』", "’"),
]


def convert2sc(s):
    if s:
        converter = opencc.OpenCC('tw2sp.json')
        return converter.convert(s)
    else:
        return s


def convert_all(s):
    new_sc_s = ""
    for c in convert2sc(s):
        new_sc_s += _convert_punctuation(c)
    return new_sc_s


def _convert_punctuation(c):
    for tp, sp in _table:
        if tp == c:
            return sp
    return c


class XC(object):
    @property
    @abc.abstractmethod
    def c(self):
        pass

    @property
    @abc.abstractmethod
    def xmlang(self):
        pass

    @property
    @abc.abstractmethod
    def zhlang(self):
        pass

    @property
    @abc.abstractmethod
    def enlang(self):
        pass

    @property
    @abc.abstractmethod
    def han_version(self):
        pass


class TC(XC):
    @property
    def c(self):
        return do_nothing

    @property
    def xmlang(self):
        return "zh-Hant"

    @property
    def zhlang(self):
        return "繁"

    @property
    def enlang(self):
        return "tc"

    @property
    def han_version(self):
        return "傳統中文版"


class SC(XC):
    @property
    def c(self):
        return convert2sc

    @property
    def xmlang(self):
        return "zh-Hans"

    @property
    def zhlang(self):
        return "简"

    @property
    def enlang(self):
        return "sc"

    @property
    def han_version(self):
        return "机转简体版"


def get_uuid(s):
    return uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meng89/ncdzj" + " " + s)


def create_epub(nikaya, xc: book_public.XC):
    epub = epubpacker.Epub()

    epub.meta.titles = [xc.c(nikaya.title_hant)]
    epub.meta.creators = ["元亨寺 ".format(xc.c("譯"))]
    epub.meta.date = nikaya.last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    epub.meta.languages = [xc.xmlang, "pi", "en-US"]

    my_uuid = get_uuid(xc.c(nikaya.title_hant) + xc.enlang)
    epub.meta.identifier = my_uuid.urn

    epub.meta.others.append(xl.Element("meta", {"property": "belongs-to-collection", "id": "c01"},
                                       ["莊春江" + xc.c("漢譯經藏")]))
    epub.meta.others.append(xl.Element("meta", {"refines": "#c01", "property": "collection-type"}, ["series"]))

    epub.userfiles[css.css1_path] = css.css1[xc.enlang]
    epub.userfiles[css.css2_path] = css.css2[xc.enlang]
    epub.userfiles[js.js1_path] = js.js1
    epub.userfiles["_css/user_css1.css"] = "/* 第一个自定义 CSS 文件 */\n\n"
    epub.userfiles["_css/user_css2.css"] = "/* 第二个自定义 CSS 文件 */\n\n"
    epub.userfiles["_js/user_js1.js"] = "// 第一个自定义 JS 文件\n\n"
    epub.userfiles["_js/user_js2.js"] = "// 第二个自定义 JS 文件\n\n"

    return epub

