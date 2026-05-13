import json
import re

nb_path = r't:\Documents\Github Desktop\Nayari-AI\nayari_build_dataset.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        # Re-doing the markdown cell string replace exactly
        new_source = []
        for line in cell['source']:
            line = line.replace("for `.md`, `.txt`, and `.pdf` files", "for `.md`, `.txt`, `.pdf`, and `.json` files")
            line = line.replace("Parse All Source Files (.md / .txt / .pdf)", "Parse All Source Files (.md / .txt / .pdf / .json)")
            new_source.append(line)
        cell['source'] = new_source

    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell['source']:
            line = line.replace('in {".md", ".txt", ".pdf"}', 'in {".md", ".txt", ".pdf", ".json"}')
            new_source.append(line)
        cell['source'] = new_source

# Now specific cell logic
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = "".join(cell['source'])
        
        if "md_conversations  = []" in src and "pdf_conversations = []" in src:
            new_src = src.replace(
                "pdf_conversations = []\n",
                "pdf_conversations = []\njson_conversations = []\n"
            )
            
            # The JSON handler
            json_handler = """
    elif ext == ".json":
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(text)
            convs = []
            if isinstance(data, list):
                convs = [c for c in data if "messages" in c]
            elif isinstance(data, dict):
                if "conversations" in data:
                    convs = data["conversations"]
                elif "messages" in data:
                    convs = [data]
            
            for c in convs:
                if "source" not in c:
                    c["source"] = rel
            
            print(f"  [JSON] {rel}: {len(convs)} conversation(s)")
            json_conversations.extend(convs)
        except Exception as exc:
            print(f"  ❌  {rel}: {exc}")
"""
            new_src = new_src.replace(
                "    elif ext == \".pdf\":",
                json_handler.strip('\n') + "\n\n    elif ext == \".pdf\":"
            )
            
            new_src = new_src.replace(
                "all_raw = md_conversations + txt_conversations + pdf_conversations\n",
                "all_raw = md_conversations + txt_conversations + pdf_conversations + json_conversations\n"
            )
            
            new_src = new_src.replace(
                "print(f\"  {len(md_conversations)} md  |  {len(txt_conversations)} txt  |  {len(pdf_conversations)} pdf\")\n",
                "print(f\"  {len(md_conversations)} md  |  {len(txt_conversations)} txt  |  {len(pdf_conversations)} pdf  |  {len(json_conversations)} json\")\n"
            )
            
            cell['source'] = [line + '\n' for line in new_src.split('\n')]
            cell['source'][-1] = cell['source'][-1][:-1] if cell['source'][-1].endswith('\n') else cell['source'][-1]

        if "Total conversations :" in src and "from txt" in src:
            new_src = src.replace(
                "print(f\"    from pdf chats    : {len(pdf_conversations)}\")\n",
                "print(f\"    from pdf chats    : {len(pdf_conversations)}\")\nprint(f\"    from json         : {len(json_conversations)}\")\n"
            )
            cell['source'] = [line + '\n' for line in new_src.split('\n')]
            cell['source'][-1] = cell['source'][-1][:-1] if cell['source'][-1].endswith('\n') else cell['source'][-1]
            
        if "sources" in src and "\"pdf\":" in src and "\"lore\":" in src:
            new_src = src.replace(
                "            \"pdf\":      len(pdf_conversations),\n",
                "            \"pdf\":      len(pdf_conversations),\n            \"json\":     len(json_conversations),\n"
            )
            cell['source'] = [line + '\n' for line in new_src.split('\n')]
            cell['source'][-1] = cell['source'][-1][:-1] if cell['source'][-1].endswith('\n') else cell['source'][-1]


with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write('\n')

print("Done.")
