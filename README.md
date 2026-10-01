# CVS onsite Redis Iris workshop

Four hands-on Python labs introduce Redis Search and Redis Iris through a fictional CVS retail scenario. Attendees write the data loading and service calls themselves. Results print in the terminal; there is no app server or frontend.

The [workshop slide deck](slides/cvs-redis-iris-workshop.pptx) walks through Cloud setup and the labs in order.
Its editable source is [`slides/build_deck.py`](slides/build_deck.py); run `python slides/build_deck.py` in the workshop virtual environment to rebuild it.

All sample policies, stores, orders, and users are fictional. Use no real customer, prescription, or health data.

## 150-minute plan

| Segment | Minutes | Checkpoint |
| --- | ---: | --- |
| Cloud account, database, Python setup | 20 | Redis `PING` returns `True` |
| Lab 1: Vector search | 30 | Pickup policy ranks near the top |
| Lab 2: Context Retriever | 45 | `get_order_by_id` returns `O1001` |
| Lab 3: LangCache | 20 | Exact prompt returns a cached entry |
| Lab 4: Agent Memory | 25 | Session event appears; search runs |
| Debrief | 10 | Explain when to use each service |

Instructors: complete the [preflight checklist](INSTRUCTOR.md) before the session, especially service access and attendee credentials. Account verification or provisioning can take longer than the schedule allows.

## Setup

1. [Create a Redis Cloud account](https://cloud.redis.io/) and sign in. In **New database**, choose **Try 30 MB for free**, then choose a region and create the database. Redis permits one free database per account. [Redis Cloud free database guide](https://redis.io/docs/latest/operate/rc/databases/create-database/create-free-database/)
2. Open the database's **Configuration** page. Copy the public endpoint (host and port). Under **Default user**, reveal the database password. The **Connect** wizard also shows Python connection examples. [Redis Cloud connection guide](https://redis.io/docs/latest/operate/rc/databases/connect/)
3. Use pyenv's selected Python to create a local virtual environment. Python 3.11 or later is required; this repository was checked with pyenv Python 3.12.2.

The `redis` entry in `requirements.txt` is the Python client, separate from the Redis Cloud server version. RedisVL uses that client underneath. The workshop accepts compatible redis-py 6.3+, 7, and 8 releases; its Redis calls were checked with redis-py 8.1.0 against Redis server 8.6.1.

```sh
pyenv exec python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Lab 1 runs a Hugging Face model locally. Download it once during setup, ideally before the onsite session; the first download needs access to `huggingface.co` and the model is cached afterward:

```sh
python - <<'PY'
from redisvl.utils.vectorize import HFTextVectorizer

vectorizer = HFTextVectorizer(model="sentence-transformers/all-MiniLM-L6-v2")
print(vectorizer.dims)
PY
```

Expect `384`. Fill `REDIS_URL` in `.env`. Use `redis://default:PASSWORD@HOST:PORT` for a non-TLS database or `rediss://` when TLS is enabled. URL-encode reserved characters in the password. Before lab 4, replace `WORKSHOP_USER_ID=change-me` with a unique non-sensitive ID. The `.env` file is ignored by Git; keep service keys there. No OpenAI key is needed for the workshop's Python scripts.

Check the database connection:

```sh
python - <<'PY'
import os
from dotenv import load_dotenv
from redisvl.redis.connection import RedisConnectionFactory

load_dotenv()
client = RedisConnectionFactory.get_redis_connection(
    redis_url=os.environ["REDIS_URL"]
)
print(client.ping())
PY
```

Expect `True`. Use a separate database per attendee if possible. Lab scripts write keys beginning `workshop:`.

## Labs

Work from the repository root, with `.venv` active, in this order:

| Lab | Guide | Main exercise |
| --- | --- | --- |
| 1. Vector search | [Lab 1 instructions](exercises/lab_1/README.md) | Parse, embed, index, and search policy documents |
| 2. Context Retriever | [Lab 2 instructions](exercises/lab_2/README.md) | Load orders and stores, model entities, call a generated tool |
| 3. LangCache | [Lab 3 instructions](exercises/lab_3/README.md) | Search, store, and compare policy answers |
| 4. Agent Memory | [Lab 4 instructions](exercises/lab_4/README.md) | Write a session event and search extracted memory |

Each starter has a commented `*_completed.py` answer beside it. Try the starter first, then compare. Lab 2 also has `models_completed.py`; create the surface with that model when trying the completed path.

RedisVL defines, loads, and queries the vector index in lab 1, supplies the Redis connection for lab 2's raw HASH writes, and wraps the managed LangCache service in lab 3. Context Retriever models those HASHes as a separate service; lab 4 uses the Agent Memory SDK.

For every lab, trace one piece of data through the system before opening the completed file:

| Lab | File you edit | Data to inspect after it runs |
| --- | --- | --- |
| 1 | `01_vector.py` | Policy HASH, vector byte length, and ranked text |
| 2 | `02_load_context.py`, `models.py`, `02_context.py` | Raw order HASH and generated tool result |
| 3 | `03_langcache.py` | Cache miss, stored public answer, and repeated search |
| 4 | `04_memory.py` | Health response, session event, and later extracted memory |

At the end of each lab, write down one prediction, what you observed, and why the result follows from the data or service configuration. The final debrief uses those notes.

Redis Cloud's current service guide offers [Agent Memory Quick create on a Free 30 MB database](https://redis.io/docs/latest/operate/iris/agent-memory/create-service/). Confirm service access in the workshop accounts before the session. The instructor should have a working service ready if an account cannot create one or provisioning takes too long.

## Debrief

Explain which component would answer each question: “What does the pickup policy say?”, “What is order O1001's status right now?”, “Have we answered this public question before?”, and “Which store does this fictional user prefer?” For each answer, identify what data was stored, who updates it, and whether the result can become stale.

## Workshop reference

This follows the [Retail Iris workshop](https://redis.io/iris-workshop/) and its [source repository](https://github.com/Redislabs-Solution-Architects/redis-iris-workshop) while leaving the core code for attendees to write. [Redis Iris overview](https://redis.io/docs/latest/develop/ai/context-engine/)
