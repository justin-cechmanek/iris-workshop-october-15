# Lab 4: Agent Memory

**Goal:** observe immediate session memory and later long-term recall. Allow about 25 minutes. This lab uses only a fictional pickup preference.

**Pace:** 5 minutes to confirm service access, 15 to code and inspect session memory, 5 to compare the two memory types.

## Service setup

In Redis Cloud, open **Agent Memory** and accept the preview terms if shown. The [service guide](https://redis.io/docs/latest/operate/iris/agent-memory/create-service/) offers **Quick create** on a Free 30 MB database. If you choose **Create custom**, set a **1-minute extraction cadence** to observe long-term recall sooner; Quick create uses the default 5-minute cadence. Copy the API key immediately; it is shown only once. From the service **Configuration** tab, copy the endpoint (including `https://`) and store ID. Put them in `.env` as `MEMORY_ENDPOINT`, `MEMORY_STORE_ID`, and `MEMORY_API_KEY`. [Agent Memory Python quickstart](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/python-sdk-quickstart/).

If your account cannot create the service, use the instructor-provided workshop service. The session event is the lab's checkpoint; long-term extraction can still be pending at the end.

Set `WORKSHOP_USER_ID` in `.env` to a unique non-sensitive ID before running the code. The script derives a stable session ID from it, so `write` and `read` use the same session. This matters when the instructor shares one Memory service across attendees. The owner filter is a query filter, not an access-control boundary for everyone sharing one service key.

**Predict before coding:** Which call should return the new message immediately? Which result could remain empty for a while?

## Exercise

Edit [`04_memory.py`](04_memory.py):

1. Call `memory.health()` and print its response. A healthy service gives you a useful baseline before interpreting the later results.
2. In `write` mode, call `add_session_event()` with `session_id=session_id`, `actor_id=user_id`, `role=models.MessageRole.USER`, `content=[models.Text(text="I prefer pickup at demo store S101.")]`, and `created_at=datetime.now(timezone.utc)`.
3. Call `get_session_memory(session_id=session_id)` and print `model_dump_json(by_alias=True, indent=2)`.
4. Search long-term memory with a question about pickup preference and `filter_` set to `{"owner_id": {"eq": user_id}}`. Use `limit=5` in the request and print the response.

```sh
python exercises/lab_4/04_memory.py write
python exercises/lab_4/04_memory.py read
```

Run `write` once; repeat `read` after the service extraction cadence. The session event should appear immediately. Long-term memory is extracted asynchronously and can initially be empty or phrased differently. The owner filter scopes this query to your fictional ID. Use no real customer or health information. Compare with [`04_memory_completed.py`](04_memory_completed.py) after your attempt.

## Explain the result

- How does session memory differ from long-term memory in timing and purpose?
- Why does a second `write` run produce another event?
- If long-term search is empty, which output proves that the write still succeeded?
- How would a service connection failure differ from a healthy service with no extracted memory yet?
