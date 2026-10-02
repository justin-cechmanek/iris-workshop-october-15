"""Completed lab 3: use RedisVL with managed LangCache for a public answer.

Run from the repository root: python exercises/lab_3/03_langcache_completed.py
Only fictional, non-personalized policy text is stored.
"""

import os

from dotenv import load_dotenv
from redisvl.extensions.cache.llm import LangCacheSemanticCache


def main():
    load_dotenv()
    first = "How long does the demo store hold my pickup order?"
    similar = "For how many days can I collect a pickup order?"

    cache = LangCacheSemanticCache(
        server_url=os.environ["LANGCACHE_URL"],
        cache_id=os.environ["LANGCACHE_CACHE_ID"],
        api_key=os.environ["LANGCACHE_API_KEY"],
    )
    # RedisVL returns a list of hit dictionaries. A 0.1 normalized distance
    # threshold is strict: smaller distance means a closer semantic match.
    found = cache.check(prompt=first, distance_threshold=0.1)
    print("Before store:", found)
    if not found:
        # This is the fictional answer in data/policies/pickup.md. A real
        # app would generate an answer on the miss, then store that answer.
        answer = (
            "The fictional demo store holds ready-for-pickup retail orders "
            "for seven days."
        )
        entry_id = cache.store(prompt=first, response=answer)
        print("Stored entry:", entry_id)

    # An exact repeat should hit even at a strict threshold. Check it before
    # testing a rephrasing so we know the stored entry is available.
    exact_hits = cache.check(prompt=first, distance_threshold=0.02)
    print("Exact prompt at distance 0.02:", exact_hits)

    # Higher normalized distance allows less similar prompts. Keep the
    # rephrased prompt unchanged and do not store it between checks.
    for threshold in (0.02, 0.10, 0.40):
        related_hits = cache.check(prompt=similar, distance_threshold=threshold)
        status = "HIT" if related_hits else "MISS"
        minimum_similarity = 1.0 - threshold
        print(
            f"Rephrased prompt at distance {threshold:.2f} "
            f"(minimum similarity {minimum_similarity:.2f}): {status}"
        )
        print("Hits:", related_hits)


if __name__ == "__main__":
    main()
