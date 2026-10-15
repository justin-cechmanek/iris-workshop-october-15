# Lab 4: Context Retriever over live orders

**Goal:** turn structured Redis Hashes into a governed get-by-ID tool. Allow about 45 minutes. Read [`stores.jsonl`](../../data/stores.jsonl) and [`orders.jsonl`](../../data/orders.jsonl) first. Each line is one fictional record.

**Pace:** 10 minutes to model entities, 10 to load data, 20 for admin-key setup and Python configuration/tool calls, 5 to explain the result.

## How it works

The loader gets a Redis connection through RedisVL and writes current data as raw hashes. A Context Retriever model describes the entity names, key patterns, and searchable fields. Python exports the Store and Order models and creates a service connected to the database in `REDIS_URL`. It saves the returned `CTX_SURFACE_ID` in the repository's `.env` so later runs update the same service. Context Retriever generates tools from that model. The script creates an agent key and calls those tools, so the caller does not construct raw Redis queries. The admin key creates and configures the surface; the agent key permits retrieval. No AI model is needed for this lab.

Both entities inherit the provided `HashContextModel`, which exports `document_type="hash"`. The installed Python SDK otherwise omits this setting, and Context Retriever defaults to JSON documents. The declaration must match the loader's `HSET` writes.

## Exercise

Edit [`04_context.py`](04_context.py), working from top to bottom: model the entities, write the loader, create or update the surface, then write the tool calls. Complete TODOs 1–10 and the admin-key setup below before running Python. Run the file once to load and inspect the data, create the service with its models, create an agent key, and call the tools. Service, entity, and field creation all happen in Python.

1. **Model the entities (TODOs 1–2).** In Step 1, add `ContextField` declarations for every remaining field in both JSONL files. Use `index="text"` for words to search and `index="tag"` for exact values such as status and IDs. Mark each entity's own ID `is_key_component=True`.

2. **Load the data (TODOs 3–4).** Continue to Step 2. `RedisConnectionFactory` provides the connection; its client still exposes Redis commands. Complete `load_file()` with one `HSET` per JSON line. The key must be `workshop:store:<store_id>` or `workshop:order:<order_id>`, and `mapping=record` must retain all field names. In `load_context()`, call `r.hgetall("workshop:order:O1001")` and print the stored HASH.

3. **Configure the surface (TODOs 5–7).** Replace each `NotImplementedError` in Step 3 with the code described in its TODO:

   - **TODO 5:** assign `data_model = export_data_model(title="CVS workshop", description="Synthetic retail orders", entities=[Store, Order])`.
   - **TODO 6:** complete both branches. If `surface_id` is set, await `client.update_context_surface(surface_id, UpdateContextSurfaceRequest(data_model=data_model), admin_key=admin_key)`. Otherwise, assign `surface = await client.create_context_surface(CreateContextSurfaceRequest(name="cvs-workshop", description="Synthetic retail orders", data_model=data_model, data_source=data_source), admin_key=admin_key)`. The supplied code builds `data_source` from `REDIS_URL`, then saves `surface.id` to `.env` and the current process environment. Keep that saving code after your create call.
   - **TODO 7:** assign `agent = await client.create_agent_key(surface_id, CreateAgentKeyRequest(name="cvs-workshop-agent"), admin_key=admin_key)` and `return agent.key`. Keep the key in memory without printing it.

4. **Inspect and call the tools (TODOs 8–10).** In Step 4, complete `query_context(agent_key)` using the key returned by `configure_context()`. Call `UnifiedClient.list_tools(agent_key)` and print the tool count and names on one line. Find `get_order_by_id` and print only its name and `inputSchema` as indented JSON, then call `UnifiedClient.query_tool(agent_key=..., tool_name="get_order_by_id", arguments={"id": "O1001"})`. Print the result. The generated tool schema, not the Redis key pattern, tells you the API argument name.

## Run and inspect

**One-time admin-key setup:** Have your workshop Redis Cloud database and `REDIS_URL` ready. The script creates the Context Retriever service; you only need an admin key for your account beforehand.

1. Open [Redis Cloud](https://cloud.redis.io/) and select **Context Retriever** from the left-hand menu.
2. If **Admin keys** is available, open that tab and select **New admin key**. Name it `cvs-workshop-admin`, select **Generate key**, and copy the value into `CTX_ADMIN_KEY` in `.env` before closing the dialog. You can also use an existing key if you have its full value. See the [admin key guide](https://redis.io/docs/latest/operate/iris/context-retriever/view-admin-keys/).
3. On a new account, you may see the introduction page instead. Use the CLI installed with the Python package to sign in and create the key, following the [Redis quickstart](https://redis.io/docs/latest/develop/ai/context-engine/context-retriever/quickstart/). With `.venv` active, run the commands below, entering your Redis Cloud password when prompted. Copy the returned `key` value into `CTX_ADMIN_KEY` in `.env`.

   ```sh
   ctxctl auth login -u YOUR_REDIS_CLOUD_EMAIL
   ctxctl --output json admin create --name cvs-workshop-admin
   ```

4. Leave `CTX_SURFACE_ID` blank for the first run. Complete the Python TODOs; service creation includes both entities and all modeled fields, including `store_id` and `name`.

Save these values in `.env`:

```dotenv
REDIS_URL=rediss://default:PASSWORD@HOST:PORT
CTX_ADMIN_KEY=YOUR_ADMIN_KEY
CTX_SURFACE_ID=
```

Use `redis://` for a non-TLS database or `rediss://` for TLS, and URL-encode reserved characters in credentials. Keep keys out of source control. Python creates `cvs-workshop` and automatically writes its ID into `CTX_SURFACE_ID` in `.env`, preserving other settings and comments. Keep that saved ID for repeat runs. An existing ID updates that service's model while retaining its database connection; use only a dedicated workshop surface. No `CTX_AGENT_KEY` is needed. After completing all TODOs, run from the repository root with `.venv` active:

```sh
python exercises/lab_4_context_retriever/04_context.py
```

The scripts resolve `.env` and data files relative to their own location. From `exercises/`, you can also run `python lab_4_context_retriever/04_context.py` (or `04_context_completed.py` for the completed version).

Expect `Stores: 2` and `Orders: 3`, the stored order HASH, the configured surface ID, a one-line list of generated tool names, the input schema for `get_order_by_id`, and a result for `O1001` with status `ready_for_pickup`. On the first run, also expect `Created surface:` and confirmation that `CTX_SURFACE_ID` was saved. Open **Context Retriever → cvs-workshop → Overview → Entities** in Redis Cloud to inspect Store, Order, and their fields. Compare the printed HASH fields with the `O1001` JSONL line and the listed get, search, and filter tools with the fields you indexed in Step 1. The Redis client prints byte strings unless you enable response decoding. Each run reloads these five synthetic keys, overwriting any direct Redis changes to their sample fields, and creates another agent key. Remove workshop agent keys in the Cloud console after the session. To see live context, change that fictional order's `status` in `data/orders.jsonl`, rerun the same command, then restore the sample data.

## Troubleshooting

If creation fails, check the admin key and account's access to Context Retriever, along with the Redis host, credentials, and TLS scheme in `REDIS_URL`. If updating fails, check the saved `CTX_SURFACE_ID` and the admin key's access to that service; the script will not create a replacement automatically. If creation succeeds but saving `.env` fails, copy the printed ID into `CTX_SURFACE_ID` before rerunning to avoid another service. Keep `.env` writable. If a tool returns no order, confirm the service's database connection matches `REDIS_URL` and its key patterns match the loaded HASHes. Changing `REDIS_URL` does not reconnect an existing service. If retrieval reports `Existing key has wrong Redis type`, keep the sample keys as HASHes and confirm both exported entities declare `document_type="hash"`. Rerun the corrected script to update the existing surface; do not delete the sample data. If the server rejects HASH entities, its deployed version needs HASH support. If expected tools are missing, check that the exported model includes both entities and that you completed their fields. The script stops on configuration or tool errors.

For the completed path, use the same `.env` with [`04_context_completed.py`](04_context_completed.py) and run it once:

```sh
python exercises/lab_4_context_retriever/04_context_completed.py
```

Running the unfinished starter model will not expose all completed fields.

## Explain the result

- Which part of the model maps `O1001` to its Redis HASH key?
- Which fields came from the loader, and which parts of the tool response came from the generated surface?
- What is the difference between indexing `item_summary` as text and `status` as a tag?
- Why does the Python caller use an agent key, while model configuration uses an admin key?
