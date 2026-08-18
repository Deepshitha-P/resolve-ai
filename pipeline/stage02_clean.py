import re
from typing import List, Dict

URL_RE = re.compile(r"http\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
MULTISPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9\s.,!?']")

CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "n't": " not",
    "i'm": "i am", "it's": "it is", "didn't": "did not",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    t = text.lower()
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    t = HASHTAG_RE.sub(r"\1", t)
    for k, v in CONTRACTIONS.items():
        t = t.replace(k, v)
    t = NON_ALNUM_RE.sub(" ", t)
    t = MULTISPACE_RE.sub(" ", t).strip()
    return t


def clean_batch(rows: List[Dict]) -> List[Dict]:
    for r in rows:
        if not r.get("clean_text"):
            raw = r.get("raw_text") or r.get("text") or ""
            r["clean_text"] = clean_text(raw)
    return rows


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    data = clean_batch(generate_raw_complaints(5))
    for d in data:
        print(d["raw_text"], "->", d["clean_text"])
