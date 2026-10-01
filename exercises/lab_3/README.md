# Lab 3: LangCache

**Goal:** serve a repeated public policy answer from managed LangCache through RedisVL. Allow about 20 minutes. Read the fictional [`pickup policy`](../../data/policies/pickup.md).

**Pace:** 5 minutes to create the service, 10 to code and compare searches, 5 to explain the result.

## Service setup

In Redis Cloud, open **LangCache** and create a service on the workshop database. **Quick create** can use a Free 30 MB database. Copy the service API key when it appears; Redis displays it only once. On the service **Configuration** page, copy the base URL and cache ID from **Connectivity**. Put them in `.env` as `LANGCACHE_URL`, `LANGCACHE_CACHE_ID`, and `LANGCACHE_API_KEY`. [Create service](https://redis.io/docs/latest/operate/rc/langcache/create-service/) and [find credentials](https://redis.io/docs/latest/operate/rc/langcache/use-langcache/).

**Predict before coding:** Will two questions with different wording always return the same cached answer? What might happen when you raise RedisVL's distance threshold?

## Exercise

Edit [`03_langcache.py`](03_langcache.py):

1. Construct RedisVL's `LangCacheSemanticCache` with the service URL, cache ID, and API key. It wraps the managed LangCache API; it does not create a second Redis index.
2. Call `cache.check(prompt=first, distance_threshold=0.1)` and print the returned list of hit dictionaries. With RedisVL's default normalized distance scale, `0.1` means a minimum LangCache similarity of `0.9`. An empty list is a miss.
3. On a miss, write a short answer supported by the sample pickup policy. Store the pair with `cache.store(prompt=first, response=answer)`.
4. Check the same prompt again, then check the rephrased prompt. Print both hit lists. The [RedisVL LangCache guide](https://docs.redisvl.com/en/latest/user_guide/13_langcache_semantic_cache.html) shows this `check`/`store` workflow.

```sh
python exercises/lab_3/03_langcache.py
```

The repeated exact prompt should hit. The related prompt may miss at normalized distance `0.1`; raise the distance threshold slightly to allow looser matches, then restore it. A match should still be checked for relevance. This lab caches only a stable public policy answer, never a personalized order response. Compare with [`03_langcache_completed.py`](03_langcache_completed.py) after your attempt.

## Explain the result

- What does an empty `cache.check()` list mean? Which stored answer appears in a hit?
- What might go wrong if the cached policy changes tomorrow?
- Why would a personalized order answer need a different cache scope or no cache entry?
