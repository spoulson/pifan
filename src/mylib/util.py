"""
General utilities.
"""

import re
from typing import List
import unicodedata


RE_SLUG1 = re.compile(r'[^.\w\s-]')
RE_SLUG2 = re.compile(r'[-\s]+')


def parse_pdv(text: str) -> List[List[str]]:
    """
    Parse pipe delimited values.
    """
    rows = []
    lines = text.split('\n')

    for line in lines:
        row = []
        cols = line.split('|')

        for col in cols:
            col2 = col.strip()
            row.append(col2)

        rows.append(row)

    return rows


def parse_hex(text: str) -> int:
    """
    Parse hex string in either 0xnn or nnh formats.
    https://stackoverflow.com/a/604244/3347
    """
    text = text.rstrip('h')
    if not text.startswith('0x'):
        text = '0x' + text
    return int(text, 0)


def make_slug(value: str) -> str:
    """
    Normalize a string for use as a slug, such as for filename.
    """
    value = unicodedata.normalize('NFKD', value)\
        .encode('ascii', 'ignore')\
        .decode('ascii')\
        .lower()
    value = RE_SLUG1.sub('', value)
    return RE_SLUG2.sub('-', value).strip('-_')
