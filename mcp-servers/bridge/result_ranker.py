# VibeZoo Bridge — BM25 하이브리드 랭킹
# BM25 + 시그니처 + 위치 기반 결과 정렬

from collections import Counter
from typing import List


class ResultRanker:
    """BM25 + 시그니처 + 위치 기반 하이브리드 랭킹"""

    def rank(self, query: str, results: List[dict]) -> List[dict]:
        """
        각 결과에 score 부여 후 정렬:
        - BM25 유사도 (0.4)
        - 정확 매칭 보너스 (0.3)
        - 위치 가중치: 정의부 > 사용부 (0.2)
        - 주변 컨텍스트 밀도 (0.1)
        """
        for r in results:
            score = 0.0
            score += self._bm25_similarity(query, r.get('content', '')) * 0.4
            score += self._exact_match_bonus(query, r.get('content', '')) * 0.3
            score += self._location_boost(r.get('type', '')) * 0.2
            score += self._context_density(r) * 0.1
            r['score'] = round(score, 4)

        return sorted(results, key=lambda r: r.get('score', 0), reverse=True)

    def _bm25_similarity(self, query: str, text: str, k1: float = 1.5, b: float = 0.75) -> float:
        """BM25 유사도 계산"""
        qw = set(query.lower().split())
        tw = text.lower().split()
        if not qw or not tw:
            return 0.0
        s = 0.0
        avg_len = sum(len(t) for t in tw) / max(len(tw), 1)
        for q in qw:
            tf = tw.count(q) / max(len(tw), 1)
            dl = len(text) / max(avg_len, 1)
            s += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl))
        return min(s / len(qw), 1.0)

    def _exact_match_bonus(self, query: str, text: str) -> float:
        """정확 매칭 보너스"""
        q = query.lower().strip()
        t = text.lower().strip()
        if q == t:
            return 1.0
        if q in t:
            return 0.7
        # 부분 매칭
        q_words = set(q.split())
        t_words = set(t.split())
        if q_words & t_words:
            return 0.3
        return 0.0

    def _location_boost(self, loc_type: str) -> float:
        """위치 가중치: 정의부 > 사용부"""
        boosts = {
            'definition': 1.0,
            'declaration': 0.9,
            'import': 0.6,
            'call': 0.5,
            'reference': 0.4,
            'read': 0.3,
            'write': 0.3,
            'comment': 0.1,
        }
        return boosts.get(loc_type, 0.3)

    def _context_density(self, result: dict) -> float:
        """주변 컨텍스트 밀도"""
        ctx_before = result.get('context_before', [])
        ctx_after = result.get('context_after', [])
        total = len(ctx_before) + len(ctx_after)
        if total == 0:
            return 0.0
        # 컨텍스트가 많을수록 좋음 (최대 3줄)
        return min(total / 3.0, 1.0)
