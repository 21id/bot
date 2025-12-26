from itertools import batched


def message_split(text: str, type_: str, uuid_: str,
                  max_size: int = 4098) -> list[str]:
    """Split message into batches with UUID, data type and data itself."""

    # Subtracting UUID, type length and 2 whitespaces
    part_size = max_size - (len(uuid_) + len(type_) + 2)
    results = []

    for line in batched(text, part_size):
        line = "".join(line)
        formatted_line = f"{uuid_} {type_} {line}"
        results.append(formatted_line)

    return results
