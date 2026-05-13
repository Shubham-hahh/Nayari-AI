import json

nb_path = r't:\Documents\Github Desktop\Nayari-AI\nayari_train.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = "".join(cell['source'])
        
        # We need to replace the entire configuration block and the get_peft_model call
        if "LORA_TARGETS =" in src and "FastLanguageModel.get_peft_model(" in src:
            new_src = """# ── CONFIGURATION ─────────────────────────────────────────────────────────────
# target_modules: \"all\" (deep learning, all layers) or \"minimal\" (faster, only attention)
LORA_TARGETS = \"all\"

# Rank (r): Determines the \"brain capacity\" of the adapter. 
# 16 or 32 is great for characters. 64-128 for complex logic.
LORA_RANK = 32

# Alpha: Scaling factor. Rule of thumb: always set to 2x the LORA_RANK.
LORA_ALPHA = 64

# Advanced: Rank-Stabilized LoRA (rsLoRA). Recommended if using high ranks (like 64+).
USE_RSLORA = False

# Advanced: Weight-Decomposed LoRA (DoRA). Can significantly improve learning quality,
# but uses slightly more VRAM and reduces training speed by ~10%.
USE_DORA = False
# ────────────────────────────────────────────────────────────────────────────

if LORA_TARGETS == \"all\":
    target_modules = [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"]
elif LORA_TARGETS == \"minimal\":
    target_modules = [\"q_proj\", \"v_proj\"]
elif isinstance(LORA_TARGETS, list):
    target_modules = LORA_TARGETS
else:
    target_modules = [\"q_proj\", \"v_proj\"]  # fallback

model = FastLanguageModel.get_peft_model(
    model, 
    r=LORA_RANK,
    target_modules=target_modules,
    lora_alpha=LORA_ALPHA,
    lora_dropout=0.0,    # must be 0 for Unsloth fast-patching
    bias=\"none\",
    use_gradient_checkpointing=\"unsloth\", random_state=42,
    use_rslora=USE_RSLORA,
    use_dora=USE_DORA,
)
print(f\"✅ LoRA applied (r={LORA_RANK}, alpha={LORA_ALPHA}, targets={len(target_modules)}, rsLoRA={USE_RSLORA}, DoRA={USE_DORA})\")
"""
            cell['source'] = [line + '\n' for line in new_src.split('\n')]
            # Remove trailing newline
            if cell['source'][-1].endswith('\n'):
                cell['source'][-1] = cell['source'][-1][:-1]

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write('\n')

print("Patch applied.")
