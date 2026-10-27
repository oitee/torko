"""The sentence rules for a quote: one sentence that a lay reader can read with no context.

The rules are in the docstring of pages/today.py ("Quote rule"). The page "On this day" and the speech rows of the Tag page use them.
"""
import re

BACK_REF = {w.lower() for w in """This That These Those It Its He She They His Her Their Them Such However But And So Thus Hence
Therefore Moreover Also Now Then Because Which Who Whereas Yes No Further Besides Similarly Secondly Firstly Thirdly
Again Otherwise Still Yet Or Nor There Here What Why How When While Even Both Either Neither Some Many Most
Another Other One Hon Honourable Madam Sir Mr""".split()}
BAD = re.compile(r"\b(sir|madam|hon(?=\.)|hon'ble|honourable|speaker|chair|clause|annexure|question no|the said|aforesaid|"
                 r"they|them|their|he|she|his|her|these|those|above|in the same|in this regard|in that|in this|mentioned earlier|as i said|as i have said|thank you|point of order|yield)\b", re.I)
HI_BACK = {w for w in """यह वह ये वे और तथा एवं लेकिन परंतु परन्तु किंतु किन्तु अतः इसलिए इसीलिए इसके इसमें इसी उसके उसमें उसी इस उस
इन उन जो जिस जिन तो भी फिर अब तब क्योंकि क्योकि जबकि हालांकि साथ ही यहां वहां कि""".split()}
# Pronouns and addresses that need the context. The check is by whole word, because \\b does not work with Devanagari marks.
HI_BAD_WORDS = set("""वह वे यह ये उन इन उनके उनकी उनका इनके इनकी इनका इस उस उसे इसे उसका उसकी उसके इसका इसकी इसके उन्हें इन्हें
ऊपर उपरोक्त उन्होंने इन्होंने उसने इसने""".split())
HI_BAD_PARTS = ("माननीय", "महोदय", "महोदया", "अध्यक्ष", "सभापति", "धन्यवाद", "स्थगित", "कार्यवाही")
DEVA = re.compile(r"[\u0900-\u097F]")
ABBR = {"mr", "mrs", "dr", "shri", "smt", "no", "rs", "st", "sh", "prof", "hon", "vs", "etc", "ltd", "govt", "sr", "jr"}


def clean(t):
    t = re.sub(r"</?(ins|del|b|i|u|span|p|br)[^>]*>", " ", t)
    t = re.sub(r"\[[a-z]\d+\]", " ", t)                       # editor markers such as [r11]
    t = re.sub(r"\(\s*l\d+/[^)]*\)?", " ", t)                  # layout markers such as (l1/1150
    t = re.sub(r"^\s*(\([^)]{0,60}\))?\s*:\s*", "", t)         # leading "(Seat):" label
    t = re.sub(r"[…]+\s*\(\s*[A-Za-z ]+\)", " ", t)            # stage notes such as ( Interruptions )
    t = re.sub(r"\(\s*[A-Za-z ]*Interruptions?\s*\)", " ", t)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n+", "\n", t)).strip()


def sentences(t):
    out, buf = [], ""
    # A Latin "l" right after a Devanagari letter is a broken danda. Read it as a sentence end.
    t = re.sub(r"(?<=[\u0900-\u097F])\s*\bl\b(?=\s|$)", "।", t)
    for part in re.split(r"(?<=[.?!।])\s+", t.replace("\n", " ")):
        buf = f"{buf} {part}".strip()
        last = buf.rstrip(".?!").split(" ")[-1].lower()
        if last in ABBR or len(last) == 1:
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return out


def english(s):
    letters = [ch for ch in s if ch.isalpha()]
    return bool(letters) and sum(ch.isascii() for ch in letters) / len(letters) >= 0.95


def good(s):
    words = s.split()
    if not 12 <= len(words) <= 40 or not s.endswith(".") or not s[0].isupper() or not english(s):
        return False
    if words[0].strip(",").lower() in BACK_REF or BAD.search(s):
        return False
    return not re.search(r"[()\[\]<>\"“”…\d?]", s)


def hindi(s):
    letters = [ch for ch in s if ch.isalpha()]
    return bool(letters) and sum(bool(DEVA.match(ch)) for ch in letters) / len(letters) >= 0.95


def good_hi(s):
    words = s.split()
    if not 10 <= len(words) <= 40 or s[-1] not in "।.?" or not hindi(s):
        return False
    plain = [w.strip(",।.?!;:-–") for w in words]
    if plain[0] in HI_BACK or HI_BAD_WORDS & set(plain) or any(p in s for p in HI_BAD_PARTS):
        return False
    return not re.search(r"[()\[\]<>\"“”…\d\u0966-\u096F*_/]", s) and not re.search(r"[A-Za-z]", s)


def score(s, title_words):
    n = len(s.split())
    sw = {w.lower().strip(",.") for w in s.split()}
    return min(2, len(sw & title_words)) + (2 if 15 <= n <= 28 else 0)
