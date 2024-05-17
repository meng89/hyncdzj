import xl


def trans(element):
    return [], []


# pass
def head(e):
    if isinstance(e, xl.Element) and e.tag == "head":
        return [], []
    else:
        raise TypeError


def string(e):
    if isinstance(e, str):
        return [], [e]
    else:
        raise TypeError


def note(e):
    if isinstance(e, xl.Element) and e.tag == "note"