"""Completed lab 2: model, load, and retrieve live orders in one file.

First finish Cloud UI setup with at least one saved entity (see README.md).
Use Store, key template workshop:store:{store_id}, and store_id as its PK.
Save REDIS_URL, CTX_ADMIN_KEY, and the created service's CTX_SURFACE_ID
in .env. This script loads data, replaces the initial UI entity model with
Store and Order, creates an agent key, and retrieves an order.
Then run once from the repository root:
    python exercises/lab_2_context_retriever/02_context_completed.py
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

    # A key component identifies one HASH; text fields support word search,
    # while tag fields support exact filtering.
    store_id: str = ContextField(description="Demo store ID", is_key_component=True)
    name: str = ContextField(description="Demo store name", index="text")
    city: str = ContextField(description="Store city", index="text")
    pickup_status: str = ContextField(description="Whether pickup is open", index="tag")


class Order(ContextModel):
    __redis_key_template__ = "workshop:order:{order_id}"

    order_id: str = ContextField(description="Demo retail order ID", is_key_component=True)
    store_id: str = ContextField(description="Store fulfilling this order", index="tag")
    status: str = ContextField(description="Current order status", index="tag")
    item_summary: str = ContextField(description="Retail items in the order", index="text")
    customer_id: str = ContextField(description="Fictional customer ID", index="tag")


# Step 2: load the JSONL records and inspect the stored order HASH.
def load_file(redis_client, file, prefix, id_field):
    count = 0
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        # Context Retriever reads the field names from each HASH, so use the
        # JSON keys unchanged and the same ID field as the model's template.
        key = f"{prefix}:{record[id_field]}"
        redis_client.hset(key, mapping=record)
        count += 1
        print("Loaded:", key)
    return count


def load_context():
    redis_client = RedisConnectionFactory.get_redis_connection(redis_url=os.environ["REDIS_URL"])
    print("Redis:", redis_client.ping())
    print("Stores:", load_file(redis_client, "data/stores.jsonl", "workshop:store", "store_id"))
    print("Orders:", load_file(redis_client, "data/orders.jsonl", "workshop:order", "order_id"))
    # Inspect a raw HASH before Context Retriever turns it into a tool result.
    # RedisVL's connection is a redis-py client. With default settings,
    # hgetall() returns bytes for each field and value.
    order_hash = redis_client.hgetall("workshop:order:O1001")
    print("Stored order O1001:", order_hash)


# Step 3: configure the existing surface and create an agent key.
# Finish the initial entity setup in the Cloud UI before running this step.
async def configure_context():
    admin_key = os.environ["CTX_ADMIN_KEY"]
    surface_id = os.environ["CTX_SURFACE_ID"]
    data_model = export_data_model(
        title="CVS workshop",
        description="Synthetic retail orders",
        entities=[Store, Order],
    )
    async with ContextSurfacesClient() as client:
        await client.update_context_surface(
            surface_id,
            UpdateContextSurfaceRequest(data_model=data_model),
            admin_key=admin_key,
        )
        print("Configured surface:", surface_id)
        # Each run creates a new agent key, which stays in memory for tool calls.
        agent = await client.create_agent_key(
            surface_id,
            CreateAgentKeyRequest(name="cvs-workshop-agent"),
            admin_key=admin_key,
        )
        return agent.key


# Step 4: inspect the generated tools and retrieve order O1001.
async def query_context(agent_key):
    async with UnifiedClient() as client:
        # Print every complete definition generated from Store and Order,
        # including fields beyond inputSchema.
        tools = await client.list_tools(agent_key)
        tool_details = [
            tool if isinstance(tool, dict) else tool.model_dump(by_alias=True)
            for tool in tools
        ]
        print(f"Generated tools ({len(tool_details)}):")
        for details in tool_details:
            print(json.dumps(details, indent=2))

        tool_name = "get_order_by_id"
        names = {details["name"] for details in tool_details}
        if tool_name not in names:
            raise RuntimeError(f"{tool_name} was not generated; check the surface model")

        # A primary key produces get_<entity>_by_id with an 'id' argument.
        # This call uses the agent key, not the admin key or a raw Redis query.
        result = await client.query_tool(
            agent_key=agent_key, tool_name=tool_name, arguments={"id": "O1001"}
        )
        if result.get("isError"):
            raise RuntimeError(result)
        content = result["content"][0]
        order = json.loads(content["text"])
        print("Order O1001:")
        print(json.dumps(order, indent=2))


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
