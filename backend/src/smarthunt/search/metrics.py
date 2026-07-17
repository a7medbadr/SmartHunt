search_counter = 0


def increment():
    global search_counter
    search_counter += 1


def total():
    return search_counter
