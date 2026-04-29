import re
from pathlib import Path


# High-precision filler prefixes to strip (case-insensitive).
PREFIXES = [
    r"cho\s+em\s+hỏi\s+với",
    r"cho\s+em\s+hỏi",
    r"cho\s+em\s+hoi\s+voi",
    r"cho\s+em\s+hoi",
    r"cho\s+mình\s+hỏi\s+với",
    r"cho\s+mình\s+hỏi",
    r"cho\s+minh\s+hoi\s+voi",
    r"cho\s+minh\s+hoi",
    r"cho\s+minh\s+hỏi\s+với",
    r"cho\s+minh\s+hỏi",
    r"mình\s+muốn\s+hỏi",
    r"minh\s+muon\s+hỏi",
    r"minh\s+muon\s+hoi",
    r"em\s+muốn\s+hỏi",
    r"em\s+muon\s+hỏi",
    r"em\s+muon\s+hoi",
    r"bạn\s+cho\s+mình\s+hỏi",
    r"ban\s+cho\s+minh\s+hỏi",
    r"ban\s+cho\s+minh\s+hoi",
    r"nhờ\s+bạn\s+hỗ\s+trợ",
    r"nho\s+ban\s+ho\s+tro",
    r"xin\s+tư\s+vấn",
    r"xin\s+tu\s+van",
    r"admin\s+cho\s+mình\s+hỏi",
    r"admin\s+cho\s+minh\s+hỏi",
    r"admin\s+cho\s+minh\s+hoi",
]

PREFIX_RE = re.compile(rf"^\s*(?:{'|'.join(PREFIXES)})\s*[:\-–]?\s*", re.IGNORECASE)

# Safe typo fixes (do not "add accents" to no-accent text globally).
TYPO_MAP = {
    "nhéf": "nhé",
    "nhêf": "nhé",
    "đuoc": "được",
    "đươc": "được",
    "đung": "đúng",
}


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def fix_typos(s: str) -> str:
    for k, v in TYPO_MAP.items():
        s = re.sub(rf"\b{re.escape(k)}\b", v, s, flags=re.IGNORECASE)
    return s


def strip_prefix(s: str) -> str:
    return PREFIX_RE.sub("", s).strip()


def is_too_generic(s: str) -> bool:
    generic = {
        "bị lỗi",
        "bi loi",
        "lỗi",
        "loi",
        "không được",
        "khong duoc",
        "ko duoc",
    }
    return normalize_spaces(s).lower() in generic


def has_diacritics(s: str) -> bool:
    return bool(re.search(r"[àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", s.lower()))


def score_example(s: str) -> tuple:
    """
    Higher is better.
    Prefer: contains domain keywords, has Vietnamese diacritics, medium length.
    """
    s_norm = normalize_spaces(s)
    s_low = s_norm.lower()
    keywords = [
        "moodle",
        "login",
        "deadline",
        "quiz",
        "submission",
        "assignment",
        "email",
        "gv",
        "mk",
        "tk",
        "hệ thống",
        "he thong",
    ]
    kw_hits = sum(1 for k in keywords if k in s_low)
    diac = 1 if has_diacritics(s_norm) else 0
    length = len(s_norm)
    return (kw_hits, diac, -abs(length - 40), length)


def parse_rasa_nlu_yaml(text: str):
    """
    Minimal parser for typical Rasa 3.1 NLU YAML:
    version: "3.1"
    nlu:
      - intent: xxx
        examples: |
          - ...
    """
    lines = text.splitlines()
    header = []
    i = 0
    while i < len(lines) and not re.match(r"^nlu:\s*$", lines[i]):
        header.append(lines[i])
        i += 1
    if i >= len(lines):
        raise RuntimeError("Cannot find 'nlu:' root key")
    header.append(lines[i])  # nlu:
    i += 1

    intents = []  # list[(intent, examples)]
    while i < len(lines):
        m = re.match(r"^\s*-\s+intent:\s+([A-Za-z0-9_]+)\s*$", lines[i])
        if not m:
            i += 1
            continue
        intent = m.group(1)
        i += 1
        while i < len(lines) and not re.match(r"^\s*examples:\s*\|\s*$", lines[i]):
            i += 1
        if i >= len(lines):
            break
        i += 1
        examples = []
        while i < len(lines) and not re.match(r"^\s*-\s+intent:\s+", lines[i]):
            line = lines[i].strip()
            if line.startswith("- "):
                examples.append(line[2:])
            i += 1
        intents.append((intent, examples))
    return header, intents


def dump_rasa_nlu_yaml(header, intents):
    out = []
    out.extend(header)
    for intent, examples in intents:
        out.append(f"  - intent: {intent}")
        out.append("    examples: |")
        for ex in examples:
            out.append(f"      - {ex}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def clean_intent_examples(examples, target_max=30):
    # First pass: normalize + strip prefixes + dedup (core only).
    cleaned = []
    seen = set()
    for ex in examples:
        ex = fix_typos(ex)
        ex = normalize_spaces(ex)
        core = strip_prefix(ex)
        core = fix_typos(core)
        core = normalize_spaces(core)
        if not core:
            continue
        if is_too_generic(core):
            continue
        key = core.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(core)

    if len(cleaned) <= target_max:
        return cleaned

    # Second pass: keep the most "informative" samples.
    cleaned = sorted(cleaned, key=score_example, reverse=True)[:target_max]
    return cleaned


def main():
    path = Path("data/nlu.yml")
    text = path.read_text(encoding="utf-8")
    header, intents = parse_rasa_nlu_yaml(text)

    cleaned_intents = []
    for intent, examples in intents:
        cleaned = clean_intent_examples(examples, target_max=30)
        cleaned_intents.append((intent, cleaned))

    new_text = dump_rasa_nlu_yaml(header, cleaned_intents)
    path.write_text(new_text, encoding="utf-8")
    print("Updated data/nlu.yml")


if __name__ == "__main__":
    main()

