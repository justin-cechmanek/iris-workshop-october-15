"""Lab 2: model, load, and retrieve live orders in one file.

First finish Cloud UI setup with at least one saved entity (see README.md).
Use Store, key template workshop:store:{store_id}, and store_id as its PK.
Complete the TODOs from top to bottom. Save REDIS_URL, CTX_ADMIN_KEY,
and the created service's CTX_SURFACE_ID in .env. Python replaces the
initial UI entity model with the complete Store and Order models.
Then run once from the repository root:
    python exercises/lab_2_context_retriever/02_context.py
"""

import asyncio
import json
import os
from pathlib import Path

from context_surfaces import (
    ContextSurfacesClient,
    CreateAgentKeyRequest,
    UnifiedClient,
    UpdateContextSurfaceRequest,
)
from context_surfaces.context_model import ContextField, ContextModel, export_data_model
from dotenv import load_dotenv
from redisvl.redis.connection import RedisConnectionFactory


# Step 1: model the entities, keeping key templates aligned with the loader.
class Store(ContextModel):
    __redis_key_template__ = "workshop:store:{store_id}"

    store_id: str = ContextField(description="Demo store ID", is_key_component=True)
    name: str = ContextField(description="Demo store name", index="text")
    # TODO 1: model city as text and pickup_status as a tag.


class Order(ContextModel):
    __redis_key_template__ = "workshop:order:{order_id}"

    order_id: str = ContextField(description="Demo retail order ID", is_key_component=True)
    # TODO 2: model store_id, status, and customer_id as tags.
    # Include item_summary as text.


# Step 2: load the JSONL records and inspect the stored order HASH.
def load_file(r, file, prefix, id_field):
    count = 0
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        # TODO 3: HSET one HASH per record at f"{prefix}:{record[id_field]}".
        # Use mapping=record. Increment count after a successful write.
        raise NotImplementedError("Write the record to Redis")
    return count


def load_context():
    r = RedisConnectionFactory.get_redis_connection(redis_url=os.environ["REDIS_URL"])
    print("Redis:", r.ping())
    print("Stores:", load_file(r, "data/stores.jsonl", "workshop:store", "store_id"))
    print("Orders:", load_file(r, "data/orders.jsonl", "workshop:order", "order_id"))
    # TODO 4: HGETALL workshop:order:O1001 and print the stored field names and
    # values. This lets you compare the JSONL record with the Redis HASH.


# Step 3: configure the existing surface and create an agent key.
# Finish the initial entity setup in the Cloud UI before running this step.
async def configure_context():
    admin_key = os.environ["CTX_ADMIN_KEY"]
    surface_id = os.environ["CTX_SURFACE_ID"]
    async with ContextSurfacesClient() as client:
        # TODO 5: export_data_model(title="CVS workshop",
        # description="Synthetic retail orders", entities=[Store, Order]).
        # TODO 6: await client.update_context_surface(surface_id,
        # UpdateContextSurfaceRequest(data_model=data_model), admin_key=admin_key).
        # TODO 7: await client.create_agent_key(surface_id,
        # CreateAgentKeyRequest(name="cvs-workshop-agent"), admin_key=admin_key).
        # Return the created agent's .key without printing it.
        raise NotImplementedError("Configure the surface and create an agent key")


# Step 4: inspect the generated tools and retrieve order O1001.
async def query_context(agent_key):
    async with UnifiedClient() as client:
        # TODO 8: list_tools(agent_key) and print every
        # full tool definition. A tool may be a dict or an SDK model (use
        # model_dump(by_alias=True) in that case).
        # TODO 9: choose the generated get-by-ID tool for Order. Copy its
        # exact name and argument schema from the printed list.
        # TODO 10: query_tool(agent_key=..., tool_name=..., arguments=...)
        # for O1001. Print the returned object.
        raise NotImplementedError("List and call a generated tool")


async def main():
    load_dotenv()
    for name in ("REDIS_URL", "CTX_ADMIN_KEY", "CTX_SURFACE_ID"):
        if not os.environ.get(name):
            raise ValueError(f"Set {name} in .env before running lab 2")
    load_context()
    agent_key = await configure_context()
    await query_context(agent_key)


if __name__ == "__main__":
    asyncio.run(main())
