import re

def trim_text(
    text,
    max_length=4000
):

    if len(text) <= max_length:

        return text

    return text[:max_length] + "..."


def normalize_space(
    text
):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()