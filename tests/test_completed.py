"""Small offline checks for the completed workshop examples."""

import asyncio
import json
import os
import runpy
import unittest
from contextlib import chdir, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from context_surfaces import ContextSurfacesClient, UnifiedClient
from dotenv import dotenv_values, load_dotenv
from redisvl.index import SearchIndex


ROOT = Path(__file__).resolve().parents[1]


class CompletedExamplesTest(unittest.TestCase):
    def test_labs_load_root_dotenv_from_another_directory(self):
        class EnvLoaded(Exception):
            pass

        def load_env(*args, **kwargs):
            load_dotenv(*args, **kwargs)
            raise EnvLoaded

        with TemporaryDirectory() as directory:
            root = Path(directory) / "workshop"
            root.mkdir()
            (root / ".env").write_text("LANGCACHE_API_KEY=from-dotenv\n")
            for path in sorted((ROOT / "exercises").glob("lab_*/*.py")):
                with self.subTest(path=path):
                    main = runpy.run_path(str(path), run_name="workshop_check")["main"]
                    environment = {"LANGCACHE_API_KEY": "from-shell"}
                    with patch.dict(main.__globals__, {
                        "__file__": str(root / path.relative_to(ROOT)),
                        "load_dotenv": load_env,
                    }), patch.dict("os.environ", environment, clear=True), chdir(directory):
                        with self.assertRaises(EnvLoaded):
                            if asyncio.iscoroutinefunction(main):
                                asyncio.run(main())
                            else:
                                main()
                        self.assertEqual(os.environ.get("LANGCACHE_API_KEY"), "from-dotenv")

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
            str(ROOT / "exercises/lab_4_context_retriever/04_context_completed.py"),
            run_name="workshop_check",
        )["load_file"]
        fake = FakeRedis()
        count = load_file(fake, ROOT / "data/orders.jsonl", "workshop:order", "order_id")
        self.assertEqual(count, 3)
        self.assertEqual(fake.records["workshop:order:O1001"]["status"], "ready_for_pickup")

    def test_context_models_match_sample_records(self):
        for filename in ("04_context.py", "04_context_completed.py"):
            with self.subTest(filename=filename):
                module = runpy.run_path(
                    str(ROOT / "exercises/lab_4_context_retriever" / filename),
                    run_name="workshop_check",
                )
                models = [module["Store"], module["Order"]]
                self.assertEqual({model.__name__ for model in models}, {"Store", "Order"})
                if filename.endswith("_completed.py"):
                    for model in models:
                        data = ROOT / f"data/{model.__name__.lower()}s.jsonl"
                        for line in data.read_text().splitlines():
                            record = json.loads(line)
                            self.assertEqual(model(**record).model_dump(), record)

    def test_context_loads_before_querying_without_arguments(self):
        for filename in ("04_context.py", "04_context_completed.py"):
            with self.subTest(filename=filename):
                main = runpy.run_path(
                    str(ROOT / "exercises/lab_4_context_retriever" / filename),
                    run_name="workshop_check",
                )["main"]
                steps = []
                dotenv = Mock(side_effect=lambda path, **kwargs: steps.append("env"))
                loader = Mock(side_effect=lambda: steps.append("load"))
                configure = AsyncMock(
                    side_effect=lambda: steps.append("configure") or "test-agent-key"
                )
                query = AsyncMock(side_effect=lambda key: steps.append("query"))
                with patch.dict(main.__globals__, {
                    "load_dotenv": dotenv, "load_context": loader, "query_context": query,
                    "configure_context": configure,
                }), patch("sys.argv", [filename]), patch.dict("os.environ", {
                    "REDIS_URL": "redis://localhost:6379",
                    "CTX_ADMIN_KEY": "test-admin-key", "CTX_SURFACE_ID": "",
                }):
                    asyncio.run(main())
                self.assertEqual(steps, ["env", "load", "configure", "query"])
                dotenv.assert_called_once_with(ROOT / ".env", override=True)
                loader.assert_called_once_with()
                configure.assert_awaited_once_with()
                query.assert_awaited_once_with("test-agent-key")

    def test_context_updates_existing_surface_and_uses_generated_agent_key(self):
        module = runpy.run_path(
            str(ROOT / "exercises/lab_4_context_retriever/04_context_completed.py"),
            run_name="workshop_check",
        )
        tools = [{"name": "get_order_by_id", "inputSchema": {
            "type": "object", "properties": {"id": {"type": "string"}},
        }}]
        admin = MagicMock(spec=ContextSurfacesClient)
        admin.__aenter__.return_value = admin
        admin.create_agent_key.return_value = SimpleNamespace(key="generated-agent-key")
        agent = MagicMock(spec=UnifiedClient)
        agent.__aenter__.return_value = agent
        agent.list_tools.return_value = tools
        agent.query_tool.return_value = {
            "content": [{"text": json.dumps({
                "order_id": "O1001", "status": "ready_for_pickup",
            })}],
        }
        query = module["query_context"]
        with patch.dict(query.__globals__, {
            "ContextSurfacesClient": Mock(return_value=admin),
            "UnifiedClient": Mock(return_value=agent),
        }), patch.dict("os.environ", {
            "CTX_ADMIN_KEY": "test-admin-key", "CTX_SURFACE_ID": "existing-surface",
        }), redirect_stdout(StringIO()) as output:
            key = asyncio.run(module["configure_context"]())
            asyncio.run(query(key))

        args, kwargs = admin.update_context_surface.await_args
        self.assertEqual(args[0], "existing-surface")
        self.assertEqual(kwargs, {"admin_key": "test-admin-key"})
        request = args[1].model_dump(exclude_none=True)
        self.assertEqual(set(request), {"data_model"})
        self.assertEqual(request["data_model"], module["export_data_model"](
            title="CVS workshop", description="Synthetic retail orders",
            entities=[module["Store"], module["Order"]],
        ))
        args, kwargs = admin.create_agent_key.await_args
        self.assertEqual(args[0], "existing-surface")
        self.assertEqual(args[1].name, "cvs-workshop-agent")
        self.assertEqual(kwargs, {"admin_key": "test-admin-key"})
        agent.list_tools.assert_awaited_once_with("generated-agent-key")
        agent.query_tool.assert_awaited_once_with(
            agent_key="generated-agent-key", tool_name="get_order_by_id",
            arguments={"id": "O1001"},
        )
        self.assertIn('"inputSchema"', output.getvalue())
        self.assertIn("ready_for_pickup", output.getvalue())
        self.assertNotIn("generated-agent-key", output.getvalue())
        admin.create_context_surface.assert_not_awaited()

        admin.update_context_surface.side_effect = RuntimeError("Configuration failed")
        admin.create_agent_key.reset_mock()
        with patch.dict(query.__globals__, {
            "ContextSurfacesClient": Mock(return_value=admin),
        }), patch.dict("os.environ", {
            "CTX_ADMIN_KEY": "test-admin-key", "CTX_SURFACE_ID": "existing-surface",
        }):
            with self.assertRaisesRegex(RuntimeError, "Configuration failed"):
                asyncio.run(module["configure_context"]())
        admin.create_agent_key.assert_not_awaited()
        admin.create_context_surface.assert_not_awaited()

    def test_context_creates_saves_and_reuses_surface(self):
        urls = [
            ("rediss://demo%40user:p%40ss%3A%2520@redis.example:12345/2", {
                "addr": "redis.example:12345", "username": "demo@user",
                "password": "p@ss:%20", "db": 2, "tls_enabled": True,
            }),
            ("redis://redis.example", {
                "addr": "redis.example:6379", "username": "",
                "password": "", "db": 0, "tls_enabled": False,
            }),
            ("redis://:demo@redis.example:6380/1?db=3", {
                "addr": "redis.example:6380", "username": "",
                "password": "demo", "db": 3, "tls_enabled": False,
            }),
            ("redis://[::1]:6380/1", {
                "addr": "[::1]:6380", "username": "",
                "password": "", "db": 1, "tls_enabled": False,
            }),
        ]
        for redis_url, expected in urls:
            for initial_id in ("", "CTX_SURFACE_ID=\n"):
                with self.subTest(url=redis_url, initial_id=initial_id), TemporaryDirectory() as directory:
                    configure = runpy.run_path(
                        str(ROOT / "exercises/lab_4_context_retriever/04_context_completed.py"),
                        run_name="workshop_check",
                    )["configure_context"]
                    env_path = Path(directory) / ".env"
                    original = (f"# Keep workshop settings\nREDIS_URL={redis_url}\n"
                                "CTX_ADMIN_KEY=test-admin-key\nOTHER_SETTING='keep me'\n")
                    env_path.write_text(original + initial_id)
                    admin = MagicMock(spec=ContextSurfacesClient)
                    admin.__aenter__.return_value = admin
                    admin.create_context_surface.return_value = SimpleNamespace(id="created-surface")
                    admin.create_agent_key.return_value = SimpleNamespace(key="generated-agent-key")
                    with patch.dict(configure.__globals__, {
                        "__file__": str(Path(directory) / "exercises/lab4/example.py"),
                        "ContextSurfacesClient": Mock(return_value=admin),
                    }), patch.dict("os.environ", {
                        "REDIS_URL": redis_url, "CTX_ADMIN_KEY": "test-admin-key",
                        "CTX_SURFACE_ID": "",
                    }, clear=True), redirect_stdout(StringIO()) as output:
                        self.assertEqual(asyncio.run(configure()), "generated-agent-key")
                        self.assertEqual(os.environ["CTX_SURFACE_ID"], "created-surface")
                        self.assertTrue(env_path.read_text().startswith(original))
                        self.assertEqual(dotenv_values(env_path)["CTX_SURFACE_ID"], "created-surface")
                        admin.update_context_surface.assert_not_awaited()
                        request = admin.create_context_surface.await_args.args[0]
                        self.assertEqual(request.name, "cvs-workshop")
                        self.assertEqual(request.data_model, configure.__globals__["export_data_model"](
                            title="CVS workshop", description="Synthetic retail orders",
                            entities=[configure.__globals__["Store"], configure.__globals__["Order"]],
                        ))
                        self.assertEqual(admin.create_context_surface.await_args.kwargs,
                                         {"admin_key": "test-admin-key"})
                        connection = request.data_source.connection_config.model_dump()
                        self.assertEqual({name: connection[name] for name in expected}, expected)
                        self.assertEqual(admin.create_agent_key.await_args.args[0], "created-surface")
                        # Simulate a new process loading the saved ID.
                        del os.environ["CTX_SURFACE_ID"]
                        load_dotenv(env_path, override=True)
                        saved = env_path.read_text()
                        asyncio.run(configure())
                        admin.create_context_surface.assert_awaited_once()
                        admin.update_context_surface.assert_awaited_once()
                        self.assertEqual(admin.update_context_surface.await_args.args[0], "created-surface")
                        self.assertEqual(env_path.read_text(), saved)
                    self.assertIn("Created surface: created-surface", output.getvalue())
                    self.assertNotIn("generated-agent-key", output.getvalue())
                    self.assertNotIn("test-admin-key", output.getvalue())
                    if expected["password"]:
                        self.assertNotIn(expected["password"], output.getvalue())

    def test_context_creation_and_save_failures_stop_before_agent_key(self):
        for failure in ("create", "save_exception", "save_false"):
            with self.subTest(failure=failure):
                configure = runpy.run_path(
                    str(ROOT / "exercises/lab_4_context_retriever/04_context_completed.py"),
                    run_name="workshop_check",
                )["configure_context"]
                admin = MagicMock(spec=ContextSurfacesClient)
                admin.__aenter__.return_value = admin
                admin.create_context_surface.return_value = SimpleNamespace(id="recoverable-id")
                save = Mock(return_value=(False, "CTX_SURFACE_ID", "recoverable-id"))
                if failure == "create":
                    admin.create_context_surface.side_effect = RuntimeError("Creation failed")
                elif failure == "save_exception":
                    save.side_effect = PermissionError("Read-only .env")
                with patch.dict(configure.__globals__, {
                    "ContextSurfacesClient": Mock(return_value=admin), "set_key": save,
                }), patch.dict("os.environ", {
                    "REDIS_URL": "redis://localhost:6379", "CTX_ADMIN_KEY": "test-admin-key",
                    "CTX_SURFACE_ID": "",
                }), redirect_stdout(StringIO()) as output:
                    message = "Creation failed" if failure == "create" else "Set CTX_SURFACE_ID=recoverable-id"
                    with self.assertRaisesRegex(RuntimeError, message):
                        asyncio.run(configure())
                    self.assertEqual(os.environ["CTX_SURFACE_ID"], "")
                admin.create_agent_key.assert_not_awaited()
                admin.update_context_surface.assert_not_awaited()
                if failure == "create":
                    save.assert_not_called()
                else:
                    self.assertIn("Created surface: recoverable-id", output.getvalue())

    def test_context_rejects_unsupported_redis_addresses_before_creation(self):
        for redis_url in ("unix:///tmp/redis.sock", "redis://"):
            with self.subTest(redis_url=redis_url):
                configure = runpy.run_path(
                    str(ROOT / "exercises/lab_4_context_retriever/04_context_completed.py"),
                    run_name="workshop_check",
                )["configure_context"]
                admin = MagicMock(spec=ContextSurfacesClient)
                admin.__aenter__.return_value = admin
                with patch.dict(configure.__globals__, {
                    "ContextSurfacesClient": Mock(return_value=admin),
                }), patch.dict("os.environ", {
                    "REDIS_URL": redis_url, "CTX_ADMIN_KEY": "test-admin-key", "CTX_SURFACE_ID": "",
                }):
                    with self.assertRaisesRegex(ValueError, "REDIS_URL"):
                        asyncio.run(configure())
                admin.create_context_surface.assert_not_awaited()
                admin.create_agent_key.assert_not_awaited()

    def test_context_missing_credentials_stops_before_loading(self):
        for filename in ("04_context.py", "04_context_completed.py"):
            main = runpy.run_path(
                str(ROOT / "exercises/lab_4_context_retriever" / filename),
                run_name="workshop_check",
            )["main"]
            for name in ("REDIS_URL", "CTX_ADMIN_KEY"):
                with self.subTest(filename=filename, missing=name):
                    credentials = {"REDIS_URL": "redis://localhost:6379",
                                   "CTX_ADMIN_KEY": "test-admin-key",
                                   "CTX_SURFACE_ID": "existing-surface"}
                    credentials[name] = ""
                    loader = Mock()
                    with patch.dict(main.__globals__, {
                        "load_dotenv": Mock(), "load_context": loader,
                    }), patch.dict("os.environ", credentials):
                        with self.assertRaisesRegex(ValueError, name):
                            asyncio.run(main())
                    loader.assert_not_called()

    def test_vector_schema_and_key(self):
        class SchemaCaptured(Exception):
            pass

        main = runpy.run_path(
            str(ROOT / "exercises/lab_1_vector_search/01_vector_completed.py"),
            run_name="workshop_check",
        )["main"]
        factory = Mock()
        factory.from_dict.side_effect = SchemaCaptured
        with patch.dict(main.__globals__, {
            "SearchIndex": factory, "load_dotenv": Mock(),
        }), patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"}):
            with self.assertRaises(SchemaCaptured):
                main()
        index = SearchIndex.from_dict(
            *factory.from_dict.call_args.args, **factory.from_dict.call_args.kwargs
        )
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
            str(ROOT / "exercises/lab_2_langcache/02_langcache_completed.py"),
            run_name="workshop_check",
        )
        main = module["main"]
        main.__globals__["LangCacheSemanticCache"] = FakeCache
        credentials = {
            "LANGCACHE_URL": "https://example.invalid",
            "LANGCACHE_CACHE_ID": "demo",
            "LANGCACHE_API_KEY": "demo",
        }
        with patch.dict(main.__globals__, {"load_dotenv": Mock()}), patch.dict(
            "os.environ", credentials
        ), redirect_stdout(StringIO()) as output:
            main()
        self.assertIn("Stored entry: demo-entry", output.getvalue())
        self.assertIn("seven days", output.getvalue())
        self.assertIn("minimum similarity 0.98): MISS", output.getvalue())
        self.assertIn("minimum similarity 0.60): HIT", output.getvalue())


if __name__ == "__main__":
    unittest.main()
