import hashlib, re
from pathlib import PurePosixPath

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["\'][^"\']{12,}["\']', 'Possible hard-coded credential'),
    (r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----', 'Private key material marker'),
    (r'(?i)\bmnemonic\b.{0,40}\b(seed phrase|recovery phrase)\b', 'Possible wallet recovery phrase reference')
]
PROMPT_INJECTION = [r'(?i)ignore (all )?(previous|prior) instructions', r'(?i)reveal (the )?(system prompt|secrets)', r'(?i)send (the )?(api key|token|secret)']


def classify(text, config):
    low = text.lower()
    scores = {}
    for cat, terms in config['categories'].items():
        scores[cat] = sum(1 for t in terms if t in low)
    return max(scores, key=scores.get) if max(scores.values(), default=0) else 'general'


def inspect_text(text):
    notes=[]
    for pat,msg in SECRET_PATTERNS:
        if re.search(pat,text): notes.append(msg)
    for pat in PROMPT_INJECTION:
        if re.search(pat,text): notes.append('Possible prompt-injection text; treat as untrusted data')
    return '; '.join(sorted(set(notes)))


def digest(data): return hashlib.sha256(data).hexdigest()

def safe_path(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts
