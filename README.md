# ✨ Nayari-AI: The Personalized Companion Framework

[![Model](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Nayari%20Weights-blue)](https://huggingface.co/Crossie/Nayari)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)](https://www.python.org/)

A complete, end-to-end pipeline for fine-tuning highly personalized AI companions. This framework leverages **Unsloth + LoRA** to train efficient, persona-driven models (based on **Qwen 2.5**) that can run on consumer hardware.

While this repository features **Nayari** (a playful cat-girl companion), the logic is designed to be **universal**—allowing you to swap in your own lore, chat logs, and personality prompts to create a unique AI.

---

## 🌟 Key Features

*   **⚡ Ultra-Fast Training**: Powered by [Unsloth](https://github.com/unslothai/unsloth) for 2x faster training and 70% less VRAM usage.
*   **📚 Multi-Source Dataset Building**: Automatically converts Markdown chat logs, character descriptions, and Lore PDFs into structured training data.
*   **🧠 "Baked-In" Persona**: Identity is embedded into the tokenizer/chat template, so the model "knows" who it is without needing a external system prompt.
*   **📦 Universal Compatibility**: Exports directly to **GGUF** (for LM Studio/Ollama), **LoRA Adapters**, and **Hugging Face** formats.
*   **☁️ Cloud-Ready**: Designed to run on Kaggle's free GPU tier (T4 x2).

---

## 📁 Project Structure

```bash
Nayari-AI/
├── dataset/                     # 📂 PLACE YOUR LORE HERE
│   ├── Nayari_Details.md        # Character description & personality
│   ├── chat_logs.md             # Raw conversation examples
│   └── Lore.pdf                 # Backstory and world-building documents
│
├── nayari_build_dataset.ipynb   # 🛠️ LOCAL: Converts raw files → nayari_dataset.json
├── nayari_train.ipynb           # 🚀 KAGGLE: Fine-tunes the model using Unsloth
├── nayari_export.ipynb          # 📦 KAGGLE: Exports to GGUF, FP16, and HF
├── nayari_test.ipynb            # 🧪 LOCAL: Benchmark & inference test script
│
├── nayari_dataset.json          # Compiled training data
├── nayari_system_prompt.txt     # The persona's "soul" (baked into training)
└── README.md
```

---

## 🚀 The Training Pipeline

To create your own custom companion, follow these steps:

### 1. Lore & Dataset Preparation
Place your character's data in the `dataset/` folder. The parser supports:
*   **Markdown**: High-quality chat examples and personality traits.
*   **PDFs**: World lore, historical context, or long-form descriptions.
*   **System Prompt**: Edit `nayari_system_prompt.txt` to define the core identity.

### 2. Build & Upload
Run `nayari_build_dataset.ipynb` locally. It will aggregate your lore, format it for ChatML, and generate `nayari_dataset.json`. Upload this file to a Kaggle Dataset.

### 3. Fine-Tune on Kaggle
Upload `nayari_train.ipynb` to Kaggle, attach your dataset, and run with **GPU T4 x2**. This will produce LoRA adapters tailored to your character.

### 4. Export & Quantize
Use `nayari_export.ipynb` to merge weights and export to **GGUF** (Q4_K_M, Q8_0, etc.) for easy distribution.

---

## 💻 Running the Model

The resulting models are compatible with almost any modern LLM runner:

| Platform | Recommended Settings |
| :--- | :--- |
| **LM Studio** | Use "ChatML" preset, load GGUF file. |
| **KoboldCpp** | Best for roleplay. Set Instruct Mode to **ChatML**. |
| **Ollama** | Use a Modelfile pointing to the GGUF. |
| **Llama.cpp** | Run via `./llama-cli -m model.gguf -p "ChatML"`. |

### Recommended Parameters
*   **Prompt Template:** ChatML
*   **Context Length:** 4096+
*   **Temperature:** 0.7 - 0.9 (for personality)
*   **Repetition Penalty:** 1.05 - 1.1

---

## 🎭 Example Implementation: Nayari

> *"Bright, cheeky, and impossibly warm — a whirlwind of playful mischief with soft cat ears and a long expressive tail."*

Nayari serves as the reference implementation for this framework. You can download her pre-compiled weights here: **[Hugging Face: Crossie/Nayari](https://huggingface.co/Crossie/Nayari)**

| Property | Value |
| :--- | :--- |
| **Base Model** | Qwen2.5-1.5B-Instruct-abliterated |
| **Method** | LoRA (bfloat16) |
| **Rank/Alpha** | 32 / 64 |
| **Training Steps** | 300 Epochs |

---

## 📄 License

This framework is licensed under the **MIT License**.
*Model weights follow the license of the base model ([Qwen 2.5](https://huggingface.co/collections/Qwen/qwen25-66e81a6663533ad4ab30046b)).*
