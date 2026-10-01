# Lab 2: Context Retriever over live orders

**Goal:** turn structured Redis HASHes into a governed get-by-ID tool. Allow about 45 minutes. Read [`stores.jsonl`](../../data/stores.jsonl) and [`orders.jsonl`](../../data/orders.jsonl) first. Each line is one fictional record.

**Pace:** 10 minutes to load data, 10 to model entities, 20 to create and call the surface, 5 to explain the result.

## How it works

The loader gets a Redis connection through RedisVL and writes current data as raw HASHes. A Context Retriever model describes the entity names, key patterns, and searchable fields. Context Retriever generates tools from that model. An agent key permits calls to those tools, so the caller does not construct raw Redis queries.

**Predict before coding:** If order `O1001` changes from `ready_for_pickup` to `processing` in Redis, should the generated get tool need to be rebuilt? Why?

## Exercise A: load the data

Edit [`02_load_context.py`](02_load_context.py). `RedisConnectionFactory` provides the connection; its client still exposes Redis commands. Complete `load_file()` with one `HSET` per JSON line. The key must be `workshop:store:<store_id>` or `workshop:order:<order_id>`, and `mapping=record` must retain all field names. After loading, call `r.hgetall("workshop:order:O1001")` and print the stored HASH. Run:

```sh
python exercises/lab_2/02_load_context.py
```

Expect `Stores: 2` and `Orders: 3`. Compare the printed HASH fields with the `O1001` JSONL line. The Redis client prints byte strings unless you enable response decoding. Re-running updates these five synthetic keys.

## Exercise B: model the entities

Edit [`models.py`](models.py). Add `ContextField` declarations for every remaining field in both JSONL files. Use `index="text"` for words to search and `index="tag"` for exact values such as status and IDs. Mark each entity's own ID `is_key_component=True`. The model's `__redis_key_template__` must match the loader keys.

## Exercise C: create and call a surface

Follow the [Context Retriever quickstart](https://redis.io/docs/latest/develop/ai/context-engine/context-retriever/quickstart/) for Cloud sign-in and the current CLI. With `.venv` active, `ctxctl` is available:

```sh
ctxctl auth login -u YOUR_CLOUD_EMAIL
ctxctl --output json admin create --name cvs-workshop-admin
export CTX_ADMIN_KEY='PASTE_ADMIN_KEY'
ctxctl --output json surface create --name cvs-workshop --description 'Synthetic retail orders' --models exercises/lab_2/models.py --redis-addr YOUR_REDIS_HOST:PORT --redis-password 'YOUR_REDIS_PASSWORD' --admin-key "$CTX_ADMIN_KEY"
export CTX_SURFACE_ID='PASTE_SURFACE_ID'
ctxctl surface describe "$CTX_SURFACE_ID" --admin-key "$CTX_ADMIN_KEY"
ctxctl --output json agent create --surface-id "$CTX_SURFACE_ID" --name cvs-workshop-agent --admin-key "$CTX_ADMIN_KEY"
export CTX_AGENT_KEY='PASTE_AGENT_KEY'
ctxctl tools list --agent-key "$CTX_AGENT_KEY"
```

Check that `surface describe` names your two entities before creating the agent key. The admin key manages surfaces; the agent key calls generated tools. Copy `CTX_AGENT_KEY` into `.env` for Python. If Redis requires TLS or a non-default user, check `ctxctl surface create --help` for the matching flags. Keep keys out of source control.

Edit [`02_context.py`](02_context.py). Call `UnifiedClient.list_tools(agent_key)` and print names plus `inputSchema`. Find `get_order_by_id`, then call `UnifiedClient.query_tool(agent_key=..., tool_name="get_order_by_id", arguments={"id": "O1001"})`. Print the result. The generated tool schema, not the Redis key pattern, tells you the API argument name.

```sh
python exercises/lab_2/02_context.py
```

Expect a result for `O1001` with status `ready_for_pickup`. To see live context, change that fictional order's `status` in `data/orders.jsonl`, rerun the loader, call the tool again, then restore the sample data.

For the completed path, run [`02_load_context_completed.py`](02_load_context_completed.py), create the surface with `--models exercises/lab_2/models_completed.py`, then run [`02_context_completed.py`](02_context_completed.py). Creating a surface from the unfinished starter model will not expose all completed fields.

## Explain the result

- Which part of the model maps `O1001` to its Redis HASH key?
- Which fields came from the loader, and which parts of the tool response came from the generated surface?
- What is the difference between indexing `item_summary` as text and `status` as a tag?
- Why does the Python caller use an agent key, while surface creation uses an admin key?
