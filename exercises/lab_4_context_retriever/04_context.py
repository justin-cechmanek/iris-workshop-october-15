"""Lab 4: model, load, and retrieve live orders in one file.

Complete the TODOs from top to bottom. Save REDIS_URL and CTX_ADMIN_KEY
in .env. In Redis Cloud, open Context Retriever > Admin keys > New admin key,
name it cvs-workshop-admin, and generate/copy the key before closing the dialog.
If Admin keys is unavailable, see README.md for the CLI login/key setup.
Leave CTX_SURFACE_ID blank: Python creates the service, entities, and fields,
then saves the ID in .env. Later runs update that service's model.
Then run once from the repository root:
    python exercises/lab_4_context_retriever/04_context.py
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


# Step 3: create or update the surface and create an agent key.
async def configure_context():
    admin_key = os.environ["CTX_ADMIN_KEY"]
    surface_id = os.environ.get("CTX_SURFACE_ID", "").strip()
    # TODO 5: assign data_model = export_data_model(title="CVS workshop",
    # description="Synthetic retail orders", entities=[Store, Order]).
    raise NotImplementedError("Export the data model")
    async with ContextSurfacesClient() as client:
        if surface_id:
            # TODO 6 (reuse): await client.update_context_surface(surface_id,
            # UpdateContextSurfaceRequest(data_model=data_model), admin_key=admin_key).
            raise NotImplementedError("Update the existing surface")
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
            # TODO 6 (create): assign surface = await client.create_context_surface(
            # CreateContextSurfaceRequest(name="cvs-workshop",
            # description="Synthetic retail orders", data_model=data_model,
            # data_source=data_source), admin_key=admin_key).
            raise NotImplementedError("Create the surface")
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
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    for name in ("REDIS_URL", "CTX_ADMIN_KEY"):
        if not os.environ.get(name):
            raise ValueError(f"Set {name} in .env before running lab 4")
    load_context()
    agent_key = await configure_context()
    await query_context(agent_key)


if __name__ == "__main__":
    asyncio.run(main())
