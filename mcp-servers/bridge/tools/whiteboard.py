# VibeZoo Bridge — Whiteboard 도구 그룹
# draw_on_whiteboard + get_whiteboard_state + open_whiteboard + capture_screen + open_ui_preview
# + WhiteboardDataConverter (Fabric.js JSON → LLM-readable text)

import json
import os
import time
import math
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Optional

from bridge.config import (
    WHITEBOARD_FILE, WHITEBOARD_ACTION_FILE, UI_ACTION_FILE,
    UPLOADED_IMAGE_PATH, IMAGE_CACHE_DIR,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string,
    _atomic_write_json,
    _truncate,
)
from bridge.crow_client import try_crow_ingest

# ── 드롭존 HTML (Webview 내장) ──────────────────────

_DROPZONE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>VibeZoo Image Drop Zone</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#1e1e1e;color:#ccc;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}
  #dropzone{width:90%;max-width:500px;height:300px;border:3px dashed #4ec9ff;border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:.3s;cursor:pointer;text-align:center;padding:20px}
  #dropzone.dragover{border-color:#6acb6a;background:rgba(106,203,106,.1)}
  #dropzone.has-image{border-style:solid;border-color:#6acb6a}
  #dropzone .icon{font-size:64px;margin-bottom:16px;opacity:.6}
  #dropzone p{font-size:14px;line-height:1.6}
  #dropzone .hint{font-size:12px;color:#888;margin-top:8px}
  #preview{max-width:100%;max-height:200px;display:none;margin-bottom:12px;border-radius:8px}
  #status{font-size:13px;margin-top:12px;padding:8px 16px;border-radius:8px;display:none}
  #status.success{background:#1a3a1a;color:#6acb6a;display:block}
  #status.error{background:#3a1a1a;color:#ff6b6b;display:block}
  input[type=file]{display:none}
</style></head>
<body>
<div id="dropzone" onclick="document.getElementById('fileInput').click()">
  <div class="icon">📸</div>
  <p>Drag & drop an image here<br>or <strong>click to browse</strong></p>
  <p class="hint">Supports: PNG, JPG, GIF, BMP, WEBP</p>
  <img id="preview" alt="Preview"/>
  <div id="status"></div>
</div>
<input type="file" id="fileInput" accept="image/*" onchange="handleFile(this.files[0])"/>
<script>
const dz=document.getElementById('dropzone');
const preview=document.getElementById('preview');
const status=document.getElementById('status');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover')});
dz.addEventListener('dragleave',()=>dz.classList.remove('dragover'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');handleFile(e.dataTransfer.files[0])});
async function handleFile(file){if(!file)return;if(!file.type.startsWith('image/')){showStatus('Not an image file','error');return}
const form=new FormData();form.append('image',file);
try{const r=await fetch('/upload',{method:'POST',body:form});const t=await r.text();showStatus('Uploaded! Use aggregate_spatial_pixels() to analyze.','success');preview.src=URL.createObjectURL(file);preview.style.display='block';dz.classList.add('has-image')}
catch(e){showStatus('Upload failed. Save manually to ~/.vibezoo-cache/dropped_image.png','error')}}
function showStatus(msg,type){status.textContent=msg;status.className=type}
</script></body></html>"""


# ── WhiteboardDataConverter ──────────────────────────────────────────

class WhiteboardDataConverter:
    """
    Fabric.js JSON → LLM-readable 텍스트 변환기.

    Deepseek는 이미지를 직접 볼 수 없으므로, 화이트보드 그림을
    텍스트/수치/코드 형태로 변환하여 LLM이 이해할 수 있게 한다.

    변환 4단계:
    1. extract_objects  — 모든 도형/텍스트/선/그룹/이미지 객체 추출
    2. extract_relationships — 객체 간 연결/포함/근접/정렬 관계
    3. quantize_spatial — 좌표/크기/색상/거리 이산화
    4. to_mermaid      — Mermaid 다이어그램 텍스트 변환
    5. fabric_json_to_text — 전체 파이프라인 통합 → 마크다운 보고서
    """

    # 색상 임계값: HSV 기반 색상명 매핑
    _COLOR_MAP = [
        ((0,   20,   30), "Red"),
        ((20,  40,   30), "Orange"),
        ((40,  70,   30), "Yellow"),
        ((70,  170,  30), "Green"),
        ((170, 260,  30), "Blue"),
        ((260, 300,  30), "Purple"),
        ((300, 360,  30), "Pink"),
    ]

    def __init__(self):
        self._version_detected = None

    # ── 1a. 객체 추출 ──────────────────────────────────

    def extract_objects(self, fabric_json: dict) -> list[dict]:
        """
        Fabric.js JSON에서 모든 객체(도형, 텍스트, 선, 그룹, 이미지) 추출.

        각 객체:
        {id, type, label, x, y, cx, cy, width, height, color, opacity, z_index, children}
        """
        objects = []
        raw_objects = fabric_json.get('objects', [])

        for idx, obj in enumerate(raw_objects):
            obj_type = obj.get('type', 'unknown')
            left = obj.get('left', 0) or 0
            top = obj.get('top', 0) or 0
            scale_x = obj.get('scaleX', 1) or 1
            scale_y = obj.get('scaleY', 1) or 1
            width = (obj.get('width', 0) or 0) * scale_x
            height = (obj.get('height', 0) or 0) * scale_y
            fill = obj.get('fill', obj.get('stroke', '#000000')) or '#000000'
            opacity = obj.get('opacity', 1.0) or 1.0
            z_index = obj.get('zIndex', idx)

            entry = {
                'id': idx,
                'type': obj_type,
                'label': '',
                'x': left,
                'y': top,
                'cx': left + width / 2,
                'cy': top + height / 2,
                'width': width,
                'height': height,
                'color': fill,
                'opacity': opacity,
                'z_index': z_index,
                'children': None,
            }

            # 레이블 추출
            if obj_type in ('text', 'i-text', 'textbox'):
                entry['label'] = obj.get('text', '')
            elif obj_type == 'group' and 'objects' in obj:
                children = self.extract_objects({'objects': obj['objects']})
                entry['children'] = children
                # 그룹 레이블 = 첫 번째 텍스트 자식
                for child in children:
                    if child['type'] in ('text', 'i-text', 'textbox') and child['label']:
                        entry['label'] = child['label']
                        break
                # 그룹 크기 재계산 (자식들의 extents)
                if children:
                    min_x = min(c['x'] for c in children)
                    min_y = min(c['y'] for c in children)
                    max_x = max(c['x'] + c['width'] for c in children)
                    max_y = max(c['y'] + c['height'] for c in children)
                    entry['x'] = min_x
                    entry['y'] = min_y
                    entry['width'] = max_x - min_x
                    entry['height'] = max_y - min_y
                    entry['cx'] = entry['x'] + entry['width'] / 2
                    entry['cy'] = entry['y'] + entry['height'] / 2
            elif obj_type in ('line', 'arrow'):
                # 선의 좌표: x1/y1, x2/y2 속성 사용
                entry['x1'] = obj.get('x1', left)
                entry['y1'] = obj.get('y1', top)
                entry['x2'] = obj.get('x2', left + width)
                entry['y2'] = obj.get('y2', top + height)
                entry['cx'] = (entry['x1'] + entry['x2']) / 2
                entry['cy'] = (entry['y1'] + entry['y2']) / 2
            elif obj_type == 'image':
                entry['src'] = obj.get('src', '')

            objects.append(entry)

        return objects

    # ── 1b. 관계 추출 ──────────────────────────────────

    def extract_relationships(self, fabric_json: dict,
                               objects: list[dict] = None) -> list[dict]:
        """
        객체 간 관계 추출.

        탐지:
        1. 연결선(line/arrow) → 시작/끝점 근처 객체
        2. group 내 포함 관계
        3. 근접 관계 (거리 임계값 이내)
        4. 정렬 관계 (수평/수직 정렬)

        각 관계: {from_id, to_id, from_label, to_label, type, direction, label}
        """
        if objects is None:
            objects = self.extract_objects(fabric_json)

        relationships = []
        threshold = 20  # 픽셀
        proximity_threshold = 60  # 근접 관계 임계값

        # 1. 연결선 분석
        for obj in objects:
            if obj['type'] in ('line', 'arrow'):
                x1, y1 = obj.get('x1', obj['x']), obj.get('y1', obj['y'])
                x2, y2 = obj.get('x2', obj['x'] + obj['width']), obj.get('y2', obj['y'] + obj['height'])

                from_obj = self._find_nearest_object(x1, y1, objects, threshold, exclude=obj['id'])
                to_obj = self._find_nearest_object(x2, y2, objects, threshold, exclude=obj['id'])

                # 방향 판단
                dx = x2 - x1
                dy = y2 - y1
                direction = '→'
                if abs(dx) < abs(dy):
                    direction = '↓' if dy > 0 else '↑'
                elif dx < 0:
                    direction = '←'

                # 연결선 자체의 레이블 (텍스트가 속성으로 있는 경우)
                line_label = obj.get('label', '')

                if from_obj and to_obj:
                    rel = {
                        'from_id': from_obj['id'],
                        'to_id': to_obj['id'],
                        'from_label': from_obj['label'],
                        'to_label': to_obj['label'],
                        'type': 'connection',
                        'direction': direction,
                        'label': line_label,
                    }
                    # 중복 방지
                    if not any(r['from_id'] == rel['from_id'] and r['to_id'] == rel['to_id']
                               and r['type'] == 'connection' for r in relationships):
                        relationships.append(rel)
                elif from_obj and not to_obj:
                    # 시작점만 연결됨 → 단방향
                    relationships.append({
                        'from_id': from_obj['id'],
                        'to_id': obj['id'],
                        'from_label': from_obj['label'],
                        'to_label': '',
                        'type': 'connection',
                        'direction': direction,
                        'label': line_label,
                    })

        # 2. 포함 관계
        for obj in objects:
            if obj['type'] == 'group' and obj['children']:
                for child in obj['children']:
                    if child['type'] not in ('line', 'arrow'):
                        relationships.append({
                            'from_id': obj['id'],
                            'to_id': child['id'],
                            'from_label': obj['label'],
                            'to_label': child['label'],
                            'type': 'containment',
                            'direction': 'contains',
                            'label': '',
                        })

        # 3. 근접 관계 (선/화살표가 아닌 객체들 사이)
        non_line_objs = [o for o in objects if o['type'] not in ('line', 'arrow')]
        for i, a in enumerate(non_line_objs):
            for b in non_line_objs[i + 1:]:
                dist = math.hypot(a['cx'] - b['cx'], a['cy'] - b['cy'])
                if dist < proximity_threshold:
                    # 중복 방지: 이미 connection 관계가 있으면 스킵
                    already_connected = any(
                        r['type'] == 'connection'
                        and ((r['from_id'] == a['id'] and r['to_id'] == b['id'])
                             or (r['from_id'] == b['id'] and r['to_id'] == a['id']))
                        for r in relationships
                    )
                    if not already_connected:
                        relationships.append({
                            'from_id': a['id'],
                            'to_id': b['id'],
                            'from_label': a['label'],
                            'to_label': b['label'],
                            'type': 'proximity',
                            'direction': '↔',
                            'label': f'dist={int(dist)}px',
                        })

        # 4. 정렬 관계 (수평/수직 정렬)
        for i, a in enumerate(non_line_objs):
            for b in non_line_objs[i + 1:]:
                if a['type'] == b['type']:
                    # 수평 정렬: y 중심이 비슷
                    if abs(a['cy'] - b['cy']) < 15:
                        relationships.append({
                            'from_id': a['id'],
                            'to_id': b['id'],
                            'from_label': a['label'],
                            'to_label': b['label'],
                            'type': 'alignment',
                            'direction': '↔',
                            'label': 'horizontal-align',
                        })
                    # 수직 정렬: x 중심이 비슷
                    elif abs(a['cx'] - b['cx']) < 15:
                        relationships.append({
                            'from_id': a['id'],
                            'to_id': b['id'],
                            'from_label': a['label'],
                            'to_label': b['label'],
                            'type': 'alignment',
                            'direction': '↕',
                            'label': 'vertical-align',
                        })

        return relationships

    # ── 1c. 공간 데이터 이산화 ─────────────────────────

    def quantize_spatial(self, objects: list[dict]) -> dict:
        """
        공간 데이터 이산화 — LLM이 이해할 수 있는 수치/범주 표현.

        - 좌표 → 그리드 위치 (top/middle/bottom × left/center/right)
        - 크기 → small/medium/large
        - 색상 → 색상명 (Red, Blue, Green, ...)
        - 거리 → adjacent/near/distant
        """
        if not objects:
            return {
                'grid_positions': [],
                'total_area': '0×0',
                'object_count': 0,
                'layout_summary': 'Empty canvas',
            }

        # 선/화살표 제외한 객체로 영역 계산
        content_objs = [o for o in objects if o['type'] not in ('line', 'arrow')]
        if not content_objs:
            return {
                'grid_positions': [],
                'total_area': '0×0',
                'object_count': 0,
                'layout_summary': 'Only lines/arrows (no content objects)',
            }

        all_x = [o['cx'] for o in content_objs]
        all_y = [o['cy'] for o in content_objs]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        range_x = max_x - min_x if max_x > min_x else 1
        range_y = max_y - min_y if max_y > min_y else 1

        grid_positions = []
        for obj in content_objs:
            # 수평 위치 (3분할)
            rx = (obj['cx'] - min_x) / range_x
            if rx < 0.33:
                hpos = "left"
            elif rx < 0.67:
                hpos = "center"
            else:
                hpos = "right"

            # 수직 위치 (3분할)
            ry = (obj['cy'] - min_y) / range_y
            if ry < 0.33:
                vpos = "top"
            elif ry < 0.67:
                vpos = "middle"
            else:
                vpos = "bottom"

            # 크기 (area 기반)
            area = obj['width'] * obj['height']
            if area < 5000:
                size = "small"
            elif area < 20000:
                size = "medium"
            elif area < 50000:
                size = "large"
            else:
                size = "xlarge"

            grid_positions.append({
                'id': obj['id'],
                'label': obj['label'] or f"{obj['type']}#{obj['id']}",
                'grid': f"({vpos}-{hpos})",
                'size': size,
                'color': self._color_name(obj['color']),
            })

        # 레이아웃 요약
        rows = {}
        for gp in grid_positions:
            v = gp['grid'].split('-')[0].lstrip('(')
            rows.setdefault(v, []).append(gp['label'] or gp['grid'])

        layout_parts = []
        for pos in ['top', 'middle', 'bottom']:
            if pos in rows:
                layout_parts.append(f"Row {pos}: [{', '.join(rows[pos])}]")

        return {
            'grid_positions': grid_positions,
            'total_area': f"{int(range_x)}×{int(range_y)}",
            'object_count': len(grid_positions),
            'layout_summary': ' | '.join(layout_parts) if layout_parts else 'No structured layout',
        }

    # ── 1d. Mermaid 변환 ───────────────────────────────

    def to_mermaid(self, fabric_json: dict) -> str:
        """
        Fabric.js JSON → Mermaid 다이어그램 텍스트 변환.

        자동 감지:
        - 사각형 + 연결선 위주 → flowchart
        - 계층 구조 (group) → graph TD
        - 순환 구조 → graph LR
        - 텍스트 위주 → sequence diagram (추정)
        """
        objects = self.extract_objects(fabric_json)
        relationships = self.extract_relationships(fabric_json, objects)

        if not objects:
            return "```mermaid\nflowchart LR\n    empty[Empty Canvas]\n```"

        # 다이어그램 타입 추론
        has_cycles = self._detect_cycles(relationships)
        has_hierarchy = any(r['type'] == 'containment' for r in relationships)
        has_connections = any(r['type'] == 'connection' for r in relationships)
        direction = "LR" if has_cycles else "TD"

        lines = ["```mermaid", f"graph {direction}"]

        # 노드 정의 (content objects만)
        content_objs = [o for o in objects if o['type'] not in ('line', 'arrow')]
        for obj in content_objs:
            node_id = f"n{obj['id']}"
            label = obj['label'] or f"{obj['type']}#{obj['id']}"
            # 특수문자 이스케이프
            label = label.replace('"', "'").replace('\n', ' ').strip()
            if not label:
                label = f"obj{obj['id']}"

            if obj['type'] == 'rect':
                lines.append(f"    {node_id}[\"{label}\"]")
            elif obj['type'] == 'circle':
                lines.append(f"    {node_id}{{\"{label}\"}}")
            elif obj['type'] == 'ellipse':
                lines.append(f"    {node_id}(\"{label}\")")
            elif obj['type'] == 'triangle':
                lines.append(f"    {node_id}[/\"{label}\\]")
            elif obj['type'] in ('text', 'i-text', 'textbox'):
                lines.append(f"    {node_id}[\"{label}\"]")
            elif obj['type'] == 'group':
                lines.append(f"    subgraph {node_id}[\"{label}\"]")
                # 자식 노드들은 subgraph 내부
                if obj['children']:
                    for child in obj['children']:
                        if child['type'] not in ('line', 'arrow', 'group'):
                            cid = f"n{child['id']}"
                            clabel = child['label'] or f"{child['type']}#{child['id']}"
                            clabel = clabel.replace('"', "'").replace('\n', ' ').strip()
                            lines.append(f"        {cid}[\"{clabel}\"]")
                lines.append("    end")
            else:
                lines.append(f"    {node_id}[\"{label}\"]")

        # 엣지 정의
        for rel in relationships:
            if rel['type'] == 'connection':
                from_id = f"n{rel['from_id']}"
                to_id = f"n{rel['to_id']}"
                edge_label = rel.get('label', '')
                if edge_label:
                    lines.append(f"    {from_id} -->|\"{edge_label}\"| {to_id}")
                else:
                    lines.append(f"    {from_id} --> {to_id}")

        lines.append("```")
        return "\n".join(lines)

    # ── 1e. 전체 파이프라인 통합 ────────────────────────

    def fabric_json_to_text(self, fabric_json: dict) -> str:
        """
        전체 파이프라인 통합 → 구조화된 마크다운 보고서.

        출력:
        ## Whiteboard Contents (N objects, M relationships)

        ### Objects
        | # | Type | Label | Position | Size | Color |

        ### Relationships
        - Service ──depends on──▶ Database

        ### Spatial Layout
        ### Mermaid Diagram
        """
        objects = self.extract_objects(fabric_json)
        relationships = self.extract_relationships(fabric_json, objects)
        spatial = self.quantize_spatial(objects)
        mermaid = self.to_mermaid(fabric_json)

        return self._format_report(objects, relationships, spatial, mermaid)

    # ── 내부 헬퍼 ─────────────────────────────────────

    def _find_nearest_object(self, x: float, y: float,
                              objects: list[dict],
                              threshold: float = 20,
                              exclude: int = None) -> Optional[dict]:
        """주어진 좌표에서 가장 가까운 객체 찾기 (임계값 이내)"""
        best = None
        best_dist = float('inf')

        for obj in objects:
            if obj['id'] == exclude:
                continue
            if obj['type'] in ('line', 'arrow'):
                continue  # 선은 연결 대상에서 제외

            # 객체 중심까지 거리
            dist = math.hypot(x - obj['cx'], y - obj['cy'])
            if dist < best_dist:
                best_dist = dist
                best = obj

        if best and best_dist <= threshold:
            return best
        return None

    def _color_name(self, hex_color: str) -> str:
        """HEX 색상 → 색상명 변환"""
        if not hex_color or hex_color == 'transparent':
            return 'Transparent'

        # HEX → RGB
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        if len(hex_color) < 6:
            return 'Unknown'

        try:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        except ValueError:
            return 'Unknown'

        # 흑백 판단
        if max(r, g, b) < 30:
            return 'Black'
        if min(r, g, b) > 230:
            return 'White'
        if abs(r - g) < 20 and abs(g - b) < 20 and max(r, g, b) > 100:
            return 'Gray'

        # 기본 색상명
        if r > 180 and g < 100 and b < 100:
            return 'Red'
        if r > 180 and g > 120 and b < 80:
            return 'Orange'
        if r > 180 and g > 180 and b < 80:
            return 'Yellow'
        if r < 80 and g > 120 and b < 80:
            return 'Green'
        if r < 80 and g < 100 and b > 150:
            return 'Blue'
        if r > 120 and g < 80 and b > 120:
            return 'Purple'
        if r > 200 and g < 150 and b > 200:
            return 'Pink'
        if r < 100 and g < 60 and b < 60:
            return 'DarkRed'
        if r < 60 and g < 100 and b < 60:
            return 'DarkGreen'
        if r < 60 and g < 60 and b < 100:
            return 'DarkBlue'

        # 유사도 기반 매칭
        named = {
            'Red': (255, 0, 0), 'Green': (0, 128, 0), 'Blue': (0, 0, 255),
            'Yellow': (255, 255, 0), 'Cyan': (0, 255, 255), 'Magenta': (255, 0, 255),
            'Orange': (255, 165, 0), 'Purple': (128, 0, 128), 'Pink': (255, 192, 203),
            'Brown': (165, 42, 42), 'Gray': (128, 128, 128), 'White': (255, 255, 255),
            'Black': (0, 0, 0), 'Navy': (0, 0, 128), 'Teal': (0, 128, 128),
        }
        best_name = 'Unknown'
        best_dist = float('inf')
        for name, (nr, ng, nb) in named.items():
            d = math.sqrt((r - nr) ** 2 + (g - ng) ** 2 + (b - nb) ** 2)
            if d < best_dist:
                best_dist = d
                best_name = name

        return best_name if best_dist < 200 else f'RGB({r},{g},{b})'

    def _detect_cycles(self, relationships: list[dict]) -> bool:
        """관계 그래프에 순환 존재 여부 (DFS)"""
        # 인접 리스트 구축
        adj = {}
        for rel in relationships:
            if rel['type'] == 'connection':
                adj.setdefault(rel['from_id'], []).append(rel['to_id'])

        # DFS for cycles
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in adj:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def _format_report(self, objects: list[dict],
                        relationships: list[dict],
                        spatial: dict,
                        mermaid: str) -> str:
        """통합 마크다운 보고서 생성"""
        lines = []

        # 헤더
        obj_count = len([o for o in objects if o['type'] not in ('line', 'arrow')])
        rel_count = len(relationships)
        lines.append(f"## Whiteboard Contents ({obj_count} objects, {rel_count} relationships)")
        lines.append("")

        # --- 객체 목록 ---
        lines.append("### Objects")
        lines.append("| # | Type | Label | Position (cx,cy) | Size (w×h) | Color |")
        lines.append("|---|------|-------|-----------------|-------------|-------|")

        content_objs = [o for o in objects if o['type'] not in ('line', 'arrow')]
        for i, obj in enumerate(content_objs, 1):
            label = obj['label'] or ''
            if len(label) > 30:
                label = label[:30] + '…'
            pos = f"({int(obj['cx'])},{int(obj['cy'])})"
            size = f"{int(obj['width'])}×{int(obj['height'])}" if obj['width'] and obj['height'] else '—'
            color = self._color_name(obj['color'])
            lines.append(f"| {i} | {obj['type']} | {label} | {pos} | {size} | {color} |")

        # --- 관계 ---
        if relationships:
            lines.append("")
            lines.append("### Relationships")
            for rel in relationships:
                from_lbl = rel['from_label'] or f"obj#{rel['from_id']}"
                to_lbl = rel['to_label'] or f"obj#{rel['to_id']}"
                if rel['type'] == 'connection':
                    lines.append(f"- `{from_lbl}` ──{rel.get('label', '')}──▶ `{to_lbl}`")
                elif rel['type'] == 'containment':
                    lines.append(f"- `{from_lbl}` contains `{to_lbl}`")
                elif rel['type'] == 'proximity':
                    lines.append(f"- `{from_lbl}` near `{to_lbl}` ({rel.get('label', '')})")
                elif rel['type'] == 'alignment':
                    lines.append(f"- `{from_lbl}` {rel.get('label', '')} with `{to_lbl}`")

        # --- 공간 레이아웃 ---
        if spatial and spatial.get('layout_summary'):
            lines.append("")
            lines.append("### Spatial Layout")
            lines.append(f"- Area: {spatial.get('total_area', '?')} px")
            lines.append(f"- {spatial['layout_summary']}")
            if spatial.get('grid_positions'):
                # 그리드 테이블
                lines.append("")
                lines.append("| Object | Grid | Size | Color |")
                lines.append("|--------|------|------|-------|")
                for gp in spatial['grid_positions']:
                    lines.append(f"| {gp['label']} | {gp['grid']} | {gp['size']} | {gp['color']} |")

        # --- Mermaid ---
        lines.append("")
        lines.append("### Mermaid Diagram")
        lines.append(mermaid)

        return "\n".join(lines)


# ── 싱글톤 인스턴스 ──────────────────────────────────

_converter = WhiteboardDataConverter()


# ── 내부 구현 함수 ──────────────────────────────────


def _capture_screen_impl() -> str:
    """화면 캡처 실제 구현 (3단계 fallback)"""
    img = None
    width = 0
    height = 0

    # 방법 1: PIL ImageGrab (가장 안정적)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        width, height = img.size
    except ImportError:
        pass

    # 방법 2: Windows PowerShell fallback
    if img is None and os.name == 'nt':
        try:
            import subprocess
            import base64

            ps_script = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size)
$ms = New-Object System.IO.MemoryStream
$bitmap.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$graphics.Dispose()
[System.Convert]::ToBase64String($ms.ToArray())
"""
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                b64_data = result.stdout.strip()
                from PIL import Image
                import io
                img_bytes = base64.b64decode(b64_data)
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
        except Exception:
            pass

    # 방법 3: mss 라이브러리 (PIL 대체)
    if img is None:
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                from PIL import Image
                img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
                width, height = img.size
        except ImportError:
            pass

    if img is None:
        return (_markdown_header("Screen Capture Error", "❌")
                + "**No screen capture method available.**\n\n"
                + "Install Pillow: `pip install Pillow`\n"
                + "Or on Windows: ensure PowerShell 5+ is available.\n"
                + _markdown_footer())

    try:
        import base64
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        data = {
            "timestamp": time.time(),
            "type": "screenshot",
            "image": f"data:image/png;base64,{img_b64}",
            "width": width,
            "height": height,
        }
        _atomic_write_json(WHITEBOARD_FILE, data, indent=2)

        output = (_markdown_header("Screen Capture")
                  + f"Screen captured ({width}x{height}). Image saved to whiteboard.\n\n"
                  + f"Use `get_whiteboard_state()` to view the captured content.\n")
        try_crow_ingest(f"Screen captured: {width}x{height}", register="context")
        output += _markdown_footer()
        return output
    except Exception as e:
        return (_markdown_header("Screen Capture Error", "❌")
                + f"**Capture failed:** `{e}`\n"
                + _markdown_footer())


def _open_dropzone_in_webview() -> str:
    """VS Code Webview 내장 드롭존 열기 (open_image_dropzone 통합)"""
    from base64 import b64encode

    html_b64 = b64encode(_DROPZONE_HTML.encode('utf-8')).decode('utf-8')

    data = {
        "action": "open_dropzone",
        "html_b64": html_b64,
        "title": "VibeZoo Image Drop Zone",
        "timestamp": time.time(),
    }
    _atomic_write_json(WHITEBOARD_ACTION_FILE, data, indent=2)

    return (_markdown_header("Image Drop Zone", "📸")
            + "Drop zone opened in VS Code Webview.\n\n"
            + "1. Drag & drop an image into the Webview\n"
            + "2. Image will be saved to `~/.vibezoo-cache/dropped_image.png`\n"
            + "3. Then call `aggregate_spatial_pixels(image_path='...')` to analyze\n\n"
            + "💡 **Tip**: Use `capture_screen()` (without arguments) to capture your screen directly.\n"
            + _markdown_footer())


def _open_file_picker() -> str:
    """파일 선택 다이얼로그 열기"""
    data = {
        "action": "open_file_picker",
        "title": "VibeZoo Image File Picker",
        "timestamp": time.time(),
    }
    _atomic_write_json(WHITEBOARD_ACTION_FILE, data, indent=2)

    return (_markdown_header("File Picker", "📁")
            + "File picker opened in VS Code Webview.\n\n"
            + "1. Select an image file from the file picker\n"
            + "2. Image will be saved to `~/.vibezoo-cache/dropped_image.png`\n"
            + "3. Then call `aggregate_spatial_pixels(image_path='...')` to analyze\n"
            + _markdown_footer())


# ── 도구 등록 ────────────────────────────────────────

def register(mcp):
    """Whiteboard 도구 등록"""

    @mcp.tool
    def capture_screen(source: str = "screen") -> str:
        """화면을 캡처하여 화이트보드에 자동으로 붙여넣습니다. AI가 시각적 분석이 필요할 때 호출합니다.
        source="dropzone" 시 VS Code Webview 드롭존을 열어 이미지를 업로드할 수 있습니다.

        Args:
            source: "screen" (화면 캡처) | "dropzone" (드롭존 열기) | "file" (파일 선택)
        """
        if source == "dropzone":
            return _open_dropzone_in_webview()
        elif source == "file":
            return _open_file_picker()

        # 기본: 화면 캡처
        return _capture_screen_impl()

    @mcp.tool
    def draw_on_whiteboard(commands: str) -> str:
        """AI가 화이트보드에 그림을 그립니다. VibeZoo가 이 명령을 받아 Webview에 렌더링합니다.

        Args:
            commands: JSON 배열 형태의 Fabric.js 드로잉 명령.
                     각 명령: {"type":"rect|circle|line|text|arrow|freehand|clear", "props":{...}}
        """
        err = _validate_string(commands, "commands")
        if err:
            return _markdown_header("Whiteboard Error", "❌") + f"**{err}**\n" + _markdown_footer()

        try:
            parsed = json.loads(commands)
            if not isinstance(parsed, list):
                return (_markdown_header("Whiteboard Error", "❌")
                        + "**Commands must be a JSON array.**\n"
                        + _markdown_footer())
        except json.JSONDecodeError as e:
            return (_markdown_header("Whiteboard Error", "❌")
                    + f"**Invalid JSON:** `{e}`\n"
                    + _markdown_footer())

        try:
            data = {"timestamp": time.time(), "commands": parsed}
            _atomic_write_json(WHITEBOARD_FILE, data, indent=2)
            try_crow_ingest(f"Whiteboard: {len(parsed)} drawing commands", register="context")
            return (_markdown_header("Whiteboard Drawing")
                    + f"Drew {len(parsed)} shapes on whiteboard.\n"
                    + _markdown_footer())
        except Exception as e:
            return (_markdown_header("Whiteboard Error", "❌")
                    + f"**Failed to draw:** `{e}`\n"
                    + _markdown_footer())

    @mcp.tool
    def get_whiteboard_state() -> str:
        """현재 화이트보드의 상태를 조회합니다. 사용자가 수정한 내용을 확인합니다."""
        try:
            if not os.path.exists(WHITEBOARD_FILE):
                return (_markdown_header("Whiteboard State")
                        + "Whiteboard is empty.\n"
                        + _markdown_footer())

            with open(WHITEBOARD_FILE) as f:
                data = json.load(f)

            # 데이터 타입에 따라 다른 처리
            if "image" in data:
                # 스크린샷 데이터
                width = data.get("width", 0)
                height = data.get("height", 0)
                output = (_markdown_header("Whiteboard State")
                          + f"**Screenshot** ({width}×{height}px)\n\n"
                          + f"Use `aggregate_spatial_pixels()` with the saved image path "
                          + f"for detailed spatial analysis.\n\n"
                          + f"Raw JSON (truncated):\n"
                          + f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}\n```\n")
                try_crow_ingest(f"Whiteboard state: screenshot {width}x{height}", register="context")
                output += _markdown_footer()
                return output

            if "commands" in data and data["commands"]:
                # Fabric.js 명령어 → WhiteboardDataConverter로 변환
                fabric_json = {"objects": data["commands"]}
                try:
                    report = _converter.fabric_json_to_text(fabric_json)
                    output = (_markdown_header("Whiteboard State")
                              + report + "\n\n"
                              + "**Raw JSON (truncated):**\n"
                              + f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}\n```\n")
                    try_crow_ingest(f"Whiteboard state: analyzed {len(data['commands'])} commands",
                                    register="context")
                    output += _markdown_footer()
                    return output
                except Exception as conv_err:
                    # 변환 실패 시 fallback: raw JSON
                    pass

            # Fallback: raw JSON만 표시
            commands_count = len(data.get("commands", [])) if isinstance(data.get("commands"), list) else 0
            output = (_markdown_header("Whiteboard State")
                      + f"Whiteboard has {commands_count} objects.\n\n"
                      + f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}\n```\n")
            output += _markdown_footer()
            return output

        except Exception as e:
            return (_markdown_header("Whiteboard Error", "❌")
                    + f"**Failed:** `{e}`\n"
                    + _markdown_footer())

    @mcp.tool
    def open_whiteboard(message: str = "") -> str:
        """VibeZoo 화이트보드를 엽니다. AI가 시각적 설명이 필요할 때 호출합니다."""
        try:
            data = {"action": "open", "message": message, "timestamp": time.time()}
            _atomic_write_json(WHITEBOARD_ACTION_FILE, data, indent=2)
            try_crow_ingest(f"Whiteboard opened: {message[:100]}" if message else "Whiteboard opened",
                            register="context")
            return (_markdown_header("Whiteboard")
                    + f"Whiteboard opened. {message}\n"
                    + _markdown_footer())
        except Exception as e:
            return (_markdown_header("Whiteboard Error", "❌")
                    + f"**Failed:** `{e}`\n"
                    + _markdown_footer())

    @mcp.tool
    def open_ui_preview(code: str = "", framework: str = "react") -> str:
        """UI Preview 패널을 열고 코드를 렌더링합니다."""
        try:
            data = {"action": "open_ui", "code": code, "framework": framework, "timestamp": time.time()}
            _atomic_write_json(UI_ACTION_FILE, data, indent=2)
            try_crow_ingest(f"UI Preview opened: {framework}", register="context")
            return (_markdown_header("UI Preview")
                    + f"UI Preview opened. Rendering {framework} component.\n"
                    + _markdown_footer())
        except Exception as e:
            return (_markdown_header("UI Preview Error", "❌")
                    + f"**Failed:** `{e}`\n"
                    + _markdown_footer())
