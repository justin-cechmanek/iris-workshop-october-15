"""Completed lab 2 loader: copy the synthetic JSONL records into Redis HASHes.

Run from the repository root: python exercises/lab_2/02_load_context_completed.py
The HASH key pattern matches models_completed.py exactly.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from redisvl.redis.connection import RedisConnectionFactory


def load_file(r, file, prefix, id_field):
    count = 0
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        # Context Retriever reads the field names from each HASH, so use the
        # JSON keys unchanged and the same ID field as the model's template.
        key = f"{prefix}:{record[id_field]}"
        r.hset(key, mapping=record)
        count += 1
        print("Loaded:", key)
    return count


def main():
    load_dotenv()
    r = RedisConnectionFactory.get_redis_connection(redis_url=os.environ["REDIS_URL"])
    print("Redis:", r.ping())
    print("Stores:", load_file(r, "data/stores.jsonl", "workshop:store", "store_id"))
    print("Orders:", load_file(r, "data/orders.jsonl", "workshop:order", "order_id"))
    # Inspect a raw HASH before Context Retriever turns it into a tool result.
    # RedisVL's connection is a redis-py client. With default settings,
    # hgetall() returns bytes for each field and value.
    order_hash = r.hgetall("workshop:order:O1001")
    print("Stored order O1001:", order_hash)


if __name__ == "__main__":
    main()
