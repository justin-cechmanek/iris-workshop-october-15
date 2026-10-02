"""Small offline checks for the completed workshop examples."""

import runpy
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from redisvl.index import SearchIndex


ROOT = Path(__file__).resolve().parents[1]


class CompletedExamplesTest(unittest.TestCase):
    def test_completed_files_import(self):
        for path in sorted((ROOT / "exercises").glob("lab_*/*_completed.py")):
            with self.subTest(path=path.name):
                runpy.run_path(str(path), run_name="workshop_check")

    def test_loader_writes_every_order(self):
        class FakeRedis:
            def __init__(self):
                self.records = {}

            def hset(self, key, mapping):
                self.records[key] = mapping

        load_file = runpy.run_path(
            str(ROOT / "exercises/lab_2/02_load_context_completed.py"),
            run_name="workshop_check",
        )["load_file"]
        fake = FakeRedis()
        count = load_file(fake, ROOT / "data/orders.jsonl", "workshop:order", "order_id")
        self.assertEqual(count, 3)
        self.assertEqual(fake.records["workshop:order:O1001"]["status"], "ready_for_pickup")

    def test_vector_schema_and_key(self):
        module = runpy.run_path(
            str(ROOT / "exercises/lab_1/01_vector_completed.py"),
            run_name="workshop_check",
        )
        index = SearchIndex.from_dict(module["SCHEMA"], redis_url="redis://localhost:6379")
        self.assertEqual(index.key("pickup"), "workshop:policy:minilm:pickup")
        self.assertEqual(index.schema.fields["embedding"].attrs.dims, 384)

    def test_langcache_miss_then_exact_hit(self):
        class FakeCache:
            answer = None

            def __init__(self, **_kwargs):
                pass

            def check(self, prompt, distance_threshold):
                if self.answer and prompt == "How long does the demo store hold my pickup order?":
                    return [{"response": self.answer}]
                if self.answer and prompt == "For how many days can I collect a pickup order?":
                    if distance_threshold >= 0.40:
                        return [{"response": self.answer}]
                return []

            def store(self, prompt, response):
                self.answer = response
                return "demo-entry"

        module = runpy.run_path(
            str(ROOT / "exercises/lab_3/03_langcache_completed.py"),
            run_name="workshop_check",
        )
        main = module["main"]
        main.__globals__["LangCacheSemanticCache"] = FakeCache
        credentials = {
            "LANGCACHE_URL": "https://example.invalid",
            "LANGCACHE_CACHE_ID": "demo",
            "LANGCACHE_API_KEY": "demo",
        }
        with patch.dict("os.environ", credentials), redirect_stdout(StringIO()) as output:
            main()
        self.assertIn("Stored entry: demo-entry", output.getvalue())
        self.assertIn("seven days", output.getvalue())
        self.assertIn("minimum similarity 0.98): MISS", output.getvalue())
        self.assertIn("minimum similarity 0.60): HIT", output.getvalue())


if __name__ == "__main__":
    unittest.main()
