"""Lab 4: write a fictional preference, then read session and long-term memory.

Run: python exercises/lab_4/04_memory.py write
Then: python exercises/lab_4/04_memory.py read
"""

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from redis_agent_memory import AgentMemory, models


def main():
    load_dotenv()
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
        # TODO 0: Call memory.health() and print the response. Check service
        # reachability before you write an event or interpret an empty search.
        if mode == "write":
            # TODO 1: add_session_event for user_id with role USER, the
            # current UTC time, and models.Text containing a fictional,
            # non-sensitive preference such as "I prefer pickup at S101."
            raise NotImplementedError("Write a session event")

        # TODO 2: get_session_memory(session_id); print model_dump_json().
        # TODO 3: search_long_term_memory with text about pickup preference,
        # filter_ owner_id eq user_id, and limit 5; print model_dump_json().
        # Extraction is asynchronous: read again after the service cadence.
        raise NotImplementedError("Read session and long-term memory")


if __name__ == "__main__":
    main()
