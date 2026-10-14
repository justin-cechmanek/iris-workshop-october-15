# Lab 1: Local embeddings and vector search with RedisVL

**Goal:** create a RedisVL index that returns the policy closest in meaning to a question. Allow about 30 minutes. Skim the eight fictional Markdown files in [`data/policies/`](../../data/policies/) before coding.

**Pace:** 5 minutes to read and predict, 20 minutes to code and run, 5 minutes to explain the result. Have the Python packages and Hugging Face model downloaded before this timed lab.

## How it works
RedisVL's `SearchIndex` defines a Redis HASH index and loads the policy records.
RedisVL's [`HFTextVectorizer`](https://docs.redisvl.com/en/latest/user_guide/04_vectorizers.html#huggingface) runs `sentence-transformers/all-MiniLM-L6-v2` on your machine. It produces 384 numbers per text. The model downloads once from Hugging Face, then uses its local cache. No OpenAI key is needed for this lab.
`VectorQuery` searches for the closest vectors. Redis stores the original body beside each vector so you can inspect the evidence for a match.**Predict before coding:** Which policy should answer “How long will my pickup order be held?” How many bytes should a 384-dimensional `FLOAT32` vector occupy?

## Exercise

Edit [`01_vector.py`](01_vector.py). Complete the TODOs in order:

1. Build a schema dictionary with index name `workshop:policies:minilm`, prefix `workshop:policy:minilm`, and `storage_type="hash"`. Define `id` as a tag, `title` and `body` as text, and `embedding` as a vector with `dims=384`, `algorithm="flat"`, `datatype="float32"`, and `distance_metric="cosine"`. Use `SearchIndex.from_dict(schema, redis_url=os.environ["REDIS_URL"])`, then `index.create()`. Call `index.client.ping()` after `create()`; RedisVL initializes this client lazily.
2. Create an `HFTextVectorizer(model=MODEL)` and check that `vectorizer.dims == DIM`.
3. Compute `vectorizer.embed(body, as_buffer=True)` and add a record containing `id`, `title`, `body`, and `embedding` to a list. The buffer is the packed `FLOAT32` data a Redis HASH needs.
4. Call `index.load(records, id_field="id")` and print the returned keys. Inspect the pickup vector with `index.client.hstrlen(index.key("pickup"), "embedding")`.
5. Embed the question with the **same** vectorizer. Make `VectorQuery(vector=question_vector, vector_field_name="embedding", return_fields=["title", "body"], num_results=2)`. Call `index.query(query)` and print each result's `title`, `vector_distance`, and `body`.

## Run and inspect

```sh
python exercises/lab_1_vector_search/01_vector.py
```

## Troubleshooting
If the model download fails, check access to `huggingface.co` and the model preflight in the [setup guide](../../README.md#setup). If index creation or search fails, check Redis Search availability and the 384-dimensional schema. Compare with [`01_vector_completed.py`](01_vector_completed.py) after trying it yourself.

## Explain the result
- Try the questions, “When will a delivered order arrive?” and, “Can I add a coupon after checkout?”
- Why must the question and policies use the same embedding model?
- How does `1536` bytes confirm the declared vector format?
- Which stored field lets you verify that a close vector match supports an answer?
- What would you change if policies became long enough to contain several unrelated topics?
