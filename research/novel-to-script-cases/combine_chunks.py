import os

BASE = r"F:\Program Files\XEngineer\research\novel-to-script-cases"

files = [
    ("chunks_sherlock_novel", "01_sherlock_study_in_pink", "a-study-in-scarlet_novel_zh.txt"),
    ("chunks_sherlock_script", "01_sherlock_study_in_pink", "sherlock-a-study-in-pink_script_zh.txt"),
    ("chunks_pnp_novel", "03_pride_and_prejudice_2005", "pride-and-prejudice_novel_zh.txt"),
    ("chunks_pnp_script", "03_pride_and_prejudice_2005", "pride-and-prejudice-2005_script_zh.txt"),
]

for chunk_dir, out_subdir, out_name in files:
    chunks_path = os.path.join(BASE, chunk_dir)
    out_path = os.path.join(BASE, out_subdir, out_name)

    # Gather all _zh chunks in order
    zh_files = sorted([f for f in os.listdir(chunks_path) if f.endswith("_zh.txt")])

    if not zh_files:
        print(f"WARNING: No _zh.txt files found in {chunks_path}")
        continue

    combined = []
    for fname in zh_files:
        fpath = os.path.join(chunks_path, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            combined.append(f.read())

    full_text = "\n\n".join(combined)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    # Verify
    with open(out_path, 'r', encoding='utf-8') as f:
        verify_text = f.read()
    print(f"Combined {len(zh_files)} chunks -> {out_path} ({len(verify_text)} chars)")

print("\nAll files combined successfully!")
