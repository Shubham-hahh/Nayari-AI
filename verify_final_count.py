import re, json, os
from pathlib import Path

DATASET_DIR = Path("dataset")

def _inject_scene_ends(text: str) -> str:
    return re.sub(r"(\r?\n){3,}", "\n--- END ---\n", text)

SPEAKER_RE = re.compile(
    r"""^
    (?:\*{1,2}|\[|>\s*)?          # optional: ** or [ or >
    ([A-Za-z][A-Za-z0-9 _\'\-]*)   # speaker name
    (?:\*{1,2}|\])?                 # optional closing ** or ]
    :\s*(.*)                         # colon + rest of line
    $""",
    re.VERBOSE,
)

END_RE = re.compile(
    r"^[-=*]{3,}\s*(<?(end|END|break|BREAK|scene|SCENE)>?)?\s*[-=*]{0,}$"
)

def parse_chat_text(text: str):
    text = _inject_scene_ends(text)
    lines = text.splitlines()
    conversations, current_messages = [], []
    current_role, buf = None, []

    def flush():
        nonlocal buf
        if current_role and buf:
            content = " ".join(" ".join(buf).split()).strip()
            if len(content) >= 10:
                current_messages.append({"role": current_role, "content": content})
        buf = []

    def save():
        if len(current_messages) >= 2:
            conversations.append({"messages": list(current_messages)})
        current_messages.clear()

    for line in lines:
        s = line.strip()
        if not s: continue
        if s.startswith(("##", "#", "---", "===")) and not SPEAKER_RE.match(s):
            if END_RE.match(s) or "<end>" in s.lower():
                flush(); save(); current_role = None
            continue
        if END_RE.match(s) or "<end>" in s.lower():
            flush(); save(); current_role = None; continue

        m = SPEAKER_RE.match(s)
        if m:
            sp = m.group(1).strip().lower()
            rest = m.group(2).strip()
            if sp in {"me", "you", "tiaya"}:
                flush(); current_role = "user"; buf = [rest] if rest else []
            elif sp in {"nayari", "nayri", "aura"}:
                flush(); current_role = "assistant"; buf = [rest] if rest else []
            else:
                if current_role: buf.append(s)
        else:
            if current_role: buf.append(s)

    flush(); save()
    return conversations

all_files = sorted(
    f for f in DATASET_DIR.rglob("*")
    if f.is_file() and f.suffix.lower() == ".md" and "Details" not in f.name
)

total_convs = 0
for f in all_files:
    text = f.read_text(encoding="utf-8", errors="replace")
    convs = parse_chat_text(text)
    total_convs += len(convs)

print(f"{total_convs}")
