# قائمة/كائن حفظ السجل المؤقت
_history = []


def all():
    return _history


def add(item):
    _history.append(item)


def clear():
    _history.clear()
