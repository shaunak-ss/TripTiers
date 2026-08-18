from __future__ import annotations

import re

_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_ORDINAL_ONES = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
    7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth",
    13: "thirteenth", 14: "fourteenth", 15: "fifteenth", 16: "sixteenth",
    17: "seventeenth", 18: "eighteenth", 19: "nineteenth",
}
_ORDINAL_TENS = {
    2: "twentieth", 3: "thirtieth", 4: "fortieth", 5: "fiftieth",
    6: "sixtieth", 7: "seventieth", 8: "eightieth", 9: "ninetieth",
}


def cardinal_word(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, rem = divmod(n, 10)
    return _TENS[tens] + ("-" + _ONES[rem] if rem else "")


def ordinal_word(n: int) -> str:
    if n in _ORDINAL_ONES:
        return _ORDINAL_ONES[n]
    tens, rem = divmod(n, 10)
    if rem == 0:
        return _ORDINAL_TENS[tens]
    return _TENS[tens] + "-" + _ORDINAL_ONES[rem]


def build_word_number_map(max_n: int, *, include_ordinals: bool = False) -> dict[str, str]:
    """Maps spelled-out number words ("twenty-five", "twenty five", and optionally
    "twenty-fifth") to their digit string, for 1..max_n."""
    mapping: dict[str, str] = {}
    for n in range(1, max_n + 1):
        words = [cardinal_word(n)]
        if include_ordinals:
            words.append(ordinal_word(n))
        for word in words:
            if not word:
                continue
            mapping[word] = str(n)
            mapping[word.replace("-", " ")] = str(n)
    return mapping


def build_word_number_pattern(mapping: dict[str, str]) -> re.Pattern[str]:
    """Longest-phrase-first alternation so multi-word numbers ("twenty five") match
    before their component words ("five") would."""
    return re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in sorted(mapping, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )


def spell_out_numbers(text: str, mapping: dict[str, str], pattern: re.Pattern[str]) -> str:
    """Replaces spelled-out number words in `text` with their digit equivalents.

    Number-parsing libraries and regexes generally understand digits but either
    reject or (worse) silently mis-handle spelled-out words ("three", "twenty-five").
    Converting up front avoids confidently-wrong results downstream."""
    return pattern.sub(lambda m: mapping[m.group(0).lower()], text)
