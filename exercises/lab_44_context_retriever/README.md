# Lab 2: Context Retriever over live orders

**Goal:** turn structured Redis Hashes into a governed get-by-ID tool. Allow about 45 minutes. Read [`stores.jsonl`](../../data/stores.jsonl) and [`orders.jsonl`](../../data/orders.jsonl) first. Each line is one fictional record.

**Pace:** 10 minutes to model entities, 10 to load data, 20 for Cloud UI setup and Python configuration/tool calls, 5 to explain the result.

## How it works

The loader gets a Redis connection through RedisVL and writes current data as raw hashes. A Context Retriever model describes the entity names, key patterns, and searchable fields. First save at least one entity in the Cloud UI to finish creating the service. The Python script then exports the workshop models and replaces that initial model with the complete Store and Order definitions. Context Retriever generates tools from that model. The script creates an agent key and calls those tools, so the caller does not construct raw Redis queries. The admin key configures the surface; the agent key permits retrieval. No AI model is needed for this lab.

## Exercise

Edit [`02_context.py`](02_context.py), working from top to bottom: model the entities, write the loader, configure the existing surface, then write the tool calls. Complete TODOs 1–10 and the Cloud UI setup below before running Python. Run the file once to load and inspect the data, upload the models, create an agent key, and call the tools.

1. **Model the entities (TODOs 1–2).** In Step 1, add `ContextField` declarations for every remaining field in both JSONL files. Use `index="text"` for words to search and `index="tag"` for exact values such as status and IDs. Mark each entity's own ID `is_key_component=True`.

2. **Load the data (TODOs 3–4).** Continue to Step 2. `RedisConnectionFactory` provides the connection; its client still exposes Redis commands. Complete `load_file()` with one `HSET` per JSON line. The key must be `workshop:store:<store_id>` or `workshop:order:<order_id>`, and `mapping=record` must retain all field names. In `load_context()`, call `r.hgetall("workshop:order:O1001")` and print the stored HASH.

3. **Configure the surface (TODOs 5–7).** In `configure_context()`, call `export_data_model(title="CVS workshop", description="Synthetic retail orders", entities=[Store, Order])`. Use `ContextSurfacesClient.update_context_surface(surface_id, UpdateContextSurfaceRequest(data_model=data_model), admin_key=admin_key)` to upload the model to the existing surface. Then call `create_agent_key(surface_id, CreateAgentKeyRequest(name="cvs-workshop-agent"), admin_key=admin_key)` and return the created agent's `.key`. Await both API calls. Keep the key in memory without printing it.

4. **Inspect and call the tools (TODOs 8–10).** In Step 4, complete `query_context(agent_key)` using the key returned by `configure_context()`. Call `UnifiedClient.list_tools(agent_key)` and print **every complete tool definition** as indented JSON. The list shows what Context Retriever generated from both entities and their indexed fields. Find `get_order_by_id` and inspect its `inputSchema`, then call `UnifiedClient.query_tool(agent_key=..., tool_name="get_order_by_id", arguments={"id": "O1001"})`. Print the result. The generated tool schema, not the Redis key pattern, tells you the API argument name.

## Run and inspect


**One-time Cloud UI setup:** The service must have at least one saved entity before this script can configure it. If your workshop service already has one, confirm its database connection and skip to copying the credentials.

1. Open [Redis Cloud](https://cloud.redis.io/) and select **Context Retriever**. Choose **New service → Create custom service**.
2. Name it `cvs-workshop` and select the same database used by `REDIS_URL`.
3. In **Entities**, select **Add Entity**. Enter entity name `Store`, key template `workshop:store:{store_id}`, and description `Demo workshop store`. Confirm the entity with the checkmark.
4. Continue to **Fields**, choose **Manually enter fields**, and expand `Store`. Add the fields below. Manual entry lets you finish setup before Python loads the sample records.

| Field | Type | PK | Index |
| --- | --- | --- | --- |
| `store_id` | String (`str`) | Checked | None needed |
| `name` | String (`str`) | Unchecked | Text |

5. Select **Create** to finish the service. Open it and confirm `Store` appears under **Overview → Entities**. This initial entity is only for setup; Python uploads the complete workshop model when you run the lab.
6. With your service open, look at the **browser address bar**. Its URL contains the surface ID:

   ```text
   https://cloud.redis.io/#/context-retriever/YOUR_SURFACE_ID
   ```

   Copy the ID immediately after `/context-retriever/` into `CTX_SURFACE_ID` in `.env`. Copy only the ID, excluding the rest of the URL and any trailing path or query parameters. The [Redis workshop's “Save your Surface ID” instructions](https://redis-iris-workshop.vercel.app/retail/context-retriever/#3-save-your-surface-id) document this location.

7. Under **Context Retriever → Admin keys**, use an existing key or select **New admin key**, name it `cvs-workshop-admin`, and generate/copy it into `CTX_ADMIN_KEY`. See the [admin key guide](https://redis.io/docs/latest/operate/iris/context-retriever/view-admin-keys/) if needed.

Save these values in `.env`:

```dotenv
REDIS_URL=rediss://default:PASSWORD@HOST:PORT
CTX_ADMIN_KEY=YOUR_ADMIN_KEY
CTX_SURFACE_ID=YOUR_EXISTING_SURFACE_ID
```

Keep keys out of source control. Use a dedicated workshop surface: the script replaces the initial UI entity model with Store and Order while keeping its existing database connection. After the one-time UI setup, Python handles model configuration and agent-key creation; no command-line setup or `CTX_AGENT_KEY` is needed. After completing all TODOs, run from the repository root with `.venv` active:

```sh
python exercises/lab_2_context_retriever/02_context.py
```

Expect `Stores: 2` and `Orders: 3`, the stored order HASH, the configured surface ID, a full list of generated tools, and a result for `O1001` with status `ready_for_pickup`. Compare the printed HASH fields with the `O1001` JSONL line and the listed get, search, and filter tools with the fields you indexed in Step 1. The Redis client prints byte strings unless you enable response decoding. Each run reloads these five synthetic keys, overwriting any direct Redis changes to their sample fields, and creates another agent key. Remove workshop agent keys in the Cloud console after the session. To see live context, change that fictional order's `status` in `data/orders.jsonl`, rerun the same command, then restore the sample data.

## Troubleshooting

If configuration fails, first confirm you finished the Cloud UI setup and saved at least one entity with a primary-key field. Then check `CTX_SURFACE_ID` and the admin key's access to that surface. If a tool returns no order, confirm the service's database connection matches `REDIS_URL` and its key patterns match the loaded HASHes. If expected tools are missing, check that the exported model includes both entities and that you completed their fields. The script stops on configuration or tool errors.

For the completed path, use the same `.env` with [`02_context_completed.py`](02_context_completed.py) and run it once:

```sh
python exercises/lab_2_context_retriever/02_context_completed.py
```

Running the unfinished starter model will not expose all completed fields.

## Explain the result

- Which part of the model maps `O1001` to its Redis HASH key?
- Which fields came from the loader, and which parts of the tool response came from the generated surface?
- What is the difference between indexing `item_summary` as text and `status` as a tag?
- Why does the Python caller use an agent key, while model configuration uses an admin key?
