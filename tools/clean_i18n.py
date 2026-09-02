import glob, json, os

nls_keys_to_delete = [
    "vibezoo.reviewProject.title",
    "vibezoo.findBugs.title",
    "vibezoo.suggestRefactor.title",
    "vibezoo.generateDocs.title",
    "vibezoo.explainCode.title",
    "vibezoo.analyzeChanges.title",
    "vibezoo.reviewPR.title",
    "vibezoo.refactorAcrossFiles.title",
    "vibezoo.learnProject.title",
    "vibezoo.recallProject.title",
    "vibezoo.learnPreference.title",
    "vibezoo.getPreferences.title",
    "vibezoo.rebuildCodeIndex.title",
    "vibezoo.scout.port.description",
    "vibezoo.reviewer.port.description",
    "vibezoo.tester.port.description",
    "vibezoo.deepAnalyzer.port.description",
    "vibezoo.emotion.detectionEnabled.description",
]

l10n_keys_to_delete = [
    'VibeZoo: Please type "explain code" in Zoo Code chat. (explain_code MCP tool)',
    'VibeZoo: Please type "analyze changes" in Zoo Code chat. (analyze_changes MCP tool)',
    'VibeZoo: Please type "review PR" in Zoo Code chat. (review_pr MCP tool)',
    'VibeZoo: Please type "refactor" in Zoo Code chat. (refactor_across_files MCP tool)',
    'VibeZoo: Please type "learn project" in Zoo Code chat. (learn_project MCP tool)',
    'VibeZoo: Please type "recall project" in Zoo Code chat. (recall_project MCP tool)',
    'VibeZoo: Please type "learn preference" in Zoo Code chat. (learn_preference MCP tool)',
    'VibeZoo: Please type "show preferences" in Zoo Code chat. (get_preferences MCP tool)',
    'VibeZoo: Please type "rebuild code index" in Zoo Code chat. (rebuild_code_index MCP tool)',
]

print("=== Processing package.nls files ===")
nls_files = sorted(glob.glob('extension/package.nls*.json'))
for fpath in nls_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    orig_len = len(data)
    del_count = 0
    for k in nls_keys_to_delete:
        if k in data:
            del data[k]
            del_count += 1
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f"{os.path.basename(fpath)}: {orig_len} -> {len(data)} (deleted {del_count}/{len(nls_keys_to_delete)})")

print("\n=== Processing bundle.l10n files ===")
l10n_files = sorted(glob.glob('extension/l10n/bundle.l10n*.json'))
for fpath in l10n_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    orig_len = len(data)
    del_count = 0
    for k in l10n_keys_to_delete:
        if k in data:
            del data[k]
            del_count += 1
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f"{os.path.basename(fpath)}: {orig_len} -> {len(data)} (deleted {del_count}/{len(l10n_keys_to_delete)})")
