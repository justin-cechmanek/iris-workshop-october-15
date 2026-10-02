"""Lab 1: embed policy Markdown locally and search it with RedisVL.

Run from the repository root: python exercises/lab_1/01_vector.py
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

    # TODO 2: Define a RedisVL HASH schema named INDEX with prefix PREFIX.
    # Include id TAG, title TEXT, body TEXT, and embedding VECTOR FLAT
    # FLOAT32, DIM 384, COSINE. Make a SearchIndex from that schema and
    # REDIS_URL. Call index.create() without dropping existing data, then
    # ping through index.client (RedisVL initializes it lazily).
    raise NotImplementedError("Create the RedisVL vector index")

    records = []
    policy_dir = Path(__file__).resolve().parents[2] / "data/policies"
    for path in sorted(policy_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # TODO 3: Split text at its first blank line. Use the heading as
        # title, the remaining paragraphs as body, and path.stem as id.
        # TODO 4: Embed body with vectorizer.embed(body, as_buffer=True).
        # Append a dict with id, title, body, and embedding to records.
        raise NotImplementedError(f"Embed {path}")

    # TODO 5: Use index.load(records, id_field="id") and print each key.
    # Then inspect the pickup vector with index.client.hstrlen(...).
    # Predict DIM * 4 bytes because each FLOAT32 value uses four bytes.

    question = "How long will my pickup order be held?"
    # TODO 6: Embed question with the same vectorizer. Build a VectorQuery
    # over embedding with title/body returned and num_results=2. Call
    # index.query(query); print each title, vector_distance, and body.
    raise NotImplementedError("Search the policies")


if __name__ == "__main__":
    main()
