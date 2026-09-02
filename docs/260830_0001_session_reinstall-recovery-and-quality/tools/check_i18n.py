import os
import sys
import hashlib

sys.stdout.reconfigure(encoding='utf-8')

def scan_i18n(base):
    res = {}
    for root, dirs, files in os.walk(base):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base).replace('\\', '/')
            with open(full, 'rb') as fp:
                data = fp.read()
            res[rel] = {
                'size': len(data),
                'sha256': hashlib.sha256(data).hexdigest()
            }
    return res

r_i18n = scan_i18n('mcp-servers/bridge/i18n')
e_i18n = scan_i18n('extension/mcp-servers/bridge/i18n')

print("Root i18n files count:", len(r_i18n))
print("Ext  i18n files count:", len(e_i18n))

diff_i18n = []
for k in set(r_i18n.keys()) | set(e_i18n.keys()):
    if k not in r_i18n:
        print("Ext only:", k)
    elif k not in e_i18n:
        print("Root only:", k)
    elif r_i18n[k]['sha256'] != e_i18n[k]['sha256']:
        print("Diff:", k)
    else:
        pass

print("All i18n files identical? ", len(r_i18n) == len(e_i18n) and all(r_i18n[k]['sha256'] == e_i18n[k]['sha256'] for k in r_i18n))
