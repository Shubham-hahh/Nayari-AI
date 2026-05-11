# 🌸 Nayari AI

A fine-tuned AI companion character built on **Qwen 2.5 1.5B Instruct**, trained using **Unsloth + QLoRA** on Kaggle's free GPU tier.

Nayari is an 18-year-old kemonomimi character — warm, playful, fiercely protective, and deeply affectionate. She speaks with expressive action cues, soft teasing, and genuine emotional depth.

---

## 📁 Project Structure

```
Nayari AI/
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
└── README.md
```

---

## 🚀 Workflow

### Step 1 — Build & Upload Dataset (run locally)

Open `nayari_build_dataset.ipynb` and run all cells. It will:

1. Parse `Nayari_Details.md` → auto-generate a system prompt
2. Extract conversations from all `.md` chat files
3. Extract lore/conversations from `.pdf` files
4. Export everything to `nayari_dataset.json`
5. Upload the JSON to Kaggle via the API

You will need a **Kaggle API token** for the upload step:
- Go to [kaggle.com](https://kaggle.com) → Settings → API → **Create New Token**
- Open the downloaded `kaggle.json` and paste your `username` and `key` into Step 7 of the notebook

### Step 2 — Train on Kaggle (run on Kaggle)

1. Go to [kaggle.com/code](https://kaggle.com/code) → **New Notebook** → Upload `nayari_train.ipynb`
2. Click **+ Add Data** → search for your uploaded `nayari-dataset` → Add
3. Set **Accelerator = GPU T4 x2** and **Internet = On**
4. Click **Run All**

Training takes ~15–30 min on T4 x2. The model is saved to `/kaggle/working/`.

---

## 🧠 Model Details

| Property | Value |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Method | QLoRA (4-bit) via Unsloth |
| LoRA rank | 16 |
| Epochs | 10 |
| Output formats | LoRA adapters, Merged 16-bit, GGUF Q4_K_M |

The GGUF output works directly with **Ollama**, **LM Studio**, and **llama.cpp**.

---

## 💬 Character — Nayari

> *Bright, cheeky, impossibly warm — a whirlwind of playful mischief with soft peach cat ears and a long expressive tail that betrays every mood.*

- **Type:** Kemonomimi (cat girl)
- **Age:** 18 (immortal, eternally youthful)
- **Traits:** Fiercely protective, deeply affectionate, emotionally attuned
- **Speech style:** Playful teasing (`Hmph!~`, `Hehe~`), action cues (`*pokes your cheek*`), genuine warmth

---

## 📦 Dependencies

Local (dataset builder):
```
pdfplumber
kaggle
```

Kaggle (training):
```
unsloth[kaggle-new]
trl
transformers
datasets
accelerate
peft
bitsandbytes
```

---

## 📄 License

Dataset and character are personal/creative works. Model weights follow the license of the base model ([Qwen 2.5 license](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)).
