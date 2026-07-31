import math


class SearchResult:
    def __init__(self, items, total, page, limit):
        self.items = items
        self.total = total
        self.page = page
        self.limit = limit
        self.pages = math.ceil(total / limit) if limit > 0 else 1
