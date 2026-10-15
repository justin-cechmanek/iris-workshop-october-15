"""Completed lab 3: seed background facts, add a conversation, and search memory.

Run: python exercises/lab_3_agent_memory/03_agent_memory_completed.py
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

        # Step 1: After memory reset, call memory.health() and print the response.
        health = memory.health()
        print("Service health:", health)

        # Step 2: Create the list of long-term memories and bulk-load them.
        long_term_memories = []
        for number, text in enumerate(background_facts):
            long_term_memories.append({
            "id": f"{user_id}-background-{number}",
            "text": text,
            "owner_id": user_id,
            "memory_type": "semantic",
            })

        background = memory.bulk_create_long_term_memories(memories=long_term_memories)
        print("Background memories:", background.model_dump_json(by_alias=True, indent=2))

        if background.errors:
            raise RuntimeError("Background memory load failed; see per-record errors above.")

        # Step 3: Add each conversation message as a session event.
        # The first USER event establishes this session's owner.
        roles = {"USER": models.MessageRole.USER, "AGENT": models.MessageRole.ASSISTANT}
        for message in conversation:
            speaker = message["role"]
            text = message["content"]
            event = memory.add_session_event(
            session_id=session_id,
            actor_id=user_id if speaker == "USER" else "cvs-workshop-agent",
            role=roles[speaker],
            content=[models.Text(text=text)],
            created_at=datetime.now(timezone.utc),
            ).event
            print(f"Role: {event.role}, Content: {event.content[0].text}")

        # Step 4: Inspect the final session.
        session = memory.get_session_memory(session_id=session_id)
        session_json = session.model_dump_json()
        print("Session:", session_json)

        # Step 5: Wait for extraction, then search long-term memories.
        # Background facts are written directly; conversation extraction is
        # asynchronous and may not appear right away.
        time.sleep(60) # Allow time for extraction; completion is not guaranteed.
        for label, question in [
            ("Background search", "Which pickup store and notification channel does this user prefer?"),
            ("Conversation search", "When does this user collect orders, and what bag option do they prefer?"),
        ]:
            results = memory.search_long_term_memory(request={
                "text": question,
                "filter_": {"owner_id": {"eq": user_id}},
                "limit": 5,
            })
            print(label + ":")
            for item in results.items:
                print(f"Text: {item.text}, Updated At: {item.updated_at}, Created At: {item.created_at}")


if __name__ == "__main__":
    main()
