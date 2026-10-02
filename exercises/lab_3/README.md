# Lab 3: LangCache

**Goal:** serve a repeated public policy answer from managed LangCache through RedisVL. Allow about 20 minutes. Read the fictional [`pickup policy`](../../data/policies/pickup.md).

**Pace:** 5 minutes to create the service, 10 to code and compare searches, 5 to explain the result.

## Service setup

In Redis Cloud, open **LangCache** and create a service on the workshop database. **Quick create** can use a Free 30 MB database. Copy the service API key when it appears; Redis displays it only once. On the service **Configuration** page, copy the base URL and cache ID from **Connectivity**. Put them in `.env` as `LANGCACHE_URL`, `LANGCACHE_CACHE_ID`, and `LANGCACHE_API_KEY`. [Create service](https://redis.io/docs/latest/operate/rc/langcache/create-service/) and [find credentials](https://redis.io/docs/latest/operate/rc/langcache/use-langcache/).

**Predict before coding:** Will two questions with different wording always return the same cached answer? At which of `0.02`, `0.10`, and `0.40` is a rephrased question most likely to hit?

## Exercise

Edit [`03_langcache.py`](03_langcache.py):

1. Construct RedisVL's `LangCacheSemanticCache` with the service URL, cache ID, and API key. It wraps the managed LangCache API; it does not create a second Redis index.
2. Call `cache.check(prompt=first, distance_threshold=0.1)` and print the returned list of hit dictionaries. With RedisVL's default normalized distance scale, `0.1` means a minimum LangCache similarity of `0.9`. An empty list is a miss.
3. On a miss, write a short answer supported by the sample pickup policy. Store the pair with `cache.store(prompt=first, response=answer)`.
4. Check the exact prompt again with `distance_threshold=0.02` and print its hit list. This confirms the stored entry is available.
5. Check the **same rephrased prompt** three times with `distance_threshold` values `0.02`, `0.10`, and `0.40`. For each check, print the threshold, `HIT` or `MISS`, and the returned hit list. With RedisVL's normalized distance scale, these correspond to minimum similarities of `0.98`, `0.90`, and `0.60`. Do not store the rephrased prompt between checks; that would create an exact match and hide the threshold effect. The [RedisVL LangCache guide](https://docs.redisvl.com/en/latest/user_guide/13_langcache_semantic_cache.html) shows this `check`/`store` workflow.

```sh
python exercises/lab_3/03_langcache.py
```

The repeated exact prompt should hit. The rephrased prompt may miss at `0.02` and hit at a looser threshold, but the actual result depends on the service's similarity score and any entries already in the cache. If every check has the same result, try another rephrasing and compare again. A loose match may return an irrelevant answer, so read the hit before using it. This lab caches only a stable public policy answer, never a personalized order response. Compare with [`03_langcache_completed.py`](03_langcache_completed.py) after your attempt.

## Explain the result

- What does an empty `cache.check()` list mean? Which stored answer appears in a hit?
- Which threshold first matched the rephrased prompt? What changed between checks?
- What might go wrong if the cached policy changes tomorrow?
- Why would a personalized order answer need a different cache scope or no cache entry?
