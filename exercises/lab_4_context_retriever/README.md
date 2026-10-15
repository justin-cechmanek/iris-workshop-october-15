# Lab 4: Context Retriever over live orders

**Goal:** turn structured Redis Hashes into a governed get-by-ID tool. Allow about 45 minutes. Read [`stores.jsonl`](../../data/stores.jsonl) and [`orders.jsonl`](../../data/orders.jsonl) first. Each line is one fictional record.

**Pace:** 10 minutes to model entities, 10 to load data, 20 for web-console setup and Python configuration/tool calls, 5 to explain the result.

## How it works

The loader gets a Redis connection through RedisVL and writes current data as raw hashes. A Context Retriever model describes the entity names, key patterns, and searchable fields. First create the service in the Redis Cloud web console using the workshop slides below. Python then exports the complete Store and Order models and updates that existing service. Context Retriever generates tools from that model. The script creates an agent key and calls those tools, so the caller does not construct raw Redis queries. The admin key configures the surface; the agent key permits retrieval. No AI model is needed for this lab.

Both entities inherit the provided `HashContextModel`, which exports `document_type="hash"`. The installed Python SDK otherwise omits this setting, and Context Retriever defaults to JSON documents. The declaration must match the loader's `HSET` writes.

## Exercise

Edit [`04_context.py`](04_context.py), working from top to bottom: model the entities, write the loader, configure the existing surface, then write the tool calls. Complete TODOs 1–10 and the web-console setup below before running Python. Run the file once to load and inspect the data, upload the complete models, create an agent key, and call the tools.

1. **Model the entities (TODOs 1–2).** In Step 1, add `ContextField` declarations for every remaining field in both JSONL files. Use `index="text"` for words to search and `index="tag"` for exact values such as status and IDs. Mark each entity's own ID `is_key_component=True`.

2. **Load the data (TODOs 3–4).** Continue to Step 2. `RedisConnectionFactory` provides the connection; its client still exposes Redis commands. Complete `load_file()` with one `HSET` per JSON line. The key must be `workshop:store:<store_id>` or `workshop:order:<order_id>`, and `mapping=record` must retain all field names. In `load_context()`, call `r.hgetall("workshop:order:O1001")` and print the stored HASH.

3. **Configure the existing surface (TODOs 5–7).** Complete the export, existing-surface update, and agent-key TODOs in Step 3:

   - **TODO 5:** assign `data_model = export_data_model(title="CVS workshop", description="Synthetic retail orders", entities=[Store, Order])`.
   - **TODO 6:** with `CTX_SURFACE_ID` saved from web-console setup, complete the existing-surface branch: await `client.update_context_surface(surface_id, UpdateContextSurfaceRequest(data_model=data_model), admin_key=admin_key)`. This replaces the initial UI model with the complete Store and Order definitions while keeping the service's database connection.
   - **TODO 7:** assign `agent = await client.create_agent_key(surface_id, CreateAgentKeyRequest(name="cvs-workshop-agent"), admin_key=admin_key)` and `return agent.key`. Keep the key in memory without printing it.

4. **Inspect and call the tools (TODOs 8–10).** In Step 4, complete `query_context(agent_key)` using the key returned by `configure_context()`. Call `UnifiedClient.list_tools(agent_key)` and print the tool count and names on one line. Find `get_order_by_id` and print only its name and `inputSchema` as indented JSON, then call `UnifiedClient.query_tool(agent_key=..., tool_name="get_order_by_id", arguments={"id": "O1001"})`. Print the result. The generated tool schema, not the Redis key pattern, tells you the API argument name.

## Run and inspect

**One-time web-console setup:** Follow the [Context Retriever setup slides](https://docs.google.com/presentation/d/1OiXwfg0rwSgQvvXwfb8VFgopNP5IFisC/edit?slide=id.h5dd1f520f493c003_0_2451#slide=id.h5dd1f520f493c003_0_2451). Create `cvs-workshop` on the same database used by `REDIS_URL`, add the initial Store entity and fields, and finish creating the service. Use lowercase `store_id` to match the key template `workshop:store:{store_id}`.

Copy the created service's ID from the browser URL into `CTX_SURFACE_ID`. After creating the service, use **Context Retriever → Admin Keys → New Admin Key** to generate `cvs-workshop-admin` and copy its value into `CTX_ADMIN_KEY` before closing the dialog. The slides guide these web-console steps.

Save all three values in the repository's `.env` before running Python:

```dotenv
REDIS_URL=redis://default:PASSWORD@HOST:PORT
CTX_ADMIN_KEY=YOUR_ADMIN_KEY
CTX_SURFACE_ID=YOUR_CREATED_SERVICE_ID
```

The workshop's free 30 MB database uses `redis://`. URL-encode reserved characters in credentials and keep keys out of source control. Keep `CTX_SURFACE_ID` set to the UI-created service's ID on every run. Python uploads the full workshop model to that service while retaining its database connection; use only a dedicated workshop surface. Python creates its agent key in memory, so no `CTX_AGENT_KEY` is needed. After completing all TODOs, run from the repository root with `.venv` active:

```sh
python exercises/lab_4_context_retriever/04_context.py
```

The scripts resolve `.env` and data files relative to their own location. From `exercises/`, you can also run `python lab_4_context_retriever/04_context.py` (or `04_context_completed.py` for the completed version).

Expect `Stores: 2` and `Orders: 3`, the stored order HASH, the configured surface ID, a one-line list of generated tool names, the input schema for `get_order_by_id`, and a result for `O1001` with status `ready_for_pickup`. Compare the printed HASH fields with the `O1001` JSONL line and the listed get, search, and filter tools with the fields you indexed in Step 1. The Redis client prints byte strings unless you enable response decoding. Each run reloads these five synthetic keys, overwriting any direct Redis changes to their sample fields, and creates another agent key. Remove workshop agent keys in the Cloud console after the session. To see live context, change that fictional order's `status` in `data/orders.jsonl`, rerun the same command, then restore the sample data.

## Troubleshooting

If configuration fails, confirm you finished service creation in the web console and saved both `CTX_SURFACE_ID` and `CTX_ADMIN_KEY` in `.env`. Copy only the ID after `/context-retriever/` in the service URL, excluding any trailing path or query parameters. Check the admin key's access to that service. If a tool returns no order, confirm the service's database connection matches `REDIS_URL` and its key patterns match the loaded HASHes. Changing `REDIS_URL` does not reconnect an existing service. If retrieval reports `Existing key has wrong Redis type`, keep the sample keys as HASHes and confirm both exported entities declare `document_type="hash"`. Rerun the corrected script to update the existing surface; do not delete the sample data. If the server rejects HASH entities, its deployed version needs HASH support. If expected tools are missing, check that the exported model includes both entities and that you completed their fields. The script stops on configuration or tool errors.

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
