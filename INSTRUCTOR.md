# Instructor preflight for the 150-minute workshop

Complete this before attendees arrive. The [attendee schedule](README.md#150-minute-plan) includes 20 minutes for account and local setup; email verification and service eligibility are the main timing risks.

1. Confirm each attendee can sign in to [Redis Cloud](https://cloud.redis.io/) and create a Free 30 MB database. One free database is allowed per account. Confirm Redis Search works on the selected database. [Free database guide](https://redis.io/docs/latest/operate/rc/databases/create-database/create-free-database/)
2. Confirm Python 3.11+ through pyenv, package installation, and outbound access to Redis Cloud and `huggingface.co`. Have attendees download `sentence-transformers/all-MiniLM-L6-v2` during setup or before arrival using the [setup command](README.md#setup). It runs locally after the first download; no OpenAI key is needed.
3. Confirm attendees can obtain a Context Retriever admin key and create a service with it. The lab 4 guide covers the Admin keys tab and CLI login/key-generation fallback for new accounts. With `CTX_ADMIN_KEY` and `REDIS_URL` set and `CTX_SURFACE_ID` blank, Python creates the service with the complete Store and Order models, saves its ID in `.env`, and creates an agent key. Later runs update the saved service's model; use dedicated workshop surfaces. Have one completed Context Retriever surface and one LangCache service ready for demonstration if Cloud setup is slow. Confirm LangCache service creation is available. Do not seed their exercise data for them.
4. Confirm Agent Memory creation in the target accounts. For lab 3, use **Create custom** and set a **1-minute extraction cadence** under **Memory configuration**, following the [current service guide](https://redis.io/docs/latest/operate/iris/agent-memory/create-service/). The completed script pauses for 60 seconds before searching, which allows time for extraction but does not guarantee completion. Have a working instructor service ready if service creation is unavailable or slow. If sharing it, give attendees its endpoint, store ID, and API key through the approved channel. Have each attendee set a unique `WORKSHOP_USER_ID` in `.env`; they should use only fictional preferences.
5. Run the completed examples against a demo account before the onsite session. Keep the starter files untouched. Check that lab 4's printed tool list exposes `get_order_by_id` and that the service extraction cadence permits a long-term memory check near the end of lab 3. Each lab 4 run creates another agent key; remove workshop keys in the Cloud console after the session.

After setting the demo credentials, use this order for the live preflight:

```sh
python exercises/lab_1_vector_search/01_vector_completed.py
python exercises/lab_2_langcache/02_langcache_completed.py
python exercises/lab_3_agent_memory/03_agent_memory_completed.py
# Set CTX_ADMIN_KEY in .env; leave CTX_SURFACE_ID blank on the first run.
# Python creates the service and saves its ID for later runs.
python exercises/lab_4_context_retriever/04_context_completed.py
```

The [lab 4 guide](exercises/lab_4_context_retriever/README.md) explains admin-key setup and inspecting the generated service in Redis Cloud. The completed Python script loads the sample records, creates or updates the surface, saves a newly created surface ID in `.env`, creates an agent key, and calls the generated tool. Lab 3 runs its full flow without arguments and resets the attendee's demo session and owner-scoped long-term memories first. Use dedicated workshop user IDs. The conversation loop writes six separate events with alternating USER and ASSISTANT roles; read the session once afterward and use it to verify all six messages before discussing extraction. Inspect later extraction in Redis Cloud before rerunning, because another run clears the prior results.

During each lab, ask attendees to predict what Redis will store or return before they run code. After the terminal result, ask them to explain it using the key, index, model, cache entry, or memory event they just created. The questions are in each lab guide.

If Agent Memory extraction is still pending at the end of lab 3, use the session result as the guaranteed checkpoint and revisit long-term search in the debrief. An empty long-term result at first is expected behavior, not a failed lab.

## Debrief answer key

| Question | Source to inspect | What changes it | Staleness to discuss |
| --- | --- | --- | --- |
| Pickup policy | Policy text returned by vector search | Re-embed and reload a revised policy | A vector match can point to old policy text |
| Current order status | Redis order HASH through Context Retriever | Reload or update the order HASH | A copied answer can outlive the live order |
| Repeated public question | LangCache entry | Store a new answer or invalidate the old one | A policy change makes a cached answer stale |
| Fictional store preference | Session event, then extracted long-term memory | New events and later extraction | Long-term recall can lag behind the session |

Ask attendees to name the stored record and update path for each answer. A useful final distinction is that retrieval selects source material, while a cache reuses an earlier response.
