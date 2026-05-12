"""
Rebuild nayari_build_dataset.ipynb with a robust, feature-complete pipeline.

New capabilities over v1:
  - Auto-discovers speaker aliases from files (no hardcoded names)
  - Supports .md, .txt, .pdf — any combo, any subfolders
  - Deduplication of near-identical conversations
  - Quality filtering (min turns, min content length per message)
  - OOC annotation stripping  [OOC: ...] / (OOC ...) 
  - Rich per-file diagnostics & warnings
  - Per-conversation source tagging
  - Dataset statistics dashboard + token estimate
  - Lore augmentation: each chunk paired with varied prompts
  - Graceful error handling — one bad file never crashes the run
"""
import json, textwrap, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

NB_PATH = Path("nayari_build_dataset.ipynb")

# ── helper ────────────────────────────────────────────────────────────────────
def cell_md(source: str, cell_id: str):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {},
            "source": [source]}

def cell_code(source: str, cell_id: str):
    lines = source.splitlines(keepends=True)
    return {"cell_type": "code", "execution_count": None, "id": cell_id,
            "metadata": {}, "outputs": [], "source": lines}

# ══════════════════════════════════════════════════════════════════════════════
# Cell sources
# ══════════════════════════════════════════════════════════════════════════════

HEADER_MD = textwrap.dedent("""\
# 🌸 Nayari Dataset Builder  v3
**Run locally.** Scans `dataset/` (including subdirectories) for `.md`, `.txt`, \
and `.pdf` files, applies a robust multi-format parser, deduplicates, quality-filters, \
and exports `nayari_dataset.json`.  Then auto-uploads to Kaggle.

| Feature | Details |
|---|---|
| Speaker formats | `Name:`, `**Name**:`, `> Name:`, `[Name]:` |
| Scene splitting | Blank-line gaps, `---END---`, `<end>`, `===` dividers |
| Auto-aliases | Unknown speakers scanned from filenames & content |
| Quality filter | Min 2 turns, min 10 chars/message |
| Deduplication | MD5 fingerprint on normalised content |
| OOC stripping | `[OOC: …]` and `(OOC …)` blocks removed |
| Source tagging | Every conversation records its origin file |
| Token estimate | Rough GPT-style token count in the stats cell |
""")

STEP0_MD = "## 📦 Step 0 — Install & Import"

STEP0_CODE = textwrap.dedent("""\
%pip install pdfplumber kaggle -q

import re, json, os, shutil, subprocess, sys, hashlib, warnings
import pdfplumber
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore", message="Could not get FontBBox")

DATASET_DIR = Path("dataset")
OUTPUT_FILE = Path("nayari_dataset.json")

# ── pretty directory scan ────────────────────────────────────────────────────
all_files = sorted(
    f for f in DATASET_DIR.rglob("*")
    if f.is_file() and f.suffix.lower() in {".md", ".txt", ".pdf"}
)
print(f"Found {len(all_files)} source file(s) in dataset/:\\n")
for f in all_files:
    rel = f.relative_to(DATASET_DIR)
    print(f"  [{f.suffix.upper():5}] {rel}  ({f.stat().st_size/1024:.1f} KB)")
""")

STEP1_MD = "## 1 — Character Details"

STEP1_CODE = textwrap.dedent("""\
# Locate the details file anywhere inside dataset/
details_candidates = list(DATASET_DIR.rglob("*details*"))
if not details_candidates:
    print("⚠️  No details file found — character metadata will be empty.")
    char_name = char_type = char_gender = char_traits = char_personality = ""
else:
    details_text = details_candidates[0].read_text(encoding="utf-8", errors="replace")

    def extract_field(text, field):
        m = re.search(rf"\\*\\*{field}\\*\\*:?\\s*(.+)", text)
        return m.group(1).strip() if m else ""

    char_name        = extract_field(details_text, "Name")
    char_type        = extract_field(details_text, "Type")
    char_gender      = extract_field(details_text, "Gender")
    char_traits      = extract_field(details_text, "Traits")
    char_personality = extract_field(details_text, "Personally")
    print(f"Character : {char_name} | {char_type} | {char_gender}")
    print(f"Details file: {details_candidates[0].relative_to(DATASET_DIR)}")

lore_sections = []
""")

STEP2_MD = "\n".join([
    "## 2 \u2014 Robust Multi-Format Parser",
    "",
    "Handles every speaker format seen in the repo:",
    "",
    "```",
    "Name: text           \u2190 plain",
    "**Name**: text       \u2190 bold markdown",
    "> Name: text         \u2190 blockquote",
    "[Name]: text         \u2190 bracket",
    "```",
    "",
    "Scene splitting triggers on: `--- END ---`, `=== break ===`, `<end>`, or **3+ blank lines**.",
    "OOC annotations `[OOC: \u2026]` and `(OOC \u2026)` are stripped from message content.",
])

STEP2_CODE = textwrap.dedent('''\
# ── Core aliases (extended automatically per-file below) ────────────────────
BASE_USER_ALIASES      = {"me", "you", "tiaya"}
BASE_ASSISTANT_ALIASES = {"nayari", "nayri", "aura"}

# Universal speaker line pattern — covers all 4 formats
SPEAKER_RE = re.compile(
    r"""^
    (?:\\*{1,2}|\\[|>\\s*)?          # optional: ** or [ or >
    ([A-Za-z][A-Za-z0-9 _\\'\\-]*)   # speaker name
    (?:\\*{1,2}|\\])?                 # optional closing ** or ]
    :\\s*(.*)                         # colon + rest of line
    $""",
    re.VERBOSE,
)

END_RE = re.compile(
    r"^[-=*]{3,}\\s*(<?(end|END|break|BREAK|scene|SCENE)>?)?\\s*[-=*]{0,}$"
)

OOC_RE = re.compile(r"\\[OOC:?[^\\]]*\\]|\\(OOC[^)]*\\)", re.IGNORECASE)


def _strip_ooc(text: str) -> str:
    return OOC_RE.sub("", text).strip()


def _inject_scene_ends(text: str) -> str:
    """Replace 3+ consecutive blank lines with a synthetic END marker."""
    return re.sub(r"(\\r?\\n){3,}", "\\n--- END ---\\n", text)


def _detect_aliases(text: str, filename: str):
    """
    Heuristically discover user/assistant aliases from the file.
    Any speaker that appears >= 2 times AND whose name contains a
    known assistant keyword is mapped to assistant; everything else
    that appears frequently becomes a user alias candidate.
    """
    counts = defaultdict(int)
    for line in text.splitlines():
        m = SPEAKER_RE.match(line.strip())
        if m:
            counts[m.group(1).strip().lower()] += 1

    user_extra, asst_extra = set(), set()
    asst_keywords = {"nayari", "nayri", "aura", "goddess"}
    for name, cnt in counts.items():
        if cnt < 2:
            continue
        if any(kw in name for kw in asst_keywords):
            asst_extra.add(name)
        else:
            user_extra.add(name)
    return user_extra, asst_extra


def parse_chat_text(text: str, filename: str = ""):
    """
    Full-featured chat parser.
    Returns list of {messages, source, turns} dicts.
    """
    user_aliases = BASE_USER_ALIASES.copy()
    asst_aliases = BASE_ASSISTANT_ALIASES.copy()
    u_extra, a_extra = _detect_aliases(text, filename)
    user_aliases |= u_extra
    asst_aliases |= a_extra

    text = _inject_scene_ends(text)
    lines = text.splitlines()
    conversations, current_messages = [], []
    current_role, buf = None, []
    skipped_lines = []

    def flush():
        nonlocal buf
        if current_role and buf:
            raw = " ".join(" ".join(buf).split()).strip()
            content = _strip_ooc(raw)
            if len(content) >= 10:          # quality: min 10 chars
                current_messages.append({"role": current_role, "content": content})
            elif content:
                skipped_lines.append(f"  ⚠ Short message ({len(content)} chars): {content!r}")
        buf = []

    def save():
        if len(current_messages) >= 2:      # quality: min 2 turns
            conversations.append({
                "messages": list(current_messages),
                "source": filename,
            })
        current_messages.clear()

    for line in lines:
        s = line.strip()
        if not s:
            continue
        # heading / metadata lines — skip
        if s.startswith(("##", "#", "---", "===")) and not SPEAKER_RE.match(s):
            if END_RE.match(s) or "<end>" in s.lower():
                flush(); save(); current_role = None
            continue
        if END_RE.match(s) or "<end>" in s.lower() or "<--- end" in s.lower():
            flush(); save(); current_role = None; continue

        m = SPEAKER_RE.match(s)
        if m:
            sp   = m.group(1).strip().lower()
            rest = m.group(2).strip()
            if sp in user_aliases:
                flush(); current_role = "user"; buf = [rest] if rest else []
            elif sp in asst_aliases:
                flush(); current_role = "assistant"; buf = [rest] if rest else []
            else:
                # unknown speaker — carry on accumulating if mid-turn
                if current_role:
                    buf.append(s)
        else:
            if current_role:
                buf.append(s)

    flush(); save()

    if skipped_lines:
        print(f"    [{filename}] quality skips:")
        for w in skipped_lines[:5]:
            print(w)

    return conversations


# ── deduplication ─────────────────────────────────────────────────────────────
def _fingerprint(conv: dict) -> str:
    norm = " ".join(
        m["content"][:80].lower()
        for m in conv["messages"]
    )
    return hashlib.md5(norm.encode()).hexdigest()


def deduplicate(convs: list) -> list:
    seen, out = set(), []
    for c in convs:
        fp = _fingerprint(c)
        if fp not in seen:
            seen.add(fp)
            out.append(c)
    return out


# ── PDF extractor ─────────────────────────────────────────────────────────────
def extract_pdf(path: Path):
    chat_convs, lore_chunks = [], []
    try:
        with pdfplumber.open(path) as pdf:
            print(f"  {path.name}: {len(pdf.pages)} page(s)")
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if not text.strip():
                    print(f"    Page {i+1}: empty — skipped"); continue
                convs = parse_chat_text(text, path.name)
                if convs:
                    print(f"    Page {i+1}: CHAT  — {len(convs)} scene(s)")
                    chat_convs.extend(convs)
                else:
                    cleaned = re.sub(r"\\n{3,}", "\\n\\n", text).strip()
                    lore_chunks.append(cleaned)
                    print(f"    Page {i+1}: LORE  — {len(cleaned)} chars")
    except Exception as exc:
        print(f"  ❌ Failed to read {path.name}: {exc}")
    return chat_convs, lore_chunks


def is_details_file(path: Path) -> bool:
    return "details" in path.name.lower() or "detail" in path.name.lower()


print("✅ Parser v3 ready — multi-format, auto-alias, OOC-strip, dedup.")
''')

STEP3_MD = "## 3 — Parse All Source Files (.md / .txt / .pdf)"

STEP3_CODE = textwrap.dedent("""\
md_conversations  = []
txt_conversations = []
pdf_conversations = []

chat_files = [f for f in all_files if not is_details_file(f)]
print(f"Processing {len(chat_files)} file(s)...\\n")

for path in chat_files:
    ext = path.suffix.lower()
    rel = str(path.relative_to(DATASET_DIR))

    if ext in {".md", ".txt"}:
        try:
            text  = path.read_text(encoding="utf-8", errors="replace")
            convs = parse_chat_text(text, rel)
            label = "md" if ext == ".md" else "txt"
            print(f"  [{label.upper():4}] {rel}: {len(convs)} conversation(s)")
            if ext == ".md":
                md_conversations.extend(convs)
            else:
                txt_conversations.extend(convs)
        except Exception as exc:
            print(f"  ❌  {rel}: {exc}")

    elif ext == ".pdf":
        print(f"  [PDF ] {path.name}")
        chat_convs, lore_chunks = extract_pdf(path)
        pdf_conversations.extend(chat_convs)
        if lore_chunks:
            name = path.stem.strip()
            text = "\\n\\n".join(lore_chunks)
            lore_sections.append({"source": name, "text": text})
            print(f"    → Lore '{name}' stored ({len(text)} chars)")
        print()

all_raw = md_conversations + txt_conversations + pdf_conversations
print(f"\\nRaw conversations: {len(all_raw)}")
print(f"  {len(md_conversations)} md  |  {len(txt_conversations)} txt  |  {len(pdf_conversations)} pdf")
""")

STEP4_MD = "\n".join([
    "## 4 \u2014 Lore \u2192 Training Conversations",
    "",
    "Each PDF lore section is chunked into paragraphs.",
    "Each chunk is paired with a varied natural-language prompt so the model learns",
    "to recall Nayari's lore organically. Multiple prompts per chunk for augmentation.",
])

STEP4_CODE = "\n".join([
    'LORE_PROMPTS = [',
    '    "Tell me about yourself.",',
    '    "What\'s your story?",',
    '    "Who are you, really?",',
    '    "Share something about yourself with me.",',
    '    "What do you believe in?",',
    '    "Tell me what you believe.",',
    '    "What matters most to you?",',
    '    "What drives you?",',
    '    "Describe yourself to me.",',
    '    "How would you describe who you are?",',
    '    "What makes you, you?",',
    '    "Can you tell me more about your past?",',
    ']',
    '',
    'def lore_to_convs(sections, min_chars=150, augment=False):',
    '    # Split each lore section into paragraph chunks.',
    '    # augment=True pairs each chunk with TWO different prompts.',
    '    convs = []',
    '    prompt_idx = 0',
    '    for section in sections:',
    '        raw_chunks = [c.strip() for c in section["text"].split("\\n\\n") if c.strip()]',
    '        chunks, buf = [], ""',
    '        for chunk in raw_chunks:',
    '            buf = (buf + "\\n\\n" + chunk).strip() if buf else chunk',
    '            if len(buf) >= min_chars:',
    '                chunks.append(buf); buf = ""',
    '        if buf:',
    '            if chunks: chunks[-1] += "\\n\\n" + buf',
    '            else: chunks.append(buf)',
    '        reps = 2 if augment else 1',
    '        for chunk in chunks:',
    '            for _ in range(reps):',
    '                prompt = LORE_PROMPTS[prompt_idx % len(LORE_PROMPTS)]',
    '                convs.append({',
    '                    "messages": [',
    '                        {"role": "user",      "content": prompt},',
    '                        {"role": "assistant", "content": chunk},',
    '                    ],',
    '                    "source": section["source"],',
    '                })',
    '                prompt_idx += 1',
    '    return convs',
    '',
    'lore_conversations = lore_to_convs(lore_sections, augment=False)',
    'print(f"Lore sections      : {len(lore_sections)}")',
    'print(f"Lore training convs: {len(lore_conversations)}")',
    'for i, c in enumerate(lore_conversations):',
    '    q = c["messages"][0]["content"]',
    '    a = c["messages"][1]["content"]',
    '    print(f"  [{i+1:2}] Q: {q!r:<40}  A ({len(a)} chars): {a[:50]!r}...")',
])

STEP5_MD = "## 5 — Deduplication & Quality Filter"

STEP5_CODE = textwrap.dedent("""\
all_conversations = all_raw + lore_conversations

before = len(all_conversations)
all_conversations = deduplicate(all_conversations)
after  = len(all_conversations)

print(f"Before dedup : {before}")
print(f"After  dedup : {after}  ({before - after} duplicates removed)")

# Sanity-check: flag any conversation with a very long single message
WARN_CHARS = 3000
flagged = [
    (i+1, m["role"], len(m["content"]))
    for i, c in enumerate(all_conversations)
    for m in c["messages"]
    if len(m["content"]) > WARN_CHARS
]
if flagged:
    print(f"\\n⚠ {len(flagged)} message(s) exceed {WARN_CHARS} chars (may be lore, review if unexpected):")
    for idx, role, length in flagged[:8]:
        print(f"  Conv {idx} [{role}]: {length} chars")
else:
    print("\\n✅ No oversized messages.")
""")

STEP6_MD = "## 6 — Preview & Statistics Dashboard"

STEP6_CODE = textwrap.dedent("""\
from collections import Counter

# ── turn distribution ────────────────────────────────────────────────────────
turn_counts = [len(c["messages"]) for c in all_conversations]
total_msgs  = sum(turn_counts)
total_chars = sum(len(m["content"]) for c in all_conversations for m in c["messages"])
# rough token estimate: ~4 chars per token
token_est   = total_chars // 4

source_counts = Counter(c.get("source","?") for c in all_conversations)

print("=" * 60)
print(f"  DATASET STATISTICS")
print("=" * 60)
print(f"  Total conversations : {len(all_conversations)}")
print(f"    from markdown     : {len(md_conversations)}")
print(f"    from txt          : {len(txt_conversations)}")
print(f"    from pdf chats    : {len(pdf_conversations)}")
print(f"    from lore         : {len(lore_conversations)}")
print(f"  Total messages      : {total_msgs}")
print(f"  Total characters    : {total_chars:,}")
print(f"  Est. tokens (÷4)    : {token_est:,}")
print(f"  Avg turns/conv      : {sum(turn_counts)/max(len(turn_counts),1):.1f}")
print(f"  Min / Max turns     : {min(turn_counts)} / {max(turn_counts)}")
print()
print("  Sources:")
for src, cnt in source_counts.most_common():
    print(f"    {src:<45} {cnt:>3} conv(s)")
print("=" * 60)

# ── conversation preview (first 3) ──────────────────────────────────────────
print()
for i, conv in enumerate(all_conversations[:3]):
    print(f"--- Conv {i+1} [{conv.get('source','?')}] ({len(conv['messages'])} turns) ---")
    for msg in conv["messages"]:
        label = "👤" if msg["role"] == "user" else "🌸"
        snippet = msg["content"][:90]
        ellipsis = "..." if len(msg["content"]) > 90 else ""
        print(f"  {label} {snippet}{ellipsis}")
    print()
""")

STEP7_MD = "## 7 — Export JSON"

STEP7_CODE = textwrap.dedent("""\
from datetime import datetime, timezone

dataset_json = {
    "meta": {
        "version": 3,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "total_conversations": len(all_conversations),
        "sources": {
            "markdown": len(md_conversations),
            "txt":      len(txt_conversations),
            "pdf":      len(pdf_conversations),
            "lore":     len(lore_conversations),
        },
    },
    "character": {
        "name": char_name, "type": char_type, "gender": char_gender,
        "traits": char_traits, "personality": char_personality,
        "lore_sections": lore_sections,
    },
    "conversations": all_conversations,
}

OUTPUT_FILE.write_text(
    json.dumps(dataset_json, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
size_kb = OUTPUT_FILE.stat().st_size / 1024
print(f"✅ Saved → {OUTPUT_FILE.resolve()}")
print(f"   {len(all_conversations)} conversations | {size_kb:.1f} KB")
""")

STEP8_MD = textwrap.dedent("""\
## 8 — Upload to Kaggle via API

**Before running:**
1. Go to [kaggle.com](https://kaggle.com) → Profile → **Settings** → **API** → **Create New Token**
2. A `kaggle.json` downloads — open it and copy the `username` and `key` values
3. Paste them into the two variables below

> The dataset is created as **private** by default.
""")

STEP8_CODE = textwrap.dedent("""\
# ── FILL THESE IN ──────────────────────────────────────────────────────────
KAGGLE_USERNAME = "kaggle_username"   # from kaggle.json
KAGGLE_KEY      = "kaggle_key"        # from kaggle.json
DATASET_TITLE   = "nayari-dataset"   # slug used in the Kaggle URL
IS_PUBLIC       = False               # True to make the dataset public
# ───────────────────────────────────────────────────────────────────────────

kaggle_dir = Path.home() / ".kaggle"
kaggle_dir.mkdir(exist_ok=True)
creds_file = kaggle_dir / "kaggle.json"
creds_file.write_text(
    json.dumps({"username": KAGGLE_USERNAME, "key": KAGGLE_KEY}),
    encoding="utf-8",
)
creds_file.chmod(0o600)
print("✅ Credentials written.")

STAGING = Path("_kaggle_upload")
shutil.rmtree(STAGING, ignore_errors=True)
STAGING.mkdir()
shutil.copy(OUTPUT_FILE, STAGING / OUTPUT_FILE.name)

(STAGING / "dataset-metadata.json").write_text(
    json.dumps({
        "title":     DATASET_TITLE,
        "id":        f"{KAGGLE_USERNAME}/{DATASET_TITLE}",
        "licenses":  [{"name": "CC0-1.0"}],
        "isPrivate": not IS_PUBLIC,
    }, indent=2),
    encoding="utf-8",
)
print(f"✅ Staging folder ready: {STAGING.resolve()}")

def run_kaggle(*args):
    return subprocess.run(["kaggle", *args], capture_output=True, text=True)

result  = run_kaggle("datasets", "create", "-p", str(STAGING), "--dir-mode", "zip")
combined = (result.stdout + result.stderr).lower()

if "already exists" in combined or "403" in combined:
    print("Dataset already exists — pushing a new version...")
    result = run_kaggle(
        "datasets", "version", "-p", str(STAGING),
        "-m", f"v3 build — {len(all_conversations)} conversations",
        "--dir-mode", "zip",
    )

print(result.stdout or result.stderr)

if result.returncode == 0:
    vis = "public" if IS_PUBLIC else "private"
    url = f"https://www.kaggle.com/datasets/{KAGGLE_USERNAME}/{DATASET_TITLE}"
    print(f"🎉 Upload successful! ({vis})")
    print(f"   Dataset URL: {url}")
    print()
    print("📋 Next steps in your Kaggle training notebook:")
    print("   1. Open nayari_train.ipynb on Kaggle")
    print(f"   2. Click '+ Add Data' → search '{DATASET_TITLE}' → Add")
    print("   3. Set Accelerator = GPU T4 x2, Internet = On → Run All")
else:
    print("❌ Upload failed. Double-check KAGGLE_USERNAME and KAGGLE_KEY.")

shutil.rmtree(STAGING, ignore_errors=True)
""")

# ══════════════════════════════════════════════════════════════════════════════
# Assemble notebook
# ══════════════════════════════════════════════════════════════════════════════

cells = [
    cell_md(HEADER_MD,  "aa000001"),
    cell_md(STEP0_MD,   "aa000002"),
    cell_code(STEP0_CODE, "aa000003"),
    cell_md(STEP1_MD,   "aa000004"),
    cell_code(STEP1_CODE, "aa000005"),
    cell_md(STEP2_MD,   "aa000006"),
    cell_code(STEP2_CODE, "aa000007"),
    cell_md(STEP3_MD,   "aa000008"),
    cell_code(STEP3_CODE, "aa000009"),
    cell_md(STEP4_MD,   "aa000010"),
    cell_code(STEP4_CODE, "aa000011"),
    cell_md(STEP5_MD,   "aa000012"),
    cell_code(STEP5_CODE, "aa000013"),
    cell_md(STEP6_MD,   "aa000014"),
    cell_code(STEP6_CODE, "aa000015"),
    cell_md(STEP7_MD,   "aa000016"),
    cell_code(STEP7_CODE, "aa000017"),
    cell_md(STEP8_MD,   "aa000018"),
    cell_code(STEP8_CODE, "aa000019"),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.14.3",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"✅ Notebook rebuilt: {NB_PATH}  ({NB_PATH.stat().st_size/1024:.1f} KB)")
print(f"   {len(cells)} cells total")
