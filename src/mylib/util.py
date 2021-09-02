"""
General utilities.
"""

import re
from typing import List
import unicodedata


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

re_slug1 = re.compile(r'[^.\w\s-]')
re_slug2 = re.compile(r'[-\s]+')

def make_slug(value: str) -> str:
    """
    Normalize a string for use as a slug, such as for filename.
    """
    value = unicodedata.normalize('NFKD', value)\
        .encode('ascii', 'ignore')\
        .decode('ascii')\
        .lower()
    value = re_slug1.sub('', value)
    return re_slug2.sub('-', value).strip('-_')
