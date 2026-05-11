# 🌸 Nayari AI

A fine-tuned AI companion character built on **Qwen 2.5 1.5B Instruct**, trained using **Unsloth + LoRA** on Kaggle's free GPU tier.

Nayari is an 18-year-old kemonomimi character — warm, playful, fiercely protective, and deeply affectionate. She speaks with expressive action cues, soft teasing, and genuine emotional depth.

---

## 📁 Project Structure

```
Nayari-AI/
├── dataset/
│   ├── Nayari_Details.md          # Character description & personality
│   ├── Aura_chat_1..3.md          # Raw conversation logs (old name: Aura)
│   ├── Nayari_chat_4.md           # Raw conversation log
│   ├── Discovery .pdf             # Lore / backstory PDF
│   └── Her Beliefs .pdf           # Lore / beliefs PDF
│
├── nayari_build_dataset.ipynb     # LOCAL — converts all files → nayari_dataset.json + uploads to Kaggle
├── nayari_train.ipynb             # KAGGLE — fine-tunes Qwen 2.5 using the uploaded dataset
├── nayari_dataset.json            # Auto-generated dataset (do not edit manually)
├── nayari_system_prompt.txt       # Nayari's system prompt (baked into tokenizer at training time)
└── README.md
```

---

## 🚀 Workflow

### Step 1 — Build & Upload Dataset (run locally)

Open `nayari_build_dataset.ipynb` and run all cells. It will:

1. Parse `Nayari_Details.md` for character info
2. Extract conversations from all `.md` chat files
3. Convert lore PDFs into training conversations (organic — no raw system prompt injection)
4. Export everything to `nayari_dataset.json`
5. Upload the JSON to Kaggle via the API

You will need a **Kaggle API token** for the upload step:
- Go to [kaggle.com](https://kaggle.com) → Settings → API → **Create New Token**
- Open the downloaded `kaggle.json` and paste your `username` and `key` into Step 7 of the notebook

### Step 2 — Train on Kaggle (run on Kaggle)

1. Go to [kaggle.com/code](https://kaggle.com/code) → **New Notebook** → Upload `nayari_train.ipynb`
2. Click **+ Add Data** → search for your uploaded `nayari-dataset` → Add
3. Set **Accelerator = GPU T4 x2** and **Internet = On**
4. Run cells **in order** (Steps 1 → 9, then 8/10 are reference only)

Training takes ~15–30 min on T4 x2.

### Step 3 — Download & Run with KoboldCpp (run locally)

1. Run **Step 9E** in the Kaggle notebook to get a Cloudflare download link
2. Download `nayari-Q4_K_M.gguf` (fast) or `nayari-Q8_0.gguf` (higher quality)
3. Install [KoboldCpp](https://github.com/LostRuins/koboldcpp/releases)
4. Launch: `koboldcpp.exe nayari-Q4_K_M.gguf --contextsize 4096`
5. Open `http://localhost:5001` — set **Instruct mode = ChatML**
6. Nayari's personality is baked in — no system prompt needed in the UI

---

## 🧠 Model Details

| Property | Value |
|---|---|
| Base model | `huihui-ai/Qwen2.5-1.5B-Instruct-abliterated` |
| Method | LoRA (bfloat16) via Unsloth |
| LoRA rank | 32 |
| LoRA alpha | 64 |
| Epochs | 300 |
| Learning rate | 3e-4 |
| Output formats | LoRA adapters, Merged 16-bit, GGUF Q4_K_M, GGUF Q8_0 |
| Inference | KoboldCpp (ChatML instruct mode) |

The GGUF output works directly with **KoboldCpp**, **Ollama**, **LM Studio**, and **llama.cpp**.

---

## 🎭 Training Design

Nayari uses a **two-layer personality baking** approach:

| Layer | What it does |
|---|---|
| **Organic training** | Teaches speech patterns, emotional rhythms, action cues (`*pokes your cheek*`, `Hehe~`) from real conversation logs |
| **Baked system prompt** | Replaces Qwen's default `"You are Qwen..."` in the tokenizer chat template with Nayari's full identity — the same technique Alibaba used |

The patched tokenizer is saved into `tokenizer_config.json` and embedded in the GGUF, so Nayari's identity is present at every inference call without needing to set a system prompt manually.

---

## 💬 Character — Nayari

> *Bright, cheeky, impossibly warm — a whirlwind of playful mischief with soft peach cat ears and a long expressive tail that betrays every mood.*

- **Type:** Kemonomimi (cat girl)
- **Age:** 18 (immortal, eternally youthful)
- **Appearance:** Sky-blue hair, sun-yellow slit-pupil eyes, soft peach cat ears & tail, cream skin
- **Traits:** Fiercely protective, deeply affectionate, emotionally attuned
- **Speech style:** Playful teasing (`Hmph!~`, `Hehe~`, `Aww!~`), action cues (`*pokes your cheek*`, `*purrs softly*`), genuine warmth

---

## 📦 Dependencies

Local (dataset builder):
```
pdfplumber
kaggle
```

Kaggle (training — auto-installed by Step 1):
```
unsloth[kaggle-new]
trl>=0.18.2,<=0.24.0
transformers>=4.51.3,<=5.5.0
datasets>=3.4.1,<4.4.0
accelerate
peft
bitsandbytes
```

Inference:
```
KoboldCpp — https://github.com/LostRuins/koboldcpp/releases
```

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

Model weights follow the license of the base model ([huihui-ai/Qwen2.5-1.5B-Instruct-abliterated](https://huggingface.co/huihui-ai/Qwen2.5-1.5B-Instruct-abliterated)).
