"""Lab 3: use RedisVL to check, store, and recheck a public policy answer.

Run from repository root: python exercises/lab_3/03_langcache.py
"""

import os

from dotenv import load_dotenv
from redisvl.extensions.cache.llm import LangCacheSemanticCache


def main():
    load_dotenv()
    cache = LangCacheSemanticCache(
        server_url=os.environ["LANGCACHE_URL"],
        cache_id=os.environ["LANGCACHE_CACHE_ID"],
        api_key=os.environ["LANGCACHE_API_KEY"],
    )
    first = "How long does the demo store hold my pickup order?"
    similar = "For how many days can I collect a pickup order?"

    # TODO 1: cache.check(prompt=first, distance_threshold=0.1).
    # RedisVL returns a list of hit dictionaries; an empty list is a miss.
    # TODO 2: On a miss, use the fictional pickup policy to write an answer.
    # Store first + answer with cache.store(prompt=..., response=...).
    # TODO 3: Check the exact and similar prompts; print and compare hit lists.
    # Answers may vary for semantic matches. Never cache personalized details
    # under an unscoped prompt.
    raise NotImplementedError("Try LangCache search and set")


if __name__ == "__main__":
    main()
