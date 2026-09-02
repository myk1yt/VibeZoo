# -*- coding: utf-8 -*-
"""T3 final verification sweep across modernized docs."""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOCS = [
    'README.md', 'README-myk1yt.md',
    'docs/INSTALLATION.md', 'docs/ARCHITECTURE_CORE.md', 'docs/ARCHITECTURE_CORE-myk1yt.md',
    'docs/PROJECT_CONTEXT.md', 'docs/PROJECT_CONTEXT-myk1yt.md',
    'docs/ACTIVE_STATE.md', 'docs/ACTIVE_STATE-myk1yt.md',
]

# Removed tool names must not appear as CURRENT tools.
# Historical/past-tense mentions allowed only in ACTIVE_STATE (cleanup record) and README Changelog (dated).
REMOVED = ['auto_analyze_whiteboard', 'auto_analyze_after_drop',
           'find_bugs', 'findBugs', 'suggest_refactor', 'suggestRefactor',
           'generate_docs', 'generateDocs', 'learn_project', 'learnProject',
           'github_diver', 'read_project_file']

# Stale counts: "40 tools", "39 tools", "38 tools", "19 tools" (tool-context word)
STALE = [r'40 tools', r'39 tools', r'38 tools', r'19 tools', r'\b19 tools\b']

for doc in DOCS:
    p = os.path.join(ROOT, doc)
    src = open(p, encoding='utf-8', errors='replace').read()
    lines = src.splitlines()
    print('===', doc, '(%d lines)' % len(lines))
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for r in REMOVED:
            if r in low:
                print('  REMOVED-NAME hit [%s] L%d: %s' % (r, i, line.strip()[:120]))
        for pat in [r'40\s+tools', r'39\s+tools', r'38\s+tools', r'19\s+tools', r'35\s+tools']:
            if re.search(pat, low):
                print('  STALE-COUNT hit L%d: %s' % (i, line.strip()[:120]))
        # 33 tool presence check (should exist somewhere)
    if '33' not in src and doc != 'docs/INSTALLATION.md':
        print('  WARNING: no 33 mention at all')
print('--- sweep done ---')

# Cross-doc consistency: 33 mentioned in each main doc
for doc in ['README.md', 'README-myk1yt.md', 'docs/PROJECT_CONTEXT.md', 'docs/ACTIVE_STATE.md',
            'docs/ARCHITECTURE_CORE.md', 'docs/ARCHITECTURE_CORE-myk1yt.md', 'docs/ACTIVE_STATE-myk1yt.md',
            'docs/PROJECT_CONTEXT-myk1yt.md']:
    src = open(os.path.join(ROOT, doc), encoding='utf-8', errors='replace').read()
    print(doc, 'mentions-33:', src.count('33'))