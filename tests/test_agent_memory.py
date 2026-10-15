"""Offline checks for the Agent Memory workshop flow."""

import runpy
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import httpx
from redis_agent_memory import AgentMemory, errors, models


LAB = Path(__file__).resolve().parents[1] / "exercises/lab_3_agent_memory/03_agent_memory_completed.py"


class AgentMemoryTest(unittest.TestCase):
    def setUp(self):
        self.main = runpy.run_path(str(LAB), run_name="workshop_check")["main"]
        self.memory = MagicMock(spec=AgentMemory)
        self.memory.__enter__.return_value = self.memory
        self.memory.search_long_term_memory.return_value = models.SearchLongTermMemoryResponseContent(items=[])
        self.memory.bulk_create_long_term_memories.return_value = (
            models.BulkCreateLongTermMemoriesResponseContent(created=["first", "second"])
        )

        def add_event(**kwargs):
            return models.AddSessionEventResponseContent(event=models.SessionEvent(
                **kwargs, event_id="demo-event", system_timestamp=datetime.now(timezone.utc),
            ))

        self.memory.add_session_event.side_effect = add_event
        self.enterContext(patch.dict(self.main.__globals__, {
            "AgentMemory": Mock(return_value=self.memory), "load_dotenv": Mock(),
        }))
        self.enterContext(patch.dict("os.environ", {
            "MEMORY_ENDPOINT": "https://example.invalid", "MEMORY_STORE_ID": "demo",
            "MEMORY_API_KEY": "demo", "WORKSHOP_USER_ID": "attendee-1",
        }))
        self.output = self.enterContext(redirect_stdout(StringIO()))
        self.enterContext(patch("sys.argv", [str(LAB)]))
        self.sleep = self.enterContext(patch("time.sleep"))

    def test_run_seeds_facts_then_adds_all_conversation_turns(self):
        self.main()
        payload = self.memory.bulk_create_long_term_memories.call_args.kwargs
        records = models.BulkCreateLongTermMemoriesRequestContent.model_validate(payload).memories
        self.assertEqual(len(records), 2)
        self.assertEqual({record.owner_id for record in records}, {"attendee-1"})
        self.assertEqual({record.memory_type for record in records}, {"semantic"})
        self.assertIn("S101", records[0].text)
        self.assertIn("email", records[1].text)
        ids = [record.id for record in records]
        self.assertEqual(len(set(ids)), 2)
        for memory_id in ids:
            self.assertRegex(memory_id, r"^[a-zA-Z0-9-]{1,64}$")

        events = [models.AddSessionEventRequestContent.model_validate(call.kwargs)
                  for call in self.memory.add_session_event.call_args_list]
        self.assertEqual([event.role for event in events], [
            models.MessageRole.USER, models.MessageRole.ASSISTANT,
        ] * 3)
        self.assertEqual([event.actor_id for event in events], [
            "attendee-1", "cvs-workshop-agent",
        ] * 3)
        self.assertEqual({event.session_id for event in events}, {"cvs-workshop-session-attendee-1"})
        self.assertEqual([event.content[0].text for event in events], [
            "I collect pickup orders after work.",
            "I'll remember that you collect orders after work.",
            "Weekday evenings are usually best for me.",
            "Noted, you prefer weekday-evening pickup.",
            "I also prefer reusable bags for my orders.",
            "I'll remember your reusable-bag preference.",
        ])
        self.assertTrue(all(event.created_at.utcoffset() == timedelta(0) for event in events))
        self.assertEqual([event.created_at for event in events], sorted(event.created_at for event in events))

        calls = [call[0] for call in self.memory.method_calls if "." not in call[0]]
        self.assertEqual(calls, [
            "delete_session_memory", "search_long_term_memory", "health",
            "bulk_create_long_term_memories", "add_session_event", "add_session_event",
            "add_session_event", "add_session_event", "add_session_event", "add_session_event",
            "get_session_memory",
            "search_long_term_memory", "search_long_term_memory",
        ])
        lines = [line for line in self.output.getvalue().splitlines() if line.startswith("Role:")]
        self.assertEqual(lines, [
            f"Role: {event.role}, Content: {event.content[0].text}" for event in events
        ])
        self.assertIn("Session:", self.output.getvalue())
        self.sleep.assert_called_once_with(60)

        self.main()
        self.assertEqual(self.memory.bulk_create_long_term_memories.call_args.kwargs, payload)
        with patch.dict("os.environ", {"WORKSHOP_USER_ID": "attendee-2"}):
            self.main()
        other = self.memory.bulk_create_long_term_memories.call_args.kwargs["memories"]
        self.assertTrue(set(ids).isdisjoint(record["id"] for record in other))

    def test_run_searches_only_this_user(self):
        self.main()
        self.assertEqual(self.memory.get_session_memory.call_count, 1)
        for call in self.memory.get_session_memory.call_args_list:
            self.assertEqual(call.kwargs, {"session_id": "cvs-workshop-session-attendee-1"})
        searches = self.memory.search_long_term_memory.call_args_list
        self.assertEqual(len(searches), 3)
        self.assertNotIn("text", searches[0].kwargs["request"])
        self.assertNotIn("limit", searches[0].kwargs["request"])
        self.assertNotEqual(searches[1].kwargs["request"]["text"], searches[2].kwargs["request"]["text"])
        for call in searches:
            self.assertEqual(call.kwargs["request"]["filter_"], {"owner_id": {"eq": "attendee-1"}})
        for call in searches[1:]:
            self.assertEqual(call.kwargs["request"]["limit"], 5)

    def test_partial_bulk_failure_stops_before_conversation_writes(self):
        self.memory.bulk_create_long_term_memories.return_value = (
            models.BulkCreateLongTermMemoriesResponseContent(
                created=["first"], errors=[models.BulkOperationError(id="second", error="demo failure")],
            )
        )
        with self.assertRaisesRegex(RuntimeError, "Background memory load failed"):
            self.main()
        self.assertIn("demo failure", self.output.getvalue())
        self.memory.add_session_event.assert_not_called()
        self.memory.get_session_memory.assert_not_called()
        self.memory.search_long_term_memory.assert_called_once()

    def test_run_preserves_service_errors(self):
        self.memory.get_session_memory.side_effect = RuntimeError("Service unavailable")
        with self.assertRaisesRegex(RuntimeError, "Service unavailable"):
            self.main()

    def test_search_output_shows_records_and_empty_heading(self):
        timestamp = datetime(2026, 10, 14, tzinfo=timezone.utc)
        empty = models.SearchLongTermMemoryResponseContent(items=[])
        record = models.MemoryRecord(
            id="background-1", text="The user prefers pickup at S101.",
            owner_id="attendee-1", created_at=timestamp, updated_at=timestamp,
        )
        self.memory.search_long_term_memory.side_effect = [
            empty, models.SearchLongTermMemoryResponseContent(items=[record]), empty,
        ]
        self.main()
        self.assertTrue(self.output.getvalue().endswith(
            "Background search:\n"
            f"Text: {record.text}, Updated At: {timestamp}, Created At: {timestamp}\n"
            "Conversation search:\n"
        ))

    def test_reset_deletes_one_page_in_one_call(self):
        for count in (1, 10):
            with self.subTest(count=count):
                self.memory.reset_mock()
                records = [SimpleNamespace(id=f"old-{number}", owner_id="attendee-1")
                           for number in range(count)]
                empty = models.SearchLongTermMemoryResponseContent(items=[])
                self.memory.search_long_term_memory.side_effect = [
                    SimpleNamespace(items=records), empty, empty,
                ]
                self.memory.bulk_delete_long_term_memories.return_value = (
                    models.BulkDeleteLongTermMemoriesResponseContent(deleted=[record.id for record in records])
                )
                self.main()
                self.memory.bulk_delete_long_term_memories.assert_called_once_with(
                    memory_ids=[record.id for record in records],
                )
                request = self.memory.search_long_term_memory.call_args_list[0].kwargs["request"]
                self.assertEqual(request, {"filter_": {"owner_id": {"eq": "attendee-1"}}})
                self.memory.bulk_create_long_term_memories.assert_called_once()

    def test_first_run_ignores_missing_session_and_skips_empty_delete(self):
        self.memory.delete_session_memory.side_effect = errors.NotFoundErrorResponseContent(
            data=errors.NotFoundErrorResponseContentData(
                title="Session Not Found", type="/errors/resource-not-found", status=404,
            ),
            raw_response=httpx.Response(404, text="Session Not Found"),
        )
        self.main()
        self.memory.bulk_delete_long_term_memories.assert_not_called()
        self.memory.bulk_create_long_term_memories.assert_called_once()

    def test_reset_failure_stops_before_new_writes(self):
        for failure in ("session", "search", "bulk-delete"):
            with self.subTest(failure=failure):
                self.memory.reset_mock(side_effect=True)
                if failure == "session":
                    self.memory.delete_session_memory.side_effect = RuntimeError("Reset unavailable")
                elif failure == "search":
                    self.memory.search_long_term_memory.side_effect = RuntimeError("Reset unavailable")
                else:
                    self.memory.search_long_term_memory.return_value = SimpleNamespace(
                        items=[SimpleNamespace(id="old-memory", owner_id="attendee-1")],
                    )
                    self.memory.bulk_delete_long_term_memories.return_value = (
                        models.BulkDeleteLongTermMemoriesResponseContent(
                            deleted=[], errors=[models.BulkOperationError(id="old-memory", error="Reset unavailable")],
                        )
                    )
                with self.assertRaisesRegex(RuntimeError, "Reset unavailable"):
                    self.main()
                self.memory.bulk_create_long_term_memories.assert_not_called()
                self.memory.add_session_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
