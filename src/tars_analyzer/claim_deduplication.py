from __future__ import annotations

import re
from collections import Counter

from .models import Conversation, ConversationClaimDedup, DedupedClaim


_SENTENCE_SPLIT = re.compile(r"[.!?\n]+")
_TOKEN = re.compile(r"[a-z0-9]+")


def _normalize(text: str) -> str:
    tokens = _TOKEN.findall(text.lower())
    return " ".join(tokens)


def _extract_claims(conversation: Conversation) -> list[str]:
    claims: list[str] = []
    for turn in conversation.turns:
        if turn.role.lower() != "agent":
            continue
        for sentence in _SENTENCE_SPLIT.split(turn.content):
            normalized = _normalize(sentence)
            if len(normalized.split()) >= 5:
                claims.append(normalized)
    return claims


def _ngram_set(text: str, n: int = 3) -> set[str]:
    words = text.split()
    if len(words) < n:
        return set(words)
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _cosine(text_a: str, text_b: str) -> float:
    counts_a = Counter(text_a.split())
    counts_b = Counter(text_b.split())
    if not counts_a or not counts_b:
        return 0.0

    terms = set(counts_a) | set(counts_b)
    dot = sum(counts_a[t] * counts_b[t] for t in terms)
    mag_a = sum(v * v for v in counts_a.values()) ** 0.5
    mag_b = sum(v * v for v in counts_b.values()) ** 0.5
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _claim_similarity(claim_a: str, claim_b: str) -> float:
    ngram_sim = _jaccard(_ngram_set(claim_a), _ngram_set(claim_b))
    cosine_sim = _cosine(claim_a, claim_b)
    return max(ngram_sim, cosine_sim)


def analyze_claim_deduplication(
    conversations: list[Conversation], similarity_threshold: float = 0.85
) -> list[ConversationClaimDedup]:
    seen_claims: list[str] = []
    results: list[ConversationClaimDedup] = []

    for convo in conversations:
        claims = _extract_claims(convo)
        repeated_items: list[DedupedClaim] = []

        for claim in claims:
            best_previous = ""
            best_similarity = 0.0
            for previous in seen_claims:
                similarity = _claim_similarity(claim, previous)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_previous = previous

            if best_similarity >= similarity_threshold:
                repeated_items.append(
                    DedupedClaim(
                        claim=claim,
                        matched_previous_claim=best_previous,
                        similarity=round(best_similarity, 3),
                    )
                )

        total = len(claims)
        repeated = len(repeated_items)
        novel = max(0, total - repeated)
        ratio = round((repeated / total), 3) if total else 0.0
        results.append(
            ConversationClaimDedup(
                conversation_id=convo.conversation_id,
                total_claims=total,
                repeated_claims=repeated,
                novel_claims=novel,
                repetition_ratio=ratio,
                repeated_items=repeated_items,
            )
        )
        seen_claims.extend(claims)

    return results
