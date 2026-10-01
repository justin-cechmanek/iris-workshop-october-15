# Instructor preflight for the 150-minute workshop

Complete this before attendees arrive. The [attendee schedule](README.md#150-minute-plan) includes 20 minutes for account and local setup; email verification and service eligibility are the main timing risks.

1. Confirm each attendee can sign in to [Redis Cloud](https://cloud.redis.io/) and create a Free 30 MB database. One free database is allowed per account. Confirm Redis Search works on the selected database. [Free database guide](https://redis.io/docs/latest/operate/rc/databases/create-database/create-free-database/)
2. Confirm Python 3.11+ through pyenv, package installation, and outbound access to Redis Cloud and `huggingface.co`. Have attendees download `sentence-transformers/all-MiniLM-L6-v2` during setup or before arrival using the [setup command](README.md#setup). It runs locally after the first download; no OpenAI key is needed.
3. Confirm Context Retriever and LangCache service creation is available to attendees. Have one completed Context Retriever surface and one LangCache service ready for demonstration if Cloud setup is slow. Do not seed their exercise data for them.
4. Confirm Agent Memory creation in the target accounts. The [current service guide](https://redis.io/docs/latest/operate/iris/agent-memory/create-service/) offers Quick create on a Free 30 MB database; a custom service can use a 1-minute extraction cadence, while the default is 5 minutes. Have a working instructor service ready if service creation is unavailable or slow. If sharing it, give attendees its endpoint, store ID, and API key through the approved channel. Have each attendee set a unique `WORKSHOP_USER_ID` in `.env`; they should use only fictional preferences.
5. Run the completed examples against a demo account before the onsite session. Keep the starter files untouched. Check that `ctxctl tools list` exposes `get_order_by_id` and that the service extraction cadence permits a long-term memory check near the end of lab 4.

After setting the demo credentials, use this order for the live preflight:

```sh
python exercises/lab_1/01_vector_completed.py
python exercises/lab_2/02_load_context_completed.py
# Create the Context Retriever surface from models_completed.py here.
python exercises/lab_2/02_context_completed.py
python exercises/lab_3/03_langcache_completed.py
python exercises/lab_4/04_memory_completed.py write
python exercises/lab_4/04_memory_completed.py read
```

The [lab 2 guide](exercises/lab_2/README.md) shows the surface creation commands; substitute `models_completed.py` for `models.py`. Repeat only the Memory `read` command after the extraction cadence.

During each lab, ask attendees to predict what Redis will store or return before they run code. After the terminal result, ask them to explain it using the key, index, model, cache entry, or memory event they just created. The questions are in each lab guide.

If Agent Memory extraction is still pending at the end of lab 4, use the session result as the guaranteed checkpoint and revisit long-term search in the debrief. An empty long-term result at first is expected behavior, not a failed lab.

## Debrief answer key

| Question | Source to inspect | What changes it | Staleness to discuss |
| --- | --- | --- | --- |
| Pickup policy | Policy text returned by vector search | Re-embed and reload a revised policy | A vector match can point to old policy text |
| Current order status | Redis order HASH through Context Retriever | Reload or update the order HASH | A copied answer can outlive the live order |
| Repeated public question | LangCache entry | Store a new answer or invalidate the old one | A policy change makes a cached answer stale |
| Fictional store preference | Session event, then extracted long-term memory | New events and later extraction | Long-term recall can lag behind the session |

Ask attendees to name the stored record and update path for each answer. A useful final distinction is that retrieval selects source material, while a cache reuses an earlier response.
