"""Completed lab 1: embed local policy text and search it with RedisVL.

Run from the repository root: python exercises/lab_1/01_vector_completed.py
The Hugging Face model downloads on first use; later runs use its local cache.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.utils.vectorize import HFTextVectorizer


MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DIM = 384
INDEX = "workshop:policies:minilm"
PREFIX = "workshop:policy:minilm"

# RedisVL turns this schema into FT.CREATE. The model-specific prefix keeps
# vectors from a different model out of this 384-dimensional index.
SCHEMA = {
    "index": {"name": INDEX, "prefix": PREFIX, "storage_type": "hash"},
    "fields": [
        {"name": "id", "type": "tag"},
        {"name": "title", "type": "text"},
        {"name": "body", "type": "text"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": DIM,
                "algorithm": "flat",
                "datatype": "float32",
                "distance_metric": "cosine",
            },
        },
    ],
}


def main():
    load_dotenv()
    vectorizer = HFTextVectorizer(model=MODEL)
    if vectorizer.dims != DIM:
        raise ValueError(f"Expected {DIM} model dimensions, got {vectorizer.dims}")

    index = SearchIndex.from_dict(SCHEMA, redis_url=os.environ["REDIS_URL"])
    # Existing indexes are kept. RedisVL does not delete indexed documents.
    index.create()
    print("Redis:", index.client.ping())
    print("Index ready:", INDEX)

    records = []
    policy_dir = Path(__file__).resolve().parents[2] / "data/policies"
    for path in sorted(policy_dir.glob("*.md")):
        heading, separator, body = path.read_text(encoding="utf-8").partition("\n\n")
        if not separator or not body.strip():
            raise ValueError(f"Expected a heading and body in {path}")
        title = heading.removeprefix("# ").strip()
        body = body.strip()

        # as_buffer=True packs the 384 FLOAT32 values for a Redis HASH.
        # Keep the source text beside the vector so a result is inspectable.
        embedding = vectorizer.embed(body, as_buffer=True)
        records.append({
            "id": path.stem,
            "title": title,
            "body": body,
            "embedding": embedding,
        })

    # The id field becomes the last part of each Redis key. Re-running
    # updates the same eight HASHes rather than creating duplicates.
    keys = index.load(records, id_field="id")
    for key in keys:
        print("Loaded:", key)

    pickup_key = index.key("pickup")
    vector_size = index.client.hstrlen(pickup_key, "embedding")
    print("Pickup embedding bytes:", vector_size)

    question = "How long will my pickup order be held?"
    question_vector = vectorizer.embed(question)
    query = VectorQuery(
        vector=question_vector,
        vector_field_name="embedding",
        return_fields=["title", "body"],
        num_results=2,
    )
    # RedisVL builds the KNN query and returns dictionaries. Smaller cosine
    # distance means a closer vector match; read the body before answering.
    results = index.query(query)
    print("Question:", question)
    for result in results:
        title = result["title"]
        body = result["body"]
        distance = result["vector_distance"]
        print(f"\n{title} (distance {distance})\n{body}")


if __name__ == "__main__":
    main()
