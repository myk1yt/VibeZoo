import json
with open('extension/l10n/bundle.l10n.json', 'r', encoding='utf-8') as f:
    en_bundle = json.load(f)

with open('extension/l10n/bundle.l10n.ko.json', 'r', encoding='utf-8') as f:
    ko_bundle = json.load(f)

# Add missing translations
ko_bundle["Enter text"] = "텍스트 입력"
ko_bundle["Text"] = "텍스트"

# Sync all keys from en_bundle
final_ko_bundle = {}
for k in en_bundle.keys():
    final_ko_bundle[k] = ko_bundle.get(k, k)

with open('extension/l10n/bundle.l10n.ko.json', 'w', encoding='utf-8') as f:
    json.dump(final_ko_bundle, f, indent=2, ensure_ascii=False)

print("Done")
