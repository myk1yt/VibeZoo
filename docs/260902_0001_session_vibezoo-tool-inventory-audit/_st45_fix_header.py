# -*- coding: utf-8 -*-
"""Fix integrated.py header comment to avoid removed tool names (grep-0 requirement)."""
import io

OLD = "# review_project (find_bugs/suggest_refactor/generate_docs \uc81c\uac70 \u2014 \ud504\ub86c\ud504\ud2b8 \uc870\ud569\uc73c\ub85c \ub300\uccb4, plan \u00a74)\n"
NEW = "# review_project \u2014 \uc9d1\uacc4\ud615 \ub3c4\uad6c \uc81c\uac70 \ub4a4 \ub0a8\uc740 \ud1b5\ud569 \ub3c4\uad6c (\ub9e4\ub274\uc5bc \uc870\ud569 \uc9c0\uce68\uc740 plan \u00a74 \ucc38\uc870)\n"

for p in ["mcp-servers/bridge/tools/integrated.py",
          "extension/mcp-servers/bridge/tools/integrated.py"]:
    with io.open(p, "r", encoding="utf-8") as f:
        text = f.read()
    assert OLD in text, "header anchor not found in %s" % p
    text = text.replace(OLD, NEW if False else NEW, 1)
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("fixed header: %s" % p)