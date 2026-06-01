# VibeZoo Bridge — 멀티랭귀지 AST 엔진
# TS/JS/Python/Go/Rust tree-sitter AST 파서 + regex 폴백
#
# 언어 초기화 시도 순서:
#   1. tree_sitter_languages (통합 패키지, 모든 언어 포함)
#   2. tree-sitter-{lang_name} (개별 언어 패키지)
# 실패 시 조용히 폴백 (에러 아님)

import re
import threading
from typing import Optional

from bridge.config import SOURCE_EXTS, TS_JS_EXTS


class AstEngine:
    """
    멀티랭귀지 tree-sitter AST 파서.
    tree-sitter 미설치 시 regex 폴백 (기존 동작 유지).
    """

    LANGUAGES = {
        '.ts':   'typescript',
        '.tsx':  'typescript',
        '.js':   'javascript',
        '.jsx':  'javascript',
        '.py':   'python',
        '.go':   'go',
        '.rs':   'rust',
    }

    NODE_TYPES = {
        'typescript': {
            'function': ['function_declaration', 'method_definition', 'arrow_function'],
            'class':    ['class_declaration'],
            'interface': ['interface_declaration', 'type_alias_declaration'],
            'import':   ['import_statement', 'import_specifier'],
            'call':     ['call_expression'],
        },
        'python': {
            'function': ['function_definition'],
            'class':    ['class_definition'],
            'import':   ['import_statement', 'import_from_statement'],
            'call':     ['call'],
        },
        'go': {
            'function': ['function_declaration', 'method_declaration'],
            'struct':   ['type_declaration', 'type_spec'],
            'import':   ['import_declaration'],
            'call':     ['call_expression'],
        },
        'rust': {
            'function': ['function_item'],
            'struct':   ['struct_item'],
            'enum':     ['enum_item'],
            'import':   ['use_declaration'],
            'call':     ['call_expression'],
        },
    }

    def __init__(self):
        self._parsers: dict[str, object] = {}
        self._languages: dict[str, object] = {}
        self._initialized: set[str] = set()
        self._init_errors: list[str] = []  # 진단 정보
        self._thread_lock = threading.Lock()
        self._ts_available = False
        self._ts_init_attempted = False

        # 기존 레거시 파서 (단일 TS/JS)
        self._legacy_ts_parser = None
        self._legacy_ts_lang = None
        self._legacy_ts_lang_js = None
        self._legacy_available = False

    # ──────────────────────────────────────────────
    # 1. 언어별 파서 초기화 (Phase C 핵심)
    # ──────────────────────────────────────────────

    def _init_language(self, lang_name: str) -> bool:
        """특정 언어의 tree-sitter 파서를 초기화.

        시도 순서:
        1. tree_sitter_languages (통합 패키지, 모든 언어 포함)
        2. tree-sitter-{lang_name} (개별 언어 패키지)

        실패 시 False 반환 (에러 아님, 조용한 폴백).

        Python/Go/Rust 언어팩 지원:
        - python: tree_sitter_python
        - go:     tree_sitter_go
        - rust:   tree_sitter_rust
        - typescript/javascript: tree_sitter_typescript / tree_sitter_javascript
        """
        # 빠른 경로: 이미 초기화됨 (락 없이 읽기)
        if lang_name in self._initialized:
            return True

        # 락 획득 후 재확인 (DCLP 패턴)
        with self._thread_lock:
            if lang_name in self._initialized:
                return True

            # 방법 1: tree_sitter_languages 통합 패키지
            try:
                from tree_sitter_languages import get_language, get_parser  # type: ignore[import]
                language = get_language(lang_name)
                parser = get_parser(lang_name)
                self._parsers[lang_name] = parser
                self._languages[lang_name] = language
                self._initialized.add(lang_name)
                return True
            except ImportError:
                pass
            except Exception as exc:
                self._init_errors.append(
                    f"[{lang_name}] tree_sitter_languages get_language failed: {exc}"
                )

            # 방법 2: 개별 tree-sitter-{lang} 패키지
            try:
                import importlib
                from tree_sitter import Language, Parser

                lang_module = importlib.import_module(f"tree_sitter_{lang_name}")
                lang_obj = Language(lang_module.language())
                parser = Parser()
                parser.set_language(lang_obj)
                self._parsers[lang_name] = parser
                self._languages[lang_name] = lang_obj
                self._initialized.add(lang_name)
                return True
            except ImportError:
                pass
            except Exception as exc:
                self._init_errors.append(
                    f"[{lang_name}] tree_sitter_{lang_name} failed: {exc}"
                )

            self._init_errors.append(
                f"[{lang_name}] not available (no tree-sitter package found)"
            )
            return False  # 모든 방법 실패

    def get_init_errors(self) -> list[str]:
        """초기화 시도 결과 진단 정보 반환."""
        return list(self._init_errors)

    def get_install_hint(self) -> str:
        """미설치 언어 패키지에 대한 설치 안내 메시지 반환.

        ast_engine 초기화 시 실패한 언어가 있으면
        사용자에게 설치 명령어를 안내한다.
        """
        if not self._init_errors:
            return ""

        missing_langs = set()
        for err in self._init_errors:
            # 에러 메시지에서 언어명 추출 (예: "[python] not available")
            for lang in ['python', 'go', 'rust', 'typescript', 'javascript']:
                if lang in err.lower():
                    missing_langs.add(lang)

        if not missing_langs:
            return ""

        packages = ' '.join(f"tree-sitter-{lang}" for lang in sorted(missing_langs))
        hint = (
            "\n⚠️ **Tree-sitter language packs missing**: "
            f"{', '.join(sorted(missing_langs))}\n"
            f"  Install: `pip install {packages}`\n"
            f"  Or run: `vibezoo_setup(target=\"recommended\")`\n"
            f"  Currently falling back to regex-based analysis (reduced accuracy).\n"
        )
        return hint

    # ──────────────────────────────────────────────
    # 2. 하위 호환 — 기존 레거시 TS/JS 초기화
    # ──────────────────────────────────────────────

    def _init_legacy_tree_sitter(self) -> bool:
        """기존 tree-sitter 초기화 (TS/JS 전용, 하위 호환)"""
        if self._legacy_available and self._legacy_ts_lang is not None:
            return True

        with self._thread_lock:
            if self._legacy_available and self._legacy_ts_lang is not None:
                return True
            if self._ts_init_attempted:
                return self._legacy_available

            self._ts_init_attempted = True

            try:
                import tree_sitter as ts
                self._legacy_ts_parser = ts.Parser()

                try:
                    from tree_sitter_languages import get_language  # type: ignore[import]
                    self._legacy_ts_lang = get_language("typescript")
                    self._legacy_ts_lang_js = get_language("javascript")
                except ImportError:
                    try:
                        from tree_sitter_typescript import language as ts_lang
                        from tree_sitter_javascript import language as js_lang
                        self._legacy_ts_lang = ts_lang()
                        self._legacy_ts_lang_js = js_lang()
                    except ImportError:
                        return False

                self._legacy_available = True
                return True
            except Exception:
                self._legacy_available = False
                return False

    # ──────────────────────────────────────────────
    # 3. 지원 여부 확인
    # ──────────────────────────────────────────────

    def is_available(self, lang: str = None) -> bool:
        """특정 언어(또는 전체) AST 지원 여부.

        - lang=None → 기존처럼 TS/JS legacy 지원 여부
        - lang="python" → python in self._initialized
        - lang="go"     → go in self._initialized
        - lang="rust"   → rust in self._initialized
        - lang="typescript" → typescript in self._initialized or legacy
        - lang="javascript" → javascript in self._initialized or legacy
        """
        if lang is None:
            return self._legacy_available

        # 멀티랭귀지 방식으로 초기화된 경우
        if lang in self._initialized:
            return True

        # TS/JS는 레거시로도 가능
        if lang in ('typescript', 'javascript') and self._legacy_available:
            return True

        return False

    # ──────────────────────────────────────────────
    # 4. 공통 AST 워커
    # ──────────────────────────────────────────────

    def _walk_nodes(self, content: str, lang_name: str, target_types: list[str],
                    field_name: str = "name") -> list[dict]:
        """지정된 노드 타입을 트리에서 찾아 이름+위치 반환."""
        if lang_name not in self._initialized:
            return []

        parser = self._parsers.get(lang_name)
        if parser is None:
            return []

        try:
            tree = parser.parse(bytes(content, "utf-8"))
            root = tree.root_node
        except Exception:
            return []

        results = []

        def walk(node, depth=0):
            if depth > 50:
                return
            if node.type in target_types:
                name_node = node.child_by_field_name(field_name)
                if name_node:
                    start = node.start_point
                    end = node.end_point
                    results.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": start[0] + 1,
                        "end_line": end[0] + 1,
                        "type": node.type,
                    })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return results

    def _walk_calls(self, content: str, lang_name: str) -> list[dict]:
        """호출 노드 추출."""
        if lang_name not in self._initialized:
            return []

        parser = self._parsers.get(lang_name)
        if parser is None:
            return []

        try:
            tree = parser.parse(bytes(content, "utf-8"))
            root = tree.root_node
        except Exception:
            return []

        call_types = self.NODE_TYPES.get(lang_name, {}).get('call', ['call_expression'])
        calls = []

        def walk(node, depth=0):
            if depth > 30:
                return
            if node.type in call_types:
                # Python: call 노드는 function 필드명이 다를 수 있음
                func_node = node.child_by_field_name("function")
                if func_node:
                    name = content[func_node.start_byte:func_node.end_byte]
                    if name not in ("require", "import"):
                        calls.append({
                            "name": name,
                            "line": node.start_point[0] + 1,
                        })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return calls

    def _walk_imports(self, content: str, lang_name: str) -> list[dict]:
        """import 노드 추출."""
        if lang_name not in self._initialized:
            return []

        parser = self._parsers.get(lang_name)
        if parser is None:
            return []

        try:
            tree = parser.parse(bytes(content, "utf-8"))
            root = tree.root_node
        except Exception:
            return []

        import_types = self.NODE_TYPES.get(lang_name, {}).get('import', [])
        imports = []

        def walk(node, depth=0):
            if depth > 30:
                return
            if node.type in import_types:
                if lang_name == 'python':
                    # import X, import X as Y
                    if node.type == 'import_statement':
                        for child in node.children:
                            if child.type == 'dotted_name':
                                module = content[child.start_byte:child.end_byte]
                                imports.append({
                                    "module": module,
                                    "type": "import",
                                    "line": node.start_point[0] + 1,
                                })
                    # from X import Y
                    elif node.type == 'import_from_statement':
                        module_node = node.child_by_field_name("module_name")
                        if module_node:
                            module = content[module_node.start_byte:module_node.end_byte]
                            imports.append({
                                "module": module,
                                "type": "from_import",
                                "line": node.start_point[0] + 1,
                            })
                elif lang_name == 'go':
                    source_node = node.child_by_field_name("source")
                    if source_node:
                        module = content[source_node.start_byte:source_node.end_byte]
                        imports.append({
                            "module": module.strip('"\''),
                            "type": "import",
                            "line": node.start_point[0] + 1,
                        })
                elif lang_name == 'rust':
                    # use X::Y
                    full_text = content[node.start_byte:node.end_byte]
                    imports.append({
                        "module": full_text,
                        "type": "use",
                        "line": node.start_point[0] + 1,
                    })
                else:
                    # TS/JS: import_statement
                    source_node = node.child_by_field_name("source")
                    if source_node:
                        module = content[source_node.start_byte:source_node.end_byte]
                        imports.append({
                            "module": module.strip('"\''),
                            "type": "import",
                            "line": node.start_point[0] + 1,
                        })

            # TS/JS require 호출 처리
            if lang_name in ('typescript', 'javascript'):
                if node.type == "call_expression":
                    func_node = node.child_by_field_name("function")
                    if func_node and content[func_node.start_byte:func_node.end_byte] == "require":
                        args_node = node.child_by_field_name("arguments")
                        if args_node and args_node.children:
                            arg = args_node.children[0]
                            if arg.type == "string":
                                module = content[arg.start_byte:arg.end_byte]
                                imports.append({
                                    "module": module.strip("'\""),
                                    "type": "require",
                                    "line": node.start_point[0] + 1,
                                })
                elif node.type == "import_expression":
                    imports.append({
                        "module": "dynamic import",
                        "type": "import",
                        "line": node.start_point[0] + 1,
                    })

            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return imports

    # ──────────────────────────────────────────────
    # 5. 메인 파싱
    # ──────────────────────────────────────────────

    def parse(self, content: str, file_ext: str) -> dict:
        """파일 전체 파싱 → 구조적 정보 반환.

        지원 확장자:
        - .ts, .tsx, .js, .jsx → TypeScript/JavaScript AST
        - .py                → Python AST
        - .go                → Go AST
        - .rs                → Rust AST
        - 그 외               → 빈 dict (regex fallback에서 사용)
        """
        lang_name = self.LANGUAGES.get(file_ext)
        if lang_name is None:
            return {}

        # 멀티랭귀지 방식 시도
        if self._init_language(lang_name):
            return self._parse_with_language(content, lang_name)

        # TS/JS 레거시 폴백
        if file_ext in TS_JS_EXTS and self._legacy_available:
            return self._parse_legacy_ts(content, file_ext)

        # Python/Go/Rust 레거시 폴백 시도
        if file_ext in TS_JS_EXTS:
            result = self._init_legacy_tree_sitter()
            if result:
                return self._parse_legacy_ts(content, file_ext)

        return {}

    def _parse_with_language(self, content: str, lang_name: str) -> dict:
        """멀티랭귀지 AST 파싱 (공통 워커 활용)."""
        node_types = self.NODE_TYPES.get(lang_name, {})

        functions = self._walk_nodes(
            content, lang_name,
            node_types.get('function', []),
        )
        classes = self._walk_nodes(
            content, lang_name,
            node_types.get('class', []) + node_types.get('struct', []),
        )

        result = {
            "functions": functions,
            "classes": classes,
        }

        # 언어별 추가 정보
        if 'interface' in node_types:
            result["interfaces"] = self._walk_nodes(
                content, lang_name,
                node_types.get('interface', []),
            )
        if 'enum' in node_types:
            result["enums"] = self._walk_nodes(
                content, lang_name,
                node_types.get('enum', []),
            )

        return result

    def _parse_legacy_ts(self, content: str, file_ext: str) -> dict:
        """기존 TS/JS 전용 AST 파싱 (하위 호환)."""
        try:
            lang = self._legacy_ts_lang if file_ext in (".ts", ".tsx") else self._legacy_ts_lang_js
            if not lang:
                return {}
            self._legacy_ts_parser.set_language(lang)
            tree = self._legacy_ts_parser.parse(bytes(content, "utf-8"))
            root = tree.root_node

            functions = []
            classes = []
            interfaces = []

            def walk(node, depth=0):
                if depth > 50:
                    return
                node_type = node.type
                if node_type in ("function_declaration", "method_definition", "arrow_function"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        start = node.start_point
                        end = node.end_point
                        functions.append({
                            "name": content[name_node.start_byte:name_node.end_byte],
                            "line": start[0] + 1,
                            "end_line": end[0] + 1,
                            "type": node_type,
                        })
                elif node_type in ("class_declaration",):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        start = node.start_point
                        end = node.end_point
                        classes.append({
                            "name": content[name_node.start_byte:name_node.end_byte],
                            "line": start[0] + 1,
                            "end_line": end[0] + 1,
                        })
                elif node_type in ("interface_declaration", "type_alias_declaration"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        start = node.start_point
                        end = node.end_point
                        interfaces.append({
                            "name": content[name_node.start_byte:name_node.end_byte],
                            "line": start[0] + 1,
                            "end_line": end[0] + 1,
                            "type": node_type,
                        })
                for child in node.children:
                    walk(child, depth + 1)

            walk(root)
            return {"functions": functions, "classes": classes, "interfaces": interfaces}
        except Exception:
            return {}

    # ──────────────────────────────────────────────
    # 6. 요소별 추출
    # ──────────────────────────────────────────────

    def extract_calls(self, content: str, file_ext: str) -> list:
        """함수 호출 노드 추출 — AST 기반 (멀티랭귀지)."""
        lang_name = self.LANGUAGES.get(file_ext)
        if lang_name is None:
            return []

        # 멀티랭귀지 방식
        if self._init_language(lang_name):
            return self._walk_calls(content, lang_name)

        # TS/JS 레거시 폴백
        if file_ext in TS_JS_EXTS:
            return self._extract_calls_legacy(content, file_ext)

        return []

    def _extract_calls_legacy(self, content: str, file_ext: str) -> list:
        """기존 TS/JS 전용 calls 추출 (하위 호환)."""
        if not self._legacy_available or file_ext not in TS_JS_EXTS:
            return []

        result = self._init_legacy_tree_sitter()
        if not result:
            return []

        try:
            lang = self._legacy_ts_lang if file_ext in (".ts", ".tsx") else self._legacy_ts_lang_js
            if not lang:
                return []
            self._legacy_ts_parser.set_language(lang)
            tree = self._legacy_ts_parser.parse(bytes(content, "utf-8"))
            root = tree.root_node

            calls = []

            def walk(node, depth=0):
                if depth > 30:
                    return
                if node.type == "call_expression":
                    func_node = node.child_by_field_name("function")
                    if func_node:
                        name = content[func_node.start_byte:func_node.end_byte]
                        if name not in ("require", "import"):
                            calls.append({
                                "name": name,
                                "line": node.start_point[0] + 1,
                            })
                for child in node.children:
                    walk(child, depth + 1)

            walk(root)
            return calls
        except Exception:
            return []

    def extract_imports(self, content: str, file_ext: str) -> list:
        """import/require 문 추출 — AST 기반 (멀티랭귀지)."""
        lang_name = self.LANGUAGES.get(file_ext)
        if lang_name is None:
            return []

        # 멀티랭귀지 방식
        if self._init_language(lang_name):
            return self._walk_imports(content, lang_name)

        # TS/JS 레거시 폴백
        if file_ext in TS_JS_EXTS:
            return self._extract_imports_legacy(content, file_ext)

        return []

    def _extract_imports_legacy(self, content: str, file_ext: str) -> list:
        """기존 TS/JS 전용 imports 추출 (하위 호환)."""
        if not self._legacy_available or file_ext not in TS_JS_EXTS:
            return []

        result = self._init_legacy_tree_sitter()
        if not result:
            return []

        try:
            lang = self._legacy_ts_lang if file_ext in (".ts", ".tsx") else self._legacy_ts_lang_js
            if not lang:
                return []
            self._legacy_ts_parser.set_language(lang)
            tree = self._legacy_ts_parser.parse(bytes(content, "utf-8"))
            root = tree.root_node

            imports = []

            def walk(node, depth=0):
                if depth > 30:
                    return
                if node.type == "import_statement":
                    source_node = node.child_by_field_name("source")
                    if source_node:
                        module = content[source_node.start_byte:source_node.end_byte]
                        imports.append({
                            "module": module.strip("'\""),
                            "type": "import",
                            "line": node.start_point[0] + 1,
                        })
                elif node.type == "call_expression":
                    func_node = node.child_by_field_name("function")
                    if func_node and content[func_node.start_byte:func_node.end_byte] == "require":
                        args_node = node.child_by_field_name("arguments")
                        if args_node and args_node.children:
                            arg = args_node.children[0]
                            if arg.type == "string":
                                module = content[arg.start_byte:arg.end_byte]
                                imports.append({
                                    "module": module.strip("'\""),
                                    "type": "require",
                                    "line": node.start_point[0] + 1,
                                })
                elif node.type == "import_expression":
                    imports.append({
                        "module": "dynamic import",
                        "type": "import",
                        "line": node.start_point[0] + 1,
                    })
                for child in node.children:
                    walk(child, depth + 1)

            walk(root)
            return imports
        except Exception:
            return []

    def extract_fields(self, content: str, file_ext: str) -> dict:
        """interface/class의 실제 필드 추출.

        현재는 TS/JS만 지원 (레거시). Python/Go/Rust는 빈 dict 반환.
        """
        if not self._legacy_available or file_ext not in TS_JS_EXTS:
            return {}

        result = self._init_legacy_tree_sitter()
        if not result:
            return {}

        try:
            lang = self._legacy_ts_lang if file_ext in (".ts", ".tsx") else self._legacy_ts_lang_js
            if not lang:
                return {}
            self._legacy_ts_parser.set_language(lang)
            tree = self._legacy_ts_parser.parse(bytes(content, "utf-8"))
            root = tree.root_node

            models = []

            def walk(node, depth=0):
                if depth > 50:
                    return
                if node.type in ("interface_declaration", "class_declaration", "type_alias_declaration"):
                    name_node = node.child_by_field_name("name")
                    name = content[name_node.start_byte:name_node.end_byte] if name_node else "anonymous"

                    fields = []

                    def find_properties(n, d=0):
                        if d > 20:
                            return
                        if n.type == "property_signature":
                            prop_name_node = n.child_by_field_name("name")
                            prop_type_node = n.child_by_field_name("type")
                            if prop_name_node:
                                pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                                ptype = content[prop_type_node.start_byte:prop_type_node.end_byte] if prop_type_node else "any"
                                fields.append({"name": pname, "type": ptype})
                        elif n.type == "method_signature":
                            prop_name_node = n.child_by_field_name("name")
                            if prop_name_node:
                                pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                                fields.append({"name": pname, "type": "method"})
                        elif n.type == "property_definition":
                            prop_name_node = n.child_by_field_name("name")
                            if prop_name_node:
                                pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                                ptype = "any"
                                try:
                                    type_ann = n.child_by_field_name("type")
                                    if type_ann:
                                        ptype = content[type_ann.start_byte:type_ann.end_byte]
                                except Exception:
                                    pass
                                fields.append({"name": pname, "type": ptype})
                        for child in n.children:
                            find_properties(child, d + 1)

                    find_properties(node)
                    models.append({
                        "name": name,
                        "type": node.type,
                        "line": node.start_point[0] + 1,
                        "fields": fields,
                    })
                for child in node.children:
                    walk(child, depth + 1)

            walk(root)
            return {"models": models}
        except Exception:
            return {}

    def extract_functions(self, content: str, file_ext: str) -> list:
        """함수 정의 추출 (AST 우선, regex 폴백)."""
        lang_name = self.LANGUAGES.get(file_ext)
        if lang_name is not None:
            if self._init_language(lang_name):
                node_types = self.NODE_TYPES.get(lang_name, {})
                funcs = self._walk_nodes(
                    content, lang_name,
                    node_types.get('function', []),
                )
                if funcs:
                    return funcs

        # TS/JS 레거시
        if file_ext in TS_JS_EXTS:
            ast = self.parse(content, file_ext)
            if ast.get("functions"):
                return ast["functions"]

        # Regex fallback
        functions = []
        for line in content.split("\n"):
            m = re.search(r'(?:export\s+)?(?:function|async function|def\s+)\s+(\w+)', line)
            if m:
                functions.append({"name": m.group(1), "line": 0, "type": "function"})
        return functions

    def extract_classes(self, content: str, file_ext: str) -> list:
        """클래스 정의 추출 (AST 우선, regex 폴백)."""
        lang_name = self.LANGUAGES.get(file_ext)
        if lang_name is not None:
            if self._init_language(lang_name):
                node_types = self.NODE_TYPES.get(lang_name, {})
                cls = self._walk_nodes(
                    content, lang_name,
                    node_types.get('class', []) + node_types.get('struct', []),
                )
                if cls:
                    return cls

        # TS/JS 레거시
        if file_ext in TS_JS_EXTS:
            ast = self.parse(content, file_ext)
            if ast.get("classes"):
                return ast["classes"]

        classes = []
        for line in content.split("\n"):
            m = re.search(r'\bclass\s+(\w+)', line)
            if m:
                classes.append({"name": m.group(1), "line": 0})
        return classes

    def extract_references(self, symbol: str, content: str, file_ext: str) -> list:
        """심볼 참조 추출 — AST 기반 (줄 단위 폴백)."""
        references = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if symbol in line:
                references.append({
                    "line": i,
                    "content": line.strip()[:200],
                    "type": "reference",
                })

        return references
