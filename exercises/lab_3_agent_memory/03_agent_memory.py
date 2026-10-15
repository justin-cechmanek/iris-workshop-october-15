"""Lab 3: seed background facts, add a conversation, and search memory.

Run: python exercises/lab_3_agent_memory/03_agent_memory.py
Each run resets this user's demo memories, seeds facts, adds events, and searches.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
import time

from dotenv import load_dotenv
from redis_agent_memory import AgentMemory, errors, models


def main():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

    user_id = os.environ.get("WORKSHOP_USER_ID", "").strip()
    if not user_id or user_id == "change-me":
        raise SystemExit("Set a unique WORKSHOP_USER_ID in .env")
    session_id = f"cvs-workshop-session-{user_id}"

    background_facts = [
        "The user prefers pickup at demo store S101.",
        "The user prefers email notifications for pickup orders.",
    ]

    conversation = [{"role": "USER", "content": "I collect pickup orders after work."},
                    {"role": "AGENT", "content": "I'll remember that you collect orders after work."},
                    {"role": "USER", "content": "Weekday evenings are usually best for me."},
                    {"role": "AGENT", "content": "Noted, you prefer weekday-evening pickup."},
                    {"role": "USER", "content": "I also prefer reusable bags for my orders."},
                    {"role": "AGENT", "content": "I'll remember your reusable-bag preference."}]

    with AgentMemory(
        os.environ["MEMORY_ENDPOINT"],
        store_id=os.environ["MEMORY_STORE_ID"],
        api_key=os.environ["MEMORY_API_KEY"],
    ) as memory:
        # Clear this session and long-term memories between runs.
        try:
            memory.delete_session_memory(session_id=session_id)
        except errors.NotFoundErrorResponseContent:
            pass  # A first run has no session to delete.

        previous = memory.search_long_term_memory(request={
            "filter_": {"owner_id": {"eq": user_id}},
        })

        memory_ids = [record.id for record in previous.items]
        if memory_ids:
            deleted = memory.bulk_delete_long_term_memories(memory_ids=memory_ids)
            if deleted.errors:
                raise RuntimeError(f"Memory reset failed: {deleted.errors}")
        # shortcut: reset assumes at most 10 memories per owner; add pagination for larger datasets.
        # shortcut: pending extraction may race cleanup; isolate runs if strict resets are needed.

        # TODO 1: After the memory reset above, call memory.health() and print
        # the response before writing new memories or interpreting an empty search.

        # TODO 2: bulk_create_long_term_memories for background_facts.
        # Enumerate facts; use f"{user_id}-background-{number}"
        # as each id, owner_id=user_id, and memory_type="semantic".
        # Print the response and raise RuntimeError if response.errors.
        # see https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/api-reference/#tag/Long-Term-Memory/operation/BulkCreateLongTermMemories
        raise NotImplementedError("Bulk-load background memories")

        # TODO 3: Add every message in conversation as a session event.
        # Read message["role"] and message["content"]; map USER to role USER
        # and AGENT to ASSISTANT. Use actor_id=user_id for USER and
        # "cvs-workshop-agent" for AGENT, the same session_id, and UTC
        # created_at. The first event must be USER. Read the response's .event
        # and print its role and content[0].text.
        # See https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/python-sdk-quickstart/#1-build-conversation-context-with-session-memory
        raise NotImplementedError("Add individual conversation turns")

        # TODO 4: get_session_memory(session_id); print model_dump_json().
        # See the session retrieval example in the quickstart section above.

        # TODO 5: Import time and call time.sleep(60) before searching to allow
        # background extraction to run; completion may take longer.
        # Run separate long-term searches for store/notification
        # preferences and conversation pickup-time/bag preferences. Use
        # filter_ owner_id eq user_id and limit 5. Label each search and print
        # each item's text, updated_at, and created_at; empty results show only the label.
        # Background facts are direct writes; conversation extraction is
        # asynchronous, so extracted facts may not appear on the first run.
        # See https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/python-sdk-quickstart/#2-recall-automatically-extracted-information
        raise NotImplementedError("Read session and long-term memory")


if __name__ == "__main__":
    main()
