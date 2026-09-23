# Strategy Retrieval Roadmap

The repository-owned corpus is the source of truth. Pinecone is a rebuildable
index used for embedding, metadata filtering, semantic retrieval, and reranking.

1. **Expand the initial corpus.** Add small, reviewable batches with generation,
   format, topic, and source metadata. Prefer original summaries over copied
   third-party prose. Status: in progress.
2. **Approve acquisition sources.** Decide which official material, community
   guides, and usage datasets may inform the corpus and how each is attributed.
3. **Broaden competitive coverage.** Add more generations, formats, doubles,
   team archetypes, and team-level strategy rather than only individual roles.
4. **Build query rewriting and retrieval-quality evals.** Turn conversational
   requests into focused retrieval text plus explicit generation, format, Pokemon,
   and topic filters. Compare rewritten queries with original prompts, measure
   whether expected passages appear, verify incompatible metadata is excluded,
   calibrate no-result thresholds, and test whether reranking improves the order.
5. **Complete tool and agent integration.** Keep Pinecone behind the model-facing
   `search_strategy` tool, execute that tool through the shared registry, connect
   it to the custom agent loop, and test that both agents receive the same schema
   and behavior.
6. **Finish configuration and deployment.** Document Pinecone environment keys,
   configure deployment secrets, and add an opt-in live smoke test.
7. **Synchronize index contents.** Make ingestion remove stale records as well as
   upserting current ones, and support safe dataset-version migrations.
8. **Measure before caching.** Record retrieval latency, read units, rerank units,
   and repeated queries; add caching only if those measurements justify it.
9. **Review and teaching walkthrough.** Walk through the corpus, validation,
   ingestion, embeddings, metadata filters, vector search, reranking, tool schema,
   agent call path, tests, evals, costs, and failure modes at a high level so the
   complete system can be understood and explained before further expansion.
