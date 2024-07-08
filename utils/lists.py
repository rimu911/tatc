def strip(values: list[str], remove_blank: bool = False, remove_duplicates: bool = False) -> list[str]:
    new_values = [v.strip() for v in values]
    if remove_blank:
        new_values = filter(lambda x: bool(x), values)
    return list(set(new_values)) if remove_duplicates else new_values


def split(values: list, size: int = 0):
    if not size:
        return values
    for i in range(0, len(values), size):
        yield values[i:i+size]
