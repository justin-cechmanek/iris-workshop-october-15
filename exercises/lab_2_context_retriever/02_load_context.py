"""Lab 2: load synthetic order/store HASH data for Context Retriever.

Run from repository root: python exercises/lab_2/02_load_context.py
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
        # TODO: HSET one HASH per record at f"{prefix}:{record[id_field]}".
        # Use mapping=record. Increment count after a successful write.
        raise NotImplementedError("Write the record to Redis")
    return count


def main():
    load_dotenv()
    r = RedisConnectionFactory.get_redis_connection(redis_url=os.environ["REDIS_URL"])
    print("Redis:", r.ping())
    print("Stores:", load_file(r, "data/stores.jsonl", "workshop:store", "store_id"))
    print("Orders:", load_file(r, "data/orders.jsonl", "workshop:order", "order_id"))
    # TODO: HGETALL workshop:order:O1001 and print the stored field names and
    # values. This lets you compare the JSONL record with the Redis HASH.


if __name__ == "__main__":
    main()
