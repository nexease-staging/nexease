"""Rank eligible ledger entries locally using statement narration and identifiers."""
from collections import Counter
from datetime import timedelta
from math import log, sqrt
import re

from apps.finance.repositories.bank_transaction_repository import BankTransactionRepository


def words(text):
    return Counter(re.findall(r"[^\W_]+", (text or "").casefold()))


def suggest(line, candidates):
    if not candidates:
        return None
    reference = (line.external_reference or "").strip().casefold()
    exact = [t for t in candidates if reference and (t.external_reference or "").strip().casefold() == reference]
    if exact:
        return (exact[0], "Same reference, amount and direction") if len(exact) == 1 else None
    candidates = [t for t in candidates if not (reference and t.external_reference)]
    if not candidates:
        return None
    query = words(line.description)
    documents = [words(t.description) for t in candidates]
    frequency = Counter(word for doc in documents for word in doc)
    weights = {word: 1 + log((1 + len(documents)) / (1 + frequency[word])) for word in query.keys() | frequency.keys()}
    def norm(vec):
        return sqrt(sum((count * weights[word]) ** 2 for word, count in vec.items()))
    scores = []
    for doc, transaction in zip(documents, candidates):
        denominator = norm(query) * norm(doc)
        score = sum(query[w] * doc[w] * weights[w] ** 2 for w in query.keys() & doc.keys()) / denominator if denominator else 0
        scores.append((score, transaction))
    scores.sort(key=lambda pair: pair[0], reverse=True)
    if scores[0][0] >= .65 and (len(scores) == 1 or scores[0][0] - scores[1][0] >= .2):
        return scores[0][1], "Similar narration, same amount and direction"
    if len(candidates) == 1 and candidates[0].transaction_date.date() == line.transaction_date.date():
        return candidates[0], "Same date, amount and direction"
    return None


def prepare(lines, organization, bank_account, direction_for):
    cache = {}
    proposals = []
    for line in lines:
        direction = direction_for(line)
        key = (line.transaction_date, direction["direction"], direction["amount"])
        if key not in cache:
            cache[key] = list(BankTransactionRepository.list_match_candidates(
                organization=organization, bank_account=bank_account, amount=direction["amount"],
                transaction_types=direction["transaction_types"],
                date_from=line.transaction_date - timedelta(days=2),
                date_to=line.transaction_date + timedelta(days=2),
            ).limit(51))
        candidates = cache[key]
        if len(candidates) <= 50:
            match = suggest(line, candidates)
            if match:
                proposals.append((line, *match))
    uses = Counter(str(transaction.id) for _, transaction, _ in proposals)
    for line, transaction, reason in proposals:
        if uses[str(transaction.id)] == 1:
            line.suggested_id = str(transaction.id)
            line.suggestion_reason = f"{reason} · {transaction.transaction_number}"
