"""Completed lab 4: model, load, and retrieve live orders in one file.

First complete Redis Cloud web-console setup using the workshop slides linked
in README.md. Save REDIS_URL, CTX_ADMIN_KEY, and the UI-created service's
CTX_SURFACE_ID in .env. Keep the surface ID set before running Python.
This script loads data, updates that service with Store and Order,
creates an agent key, and retrieves an order.
Then run once from the repository root:
    python exercises/lab_4_context_retriever/04_context_completed.py
"""

import asyncio
import json
import os
from pathlib import Path

from context_surfaces import (
    ContextSurfacesClient,
    CreateAgentKeyRequest,
    CreateContextSurfaceRequest,
    DataSourceConnectionConfig,
    DataSourceRequest,
    UnifiedClient,
    UpdateContextSurfaceRequest,
)
from context_surfaces.context_model import ContextField, ContextModel, export_data_model
from dotenv import load_dotenv, set_key
from redis.connection import parse_url
from redisvl.redis.connection import RedisConnectionFactory


# Step 1: model the entities, keeping key templates aligned with the loader.
class HashContextModel(ContextModel):
    # shortcut: SDK 0.0.6 omits document_type; use native HASH declarations after upgrading.
    @classmethod
    def to_entity_dict(cls):
        return {**super().to_entity_dict(), "document_type": "hash"}


class Store(HashContextModel):
    __redis_key_template__ = "workshop:store:{store_id}"

    # A key component identifies one HASH; text fields support word search,
    # while tag fields support exact filtering.
    store_id: str = ContextField(description="Demo store ID", is_key_component=True)
    name: str = ContextField(description="Demo store name", index="text")
    city: str = ContextField(description="Store city", index="text")
    pickup_status: str = ContextField(description="Whether pickup is open", index="tag")


class Order(HashContextModel):
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
    return count


def load_context():
    data_dir = Path(__file__).resolve().parents[2] / "data"
    redis_client = RedisConnectionFactory.get_redis_connection(redis_url=os.environ["REDIS_URL"])
    print("Redis:", redis_client.ping())
    print("Stores:", load_file(redis_client, data_dir / "stores.jsonl", "workshop:store", "store_id"))
    print("Orders:", load_file(redis_client, data_dir / "orders.jsonl", "workshop:order", "order_id"))
    # Inspect a raw HASH before Context Retriever turns it into a tool result.
    # RedisVL's connection is a redis-py client. With default settings,
    # hgetall() returns bytes for each field and value.
    order_hash = redis_client.hgetall("workshop:order:O1001")
    print("Stored order O1001:", order_hash)


# Step 3: create or update the surface and create an agent key.
async def configure_context():
    admin_key = os.environ["CTX_ADMIN_KEY"]
    surface_id = os.environ.get("CTX_SURFACE_ID", "").strip()
    data_model = export_data_model(
        title="CVS workshop",
        description="Synthetic retail orders",
        entities=[Store, Order],
    )
    async with ContextSurfacesClient() as client:
        if surface_id:
            await client.update_context_surface(
                surface_id,
                UpdateContextSurfaceRequest(data_model=data_model),
                admin_key=admin_key,
            )
        else:
            redis_url = os.environ["REDIS_URL"]
            if not redis_url.startswith(("redis://", "rediss://")):
                raise ValueError("REDIS_URL must use redis:// or rediss:// for Context Retriever")
            connection = parse_url(redis_url)
            if not connection.get("host"):
                raise ValueError("REDIS_URL must include a Redis host")
            host = connection["host"]
            address = f"[{host}]" if ":" in host else host
            data_source = DataSourceRequest(
                connection_config=DataSourceConnectionConfig(
                    addr=f"{address}:{connection.get('port', 6379)}",
                    username=connection.get("username", ""),
                    password=connection.get("password", ""),
                    db=connection.get("db", 0),
                    tls_enabled=redis_url.startswith("rediss://"),
                ),
            )
            surface = await client.create_context_surface(
                CreateContextSurfaceRequest(
                    name="cvs-workshop",
                    description="Synthetic retail orders",
                    data_model=data_model,
                    data_source=data_source,
                ),
                admin_key=admin_key,
            )
            surface_id = surface.id
            # Print before saving so a failed local write does not lose the ID.
            print("Created surface:", surface_id)
            env_path = Path(__file__).resolve().parents[2] / ".env"
            try:
                if not set_key(env_path, "CTX_SURFACE_ID", surface_id)[0]:
                    raise OSError("Could not save CTX_SURFACE_ID")
            except (OSError, UnicodeError) as error:
                raise RuntimeError(
                    f"Service created, but could not save its ID to {env_path}. "
                    f"Set CTX_SURFACE_ID={surface_id} there before rerunning."
                ) from error
            os.environ["CTX_SURFACE_ID"] = surface_id
            print("Saved CTX_SURFACE_ID in:", env_path)
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
        # Summarize the tools; inspect only the schema used by this lab.
        tools = await client.list_tools(agent_key)
        tool_details = [
            tool if isinstance(tool, dict) else tool.model_dump(by_alias=True)
            for tool in tools
        ]
        tools_by_name = {details["name"]: details for details in tool_details}
        print(f"Generated tools ({len(tools_by_name)}):", ", ".join(tools_by_name))

        tool_name = "get_order_by_id"
        if tool_name not in tools_by_name:
            raise RuntimeError(f"{tool_name} was not generated; check the surface model")
        print(json.dumps({
            "name": tool_name,
            "inputSchema": tools_by_name[tool_name]["inputSchema"],
        }, indent=2))

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
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    for name in ("REDIS_URL", "CTX_ADMIN_KEY"):
        if not os.environ.get(name):
            raise ValueError(f"Set {name} in .env before running lab 4")
    load_context()
    agent_key = await configure_context()
    await query_context(agent_key)


if __name__ == "__main__":
    asyncio.run(main())
