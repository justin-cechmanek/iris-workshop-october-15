"""Lab 2: use RedisVL to check, store, and recheck a public policy answer.

Run from repository root: python exercises/lab_2_langcache/o2_langcache.py
Only fictional, non-personalized policy text is stored.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from redisvl.extensions.cache.llm import LangCacheSemanticCache


def main():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

    first = "How long does the demo store hold my pickup order?"
    similar = "For how many days can I collect a pickup order?"

    # TODO 1: create a LangCacheSemanticCache instance with the server_url,
    # cache_id, and api_key from the .env file.
    # see https://docs.redisvl.com/en/latest/user_guide/13_langcache_semantic_cache.html#:~:text=)%0A%0Acache%20%3D-,LangCacheSemanticCache,-(%0A%20%20%20%20name%3D

    # TODO 2: cache.check(prompt=first, distance_threshold=0.1).
    # RedisVL returns a list of hit dictionaries; an empty list is a miss.

    # TODO 3: On a miss, use the fictional pickup policy to write an answer.
    # Store first + answer with cache.store(prompt=..., response=...).

    # TODO 4: Check first again at distance_threshold=0.02 to confirm the
    # stored prompt can be found. Print the hit list.

    # TODO 5: Check similar at thresholds 0.02, 0.10, and 0.40. For each,
    # print the threshold, HIT or MISS, and the returned hit list.
    # see https://docs.redisvl.com/en/latest/api/cache.html#redisvl.extensions.cache.llm.SemanticCache.check

    raise NotImplementedError("Try LangCache search and set")


if __name__ == "__main__":
    main()
