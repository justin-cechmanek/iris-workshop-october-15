"""Offline regression check for the HASH-backed workshop model."""

import runpy
import unittest
from pathlib import Path

from context_surfaces import CreateContextSurfaceRequest, UpdateContextSurfaceRequest


class ContextModelTest(unittest.TestCase):
    def test_create_and_update_requests_declare_hash_entities(self):
        for filename in ("04_context.py", "04_context_completed.py"):
            with self.subTest(filename=filename):
                module = runpy.run_path(str(Path(__file__).resolve().parents[1] / filename))
                data_model = module["export_data_model"](
                    title="CVS workshop",
                    description="Synthetic retail orders",
                    entities=[module["Store"], module["Order"]],
                )
                requests = (
                    CreateContextSurfaceRequest(name="cvs-workshop", data_model=data_model),
                    UpdateContextSurfaceRequest(data_model=data_model),
                )
                for request in requests:
                    entities = request.model_dump(mode="json")["data_model"]["entities"]
                    self.assertEqual({entity["name"] for entity in entities}, {"Store", "Order"})
                    for entity in entities:
                        self.assertEqual(entity["document_type"], "hash")
                        self.assertTrue(entity["redis_key_template"].startswith("workshop:"))


if __name__ == "__main__":
    unittest.main()
