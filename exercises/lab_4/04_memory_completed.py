"""Completed lab 4: add a fictional session event and search memory.

Run 'python exercises/lab_4/04_memory_completed.py write' once, then use 'read'.
Long-term extraction is asynchronous and may need another read later.
"""

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from redis_agent_memory import AgentMemory, models


def main():
    load_dotenv()
    # A shared instructor service needs separate owner and session IDs for
    # each attendee. Keep the chosen ID stable between write and read runs.
    user_id = os.environ.get("WORKSHOP_USER_ID", "").strip()
    if not user_id or user_id == "change-me":
        raise SystemExit("Set a unique WORKSHOP_USER_ID in .env")
    session_id = f"cvs-workshop-session-{user_id}"

    mode = sys.argv[1] if len(sys.argv) > 1 else "read"
    if mode not in {"write", "read"}:
        raise SystemExit("Use 'write' or 'read'")

    with AgentMemory(
        os.environ["MEMORY_ENDPOINT"],
        store_id=os.environ["MEMORY_STORE_ID"],
        api_key=os.environ["MEMORY_API_KEY"],
    ) as memory:
        # Separate connection health from the later session and search calls.
        health = memory.health()
        health_json = health.model_dump_json(by_alias=True, indent=2)
        print("Service health:", health_json)

        if mode == "write":
            # Session memory records the turn immediately. Write mode is
            # separate so re-running read does not create duplicate events.
            event = memory.add_session_event(
                session_id=session_id,
                actor_id=user_id,
                role=models.MessageRole.USER,
                content=[models.Text(text="I prefer pickup at demo store S101.")],
                created_at=datetime.now(timezone.utc),
            )
            event_json = event.model_dump_json(by_alias=True, indent=2)
            print("Created event:", event_json)

        session = memory.get_session_memory(session_id=session_id)
        session_json = session.model_dump_json(by_alias=True, indent=2)
        print("Session:", session_json)

        # Scope this query to the attendee's fictional ID. The shared API key
        # still grants access to the service; this is not an access boundary.
        # The service may need time to extract long-term memory.
        results = memory.search_long_term_memory(request={
            "text": "Which pickup store does this user prefer?",
            "filter_": {"owner_id": {"eq": user_id}},
            "limit": 5,
        })
        results_json = results.model_dump_json(by_alias=True, indent=2)
        print("Long-term search:", results_json)


if __name__ == "__main__":
    main()
