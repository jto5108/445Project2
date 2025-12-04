import re
from typing import List, Tuple
import nltk

# Ensure NLTK punkt exists
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

WORD_RE = re.compile(r"\b[a-zA-Z0-9']+\b")

def normalize_text(text: str) -> str:
    return text.lower() if text else ""

def extract_keywords_from_text(text: str) -> List[str]:
    """
    Very simple keyword extractor: return lowercased words (excluding common stopwords if desired).
    This is used for simple title similarity heuristics.
    """
    if not text:
        return []
    text = normalize_text(text)
    tokens = WORD_RE.findall(text)
    # filter short tokens
    return [t for t in tokens if len(t) > 2]

def analyze_comments_keywords(comments: List[str], keywords: List[str]) -> Tuple[float, list]:
    """
    Returns (flag_rate, examples_list). flag_rate is fraction of comments containing >=1 keyword.
    examples_list contains up to 6 example comments that matched.
    """
    if not comments:
        return 0.0, []
    kws = [k.lower() for k in keywords]
    flagged = []
    for c in comments:
        cl = c.lower()
        for k in kws:
            if k in cl:
                flagged.append(c)
                break
    rate = len(flagged) / len(comments)
    # return a few examples truncated
    examples = [e if len(e) <= 300 else e[:300] + "..." for e in flagged[:6]]
    return rate, examples
