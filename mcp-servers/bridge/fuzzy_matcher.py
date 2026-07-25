"""Trigram-based fuzzy matching for codebase search — stdlib only."""


def trigram_similarity(a: str, b: str) -> float:
    """Dice coefficient on character 3-grams. Returns 0.0–1.0."""
    if not a or not b:
        return 0.0
    if len(a) < 3 or len(b) < 3:
        # Fall back to substring containment for very short strings
        if a.lower() in b.lower() or b.lower() in a.lower():
            return 1.0
        return 0.0
    a_trigrams = {a[i:i + 3].lower() for i in range(len(a) - 2)}
    b_trigrams = {b[i:i + 3].lower() for i in range(len(b) - 2)}
    intersection = len(a_trigrams & b_trigrams)
    if not a_trigrams or not b_trigrams:
        return 0.0
    return (2.0 * intersection) / (len(a_trigrams) + len(b_trigrams))


def fuzzy_filter(query: str, results: list[dict], threshold: float = 0.35,
                 max_results: int = 50) -> list[dict]:
    """Score each result's content/file against query using trigram similarity.

    Keeps results >= threshold, annotates with fuzzy_score, caps at max_results.
    Pre-caps input at 500 to bound cost.
    """
    if not query or not results:
        return []
    # Pre-cap to bound cost
    candidates = results[:500]
    scored = []
    for r in candidates:
        content = r.get("content", "")
        filename = r.get("file", "")
        # Skip binary/empty content
        if not content and not filename:
            continue
        # Score against content lines and filename
        content_score = max(
            (trigram_similarity(query, line.strip())
             for line in content.split("\n")[:10]),
            default=0.0
        )
        file_score = trigram_similarity(query, filename)
        score = max(content_score, file_score)
        if score >= threshold:
            r["fuzzy_score"] = round(score, 3)
            scored.append(r)
    scored.sort(key=lambda x: x["fuzzy_score"], reverse=True)
    return scored[:max_results]
