# Lab 3: Agent Memory

**Goal:** bulk-load background memories, add conversation exchanges, and compare immediate session memory with later long-term recall. Allow about 25 minutes.

**Pace:** 5 minutes to confirm service access, 15 to code and inspect session memory, 5 to compare the two memory types.

## Service setup

In Redis Cloud, open **Agent Memory** and accept the preview terms if shown. Choose **Create custom** and set a **1-minute extraction cadence** under **Memory configuration** for this lab. Follow the [service guide](https://redis.io/docs/latest/operate/iris/agent-memory/create-service/) for the remaining setup. Copy the API key immediately; it is shown only once. From the service **Configuration** tab, copy the endpoint (including `https://`) and store ID. Put them in `.env` as `MEMORY_ENDPOINT`, `MEMORY_STORE_ID`, and `MEMORY_API_KEY`. [Agent Memory Python quickstart](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/python-sdk-quickstart/).

Set `WORKSHOP_USER_ID` in `.env` to a unique non-sensitive ID such as `attendee-1` before running the code. Use an ID dedicated to this lab: each run deletes its demo session and all long-term memories matching that owner ID before adding new data. The script derives a stable session ID and background-memory IDs from it, so keep it unchanged between runs.

## How it works

The provided reset block deletes this user's demo session, searches long-term memories for `owner_id=user_id` once, and deletes their IDs in one bulk call. This lab assumes at most 10 long-term memories per attendee, within the search's default result limit. A missing session is normal on the first run. Reset errors, including per-record deletion errors, stop new writes.

Bulk creation then writes background facts directly into long-term memory. Session events record a conversation immediately; the service extracts durable facts from those events asynchronously. The supplied `conversation` is a list of dictionaries with `role` and `content` fields. The roles are `USER` and `AGENT`. Redis's SDK calls the agent role `ASSISTANT`.

## Exercise

Edit [`03_agent_memory.py`](03_agent_memory.py):

1. After the provided memory reset block, call `memory.health()` and print its response. A healthy service gives you a useful baseline before writing new memories and interpreting the later results.
2. Call `bulk_create_long_term_memories(memories=...)` once for both `background_facts`: pickup at S101 and email notifications. Enumerate the facts and give each record `id=f"{user_id}-background-{number}"`, `text=text`, `owner_id=user_id`, and `memory_type="semantic"`. Print the response, including its `created` IDs and any `errors`; raise `RuntimeError` if errors are reported. Stable IDs avoid creating new seed records on each run.
3. Loop over all six messages in `conversation`, adding one message at a time with `add_session_event()`. Read `speaker = message["role"]` and `text = message["content"]` from each dictionary. Use `actor_id=user_id` and `models.MessageRole.USER` for the user, and `actor_id="cvs-workshop-agent"` and `models.MessageRole.ASSISTANT` for the agent. Pass the same `session_id`, `content=[models.Text(text=text)]`, and `created_at=datetime.now(timezone.utc)`. The first event must be the USER message. Read `.event` from each response and print its `role` and `content[0].text` as `Role: ..., Content: ...`.
4. Call `get_session_memory(session_id=session_id)` once after the loop and print `model_dump_json()` with the label `Session:`. On a fresh session, verify that all six messages appear in order with alternating USER and ASSISTANT roles.
5. Call `time.sleep(60)` after inspecting the session and before searching, to allow background extraction to run. Extraction may take longer than 60 seconds. Run separate `search_long_term_memory()` calls for the store/notification background facts and the pickup-time/bag preferences in the conversation. Set `filter_` to `{"owner_id": {"eq": user_id}}` and `limit=5` in each request. Print headings `Background search:` and `Conversation search:`, then each item's `text`, `updated_at`, and `created_at` as `Text: ..., Updated At: ..., Created At: ...`. An empty search prints only its heading. Semantic searches can return overlapping results; inspect the text rather than expecting an exact match.

## Run and inspect

Run the script once to reset this user's demo memories, load background facts, add the conversation, inspect the session, and search long-term memory:

```sh
python exercises/lab_3_agent_memory/03_agent_memory.py
```

Every run resets the stored demo data and performs the full flow, producing six new session events. Background facts are written directly without waiting for conversation extraction; search visibility can still depend on indexing. The completed script pauses for 60 seconds before searching to allow time for extraction with the custom service’s 1-minute cadence; this does not guarantee extraction has finished. Facts extracted from the conversation may be absent at first or phrased differently. To observe later extraction, wait for the service cadence and inspect the memories in Redis Cloud before rerunning: another run clears the previous results. Background jobs already queued may race cleanup, so this reset is not a guarantee that prior extraction has finished. The owner filter scopes both searches to your fictional ID. Compare with [`03_agent_memory_completed.py`](03_agent_memory_completed.py) after your attempt.

## Explain the result

- How do directly loaded facts differ from facts extracted from a conversation?
- Why must the reset delete long-term memories separately from the session?
- If conversation-derived facts are missing from search, which output proves that the session writes still succeeded?
