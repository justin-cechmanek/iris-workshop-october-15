"""Lab 1: embed policy Markdown locally and search it with RedisVL.

Run from the repository root: python exercises/lab_1_vector_search/01_vector.py
Fill the TODOs using this lab's README.md. Do not delete existing indexes.
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


def main():
    load_dotenv()

    # TODO 1: Build an HFTextVectorizer with MODEL. Check its dims against DIM.
    # The model runs locally after Hugging Face downloads it once.

    # see https://docs.redisvl.com/en/latest/api/vectorizer.html#:~:text=installed%20with%20pip.-,%23%20Basic%20usage,-vectorizer%20%3D%20HFTextVectorizer

    # TODO 2: Define a RedisVL HASH schema named INDEX with prefix PREFIX.
    # Include id TAG, title TEXT, body TEXT, and embedding VECTOR FLAT
    # FLOAT32, DIM 384, COSINE. Make a SearchIndex from that schema and
    # REDIS_URL. Call index.create() without dropping existing data, then
    # ping through index.client (RedisVL initializes it lazily).

    # see https://docs.redisvl.com/en/latest/api/schema.html#redisvl.schema.fields.FlatVectorField.type:~:text=dict%20is%20as%20simple%20as%3A-,from,-redisvl.schema%20import%20IndexSchema%0A%0Aschema
    # and https://docs.redisvl.com/en/latest/api/searchindex.html#redisvl.index.SearchIndex.create:~:text=%3DTrue)-,%23%20overwrite%20an%20index%20in%20Redis%3B%20drop%20associated%20data%20(clean%20slate),-index.create
    raise NotImplementedError("Create the RedisVL vector index")

     # Read policies, parse them, and create a list of dictionaries
    policy_dir = Path(__file__).resolve().parents[2] / "data/policies"
    records = []
    for path in sorted(policy_dir.glob("*.md")):
        heading, separator, body = path.read_text(encoding="utf-8").partition("\n\n")
        if not separator or not body.strip():
            raise ValueError(f"Expected a heading and body in {path}")
        title = heading.removeprefix("# ").strip()
        body = body.strip()
        records.append({
            "id": path.stem,
            "title": title,
            "body": body,
        })

    # TODO 3: Loop through records and embed body with vectorizer.embed(body, as_buffer=True).
    # Append this vector to the dict with id, title, body, inside records.
    raise NotImplementedError(f"Embed {path}")

    # TODO 4: Use index.load(records, id_field="id") and print each key.
    # Then inspect the pickup vector with index.client.hstrlen(...).
    # Predict DIM * 4 bytes because each FLOAT32 value uses four bytes.

    question = "How long will my pickup order be held?"
    # TODO 5: Embed question with the same vectorizer. Build a VectorQuery
    # over embedding with title/body returned and num_results=2. Call
    # index.query(query); print each title, vector_distance, and body.

    # see https://docs.redisvl.com/en/latest/api/query.html#:~:text=class-,VectorQuery,-(vector%2C

    raise NotImplementedError("Search the policies")

    results = index.query(query)
    print("Question:", question)
    for result in results:
        title = result["title"]
        body = result["body"]
        distance = result["vector_distance"]
        print(f"\n{title} (distance {distance})\n{body}")

if __name__ == "__main__":
    main()
