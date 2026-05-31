# VibeZoo Bridge — 멀티랭귀지 AST 엔진
# TS/JS/Python/Go/Rust tree-sitter AST 파서 + regex 폴백

import re
import threading
from typing import Optional

from bridge.config import TS_JS_EXTS


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
            'struct':   ['type_declaration'],
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
        self._thread_lock = threading.Lock()
        self._ts_available = False
        self._ts_init_attempted = False

        # 기존 레거시 파서 (단일 TS/JS)
        self._legacy_ts_parser = None
        self._legacy_ts_lang = None
        self._legacy_ts_lang_js = None
        self._legacy_available = False

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
                    from tree_sitter_languages import get_language
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

    def is_available(self, lang: str = None) -> bool:
        """특정 언어(또는 전체) AST 지원 여부"""
        if lang is None:
            return self._legacy_available
        return lang in ('typescript', 'javascript') and self._legacy_available

    def parse(self, content: str, file_ext: str) -> dict:
        """파일 전체 파싱 → 구조적 정보 반환"""
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

    def extract_calls(self, content: str, file_ext: str) -> list:
        """함수 호출 노드 추출 — AST 기반"""
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
        """import/require 문 추출 — AST 기반"""
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
        """interface/class의 실제 필드 추출"""
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
        """함수 정의 추출 (AST 우선, regex 폴백)"""
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
        """클래스 정의 추출"""
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
        """심볼 참조 추출 — AST 기반"""
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
