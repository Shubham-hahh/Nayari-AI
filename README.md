# 🌸 Nayari AI

A fine-tuned AI companion character built on **Qwen 2.5 1.5B Instruct**, trained using **Unsloth + LoRA** on Kaggle's free GPU tier.

Nayari is an 18-year-old kemonomimi character — warm, playful, fiercely protective, and deeply affectionate. She speaks with expressive action cues, soft teasing, and genuine emotional depth.

**🔗 Model Weights:** [https://huggingface.co/Crossie/Nayari](https://huggingface.co/Crossie/Nayari)

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
├── nayari_export.ipynb            # KAGGLE — exports the fine-tuned model to GGUF, HuggingFace, etc.
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
3. Convert lore PDFs into training conversations
4. Export everything to `nayari_dataset.json`
5. Upload the JSON to Kaggle via the API

### Step 2 — Train on Kaggle (run on Kaggle)

1. Go to [kaggle.com/code](https://kaggle.com) → **New Notebook** → Upload `nayari_train.ipynb`
2. Click **+ Add Data** → search for your uploaded `nayari-dataset` → Add
3. Set **Accelerator = GPU T4 x2** and **Internet = On**
4. Run cells **in order**.

### Step 3 — Export & Download

1. After training, use `nayari_export.ipynb` to generate LoRA adapters and GGUF outputs.
2. You can download the files directly or push them to Hugging Face.
3. Pre-compiled weights are available here: [Crossie/Nayari](https://huggingface.co/Crossie/Nayari)

---

## 💻 How to Run Nayari

Nayari is exported in **GGUF** and **Hugging Face** formats, making her compatible with almost any modern LLM runner.

### Option A: Desktop Apps (Easiest)
Download the `.gguf` file from the [Hugging Face repo](https://huggingface.co/Crossie/Nayari) and load it into:
*   **LM Studio:** Search for the local file and load it. Use the "ChatML" preset.
*   **KoboldCpp:** Excellent for roleplay. Launch and set **Instruct Mode = ChatML**.
*   **Jan.ai / AnythingLLM:** Standard GGUF support.

### Option B: Command Line / Servers
*   **Ollama:** Create a `Modelfile` pointing to the GGUF and run `ollama create nayari -f Modelfile`.
*   **Llama.cpp:** Run via `./llama-cli -m nayari-Q4_K_M.gguf -p "ChatML"`.

### Important Settings
*   **Instruct Mode / Prompt Template:** ChatML
*   **System Prompt:** Not required (Nayari’s identity is baked into the model's tokenizer).
*   **Context Length:** 4096 (or higher if your hardware allows).

---

## 🧠 Model Details

| Property              | Value                                                                  |
| -----------------------| ------------------------------------------------------------------------|
| **Base model**        | `huihui-ai/Qwen2.5-1.5B-Instruct-abliterated`                          |
| **Weights**           | [huggingface.co/Crossie/Nayari](https://huggingface.co/Crossie/Nayari) |
| **Method**            | LoRA (bfloat16) via Unsloth                                            |
| **LoRA rank / alpha** | 32 / 64                                                                |
| **Epochs**            | 300                                                                    |
| **Output formats**    | GGUF (Q4, Q8), FP16, LoRA Adapters                                     |

---

## 🎭 Training Design

Nayari uses a **two-layer personality baking** approach:

1.  **Organic Training:** Teaches speech patterns, emotional rhythms, and action cues (`*pokes your cheek*`, `Hehe~`) from real conversation logs.
2.  **Baked System Prompt:** Nayari's full identity is embedded directly into the tokenizer's chat template. This means the model "knows" who she is from the first token without the user needing to provide a long system description in the UI.

---

## 💬 Character — Nayari

> *Bright, cheeky, impossibly warm — a whirlwind of playful mischief with soft peach cat ears and a long expressive tail that betrays every mood.*

- **Type:** Kemonomimi (cat girl)
- **Age:** 18 (immortal, eternally youthful)
- **Appearance:** Sky-blue hair, sun-yellow slit-pupil eyes, soft peach cat ears & tail, cream skin
- **Traits:** Fiercely protective, deeply affectionate, emotionally attuned
- **Speech style:** Playful teasing (`Hmph!~`, `Hehe~`), action cues (`*purrs softly*`), genuine warmth

---

## 📄 License

This project is licensed under the **MIT License**. Model weights follow the license of the base model ([Qwen 2.5](https://huggingface.co/collections/Qwen/qwen25-66e81a6663533ad4ab30046b)).
