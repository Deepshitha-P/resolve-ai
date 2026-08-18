# Initial Project Analysis: RootIQ UC18 RAG Pipeline

## Executive Summary

This report presents a thorough technical inspection of the existing **RootIQ UC18** codebase (`rootiq_rag`). The evaluation covers the raw dataset, end-to-end preprocessing and NLP workflows, conversation reconstruction algorithms, batching and checkpoint mechanisms, output schema traceability, and system memory characteristics.

Based on our empirical code inspection, while the prototype is cleanly structured with modular 17-stage orchestration and Parquet persistence, **it loads full stage datasets directly into Python RAM lists** and relies on **in-memory global dictionary traversal** for conversation threading and vector search. Consequently, executing the pipeline over the full **~2.81 million row dataset** in its current form will result in RAM exhaustion (Out-Of-Memory / OOM crashes) and severe CPU performance bottlenecks.

---

## 1. The Real TWCS Dataset

* **Primary Dataset File**: [twcs_cleaned.csv](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/data/raw/twcs_cleaned.csv)
* **File Size**: ~788.7 MB (788,701,297 bytes)
* **Total Row Count**: `2,811,774` records (as verified in [main.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/main.py#L216) and [pipeline_state.json](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/data/checkpoints/pipeline_state.json#L34)).
* **CSV Header Schema**: `tweet_id, author_id, inbound, created_at, text, response_tweet_id, in_response_to_tweet_id, clean_text`
* **Sample Dataset File**: [sample_1000.csv](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/data/sample_1000.csv) (248 KB, 1,000 records used for rapid testing).

---

## 2. Current End-to-End Preprocessing + NLP Flow

The pipeline consists of 17 sequential stages, split into a **Batch Knowledge Pipeline** (Stages 1–12) and a **Live Query Pipeline** (Stages 13–17):

```
RAW DATA (1) -> CLEAN (2) -> CONVERSATIONS (3) -> NLP (4) -> ANALYTICS (5)
-> TEMPORAL INTELLIGENCE (6) -> ISSUE CLUSTERS (7) -> ANALYTICS SNAPSHOTS (8)
-> KNOWLEDGE MEMORY (9) -> EMBEDDINGS (10) -> VECTOR DB (11) -> HYBRID RETRIEVAL (12)
-> QUERY ROUTER (13) -> RERANKER (14) -> EVIDENCE (15) -> CONFIDENCE (15)
-> INSIGHT MEMORY (16) -> LLM (17) -> GROUNDED BUSINESS INSIGHT
```

### Preprocessing & NLP Flow (Stages 1–4):

1. **Stage 1 (Raw Ingestion)**: [stage01_raw_data.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage01_raw_data.py) calls `CSVDatasetAdapter` in [adapters.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/adapters.py#L24) to parse CSV rows into `CaseRecord` schema objects and writes them to `data/parquet/raw_cases.parquet`.
2. **Stage 2 (Cleaning)**: [stage02_clean.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage02_clean.py) normalizes text using lowercasing, regex stripping of URLs (`http\S+`), mentions (`@\w+`), hashtags (`#\w+`), contraction expansions (`can't` -> `cannot`), and non-alphanumeric character removal.
3. **Stage 3 (Conversation Threading)**: [stage03_conversations.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage03_conversations.py) links customer tweets with brand replies by indexing `tweet_id` and `in_response_to_tweet_id`, producing multi-turn `Conversation` threads with response time and turn metrics, saved to `data/conversations/conversations.parquet`.
4. **Stage 4 (Local NLP Enrichment)**: [stage04_nlp.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage04_nlp.py) invokes `LocalNLPProvider` in [nlp_engine.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/nlp_engine.py#L68) to compute `intent`, `category` (across 15 taxonomy classes), `sentiment` (-1.0 to +1.0), `emotion`, `urgency`, `severity` (label, score 1-10, reasons), `escalation_signals`, and `temporal_signals`. Output is written to `data/nlp/nlp_results.parquet`.

---

## 3. How the 50K Run Was Executed

The 50,000-row run (Milestone B) was executed via:
```bash
python main.py --milestone B
```

### Execution Mechanics:
* [main.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/main.py#L56) invokes `run_batch_pipeline(sample_size=50000)`.
* `CSVDatasetAdapter.stream_data(chunk_size=50000, limit=50000)` streams 50K rows into memory.
* `dict_records.extend(...)` gathers all 50K dicts into a single Python list.
* The 50K records pass sequentially in-memory through Stages 1–4, DuckDB analytics (Stage 5), temporal intelligence (Stage 6), and clustering (Stage 7).
* In Stage 7 ([stage07_issue_clusters.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage07_issue_clusters.py#L17)), `max_sample_size` was capped at `10,000` conversations in [config.yaml](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/config/config.yaml#L44), allowing `MiniBatchKMeans` to complete quickly.

---

## 4. Stage Responsibilities and File Mapping

| Stage # | Stage Name | Responsible File | Input -> Output |
|---|---|---|---|
| **01** | Raw Ingestion | [stage01_raw_data.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage01_raw_data.py) | CSV -> `CaseRecord` dicts -> `raw_cases.parquet` |
| **02** | Cleaning | [stage02_clean.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage02_clean.py) | Raw text -> Normalized `clean_text` |
| **03** | Conversations | [stage03_conversations.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage03_conversations.py) | `CaseRecord` list -> `Conversation` threads -> `conversations.parquet` |
| **04** | Local NLP | [stage04_nlp.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage04_nlp.py), [nlp_engine.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/nlp_engine.py) | `Conversation` list -> `NLPResult` enriched -> `nlp_results.parquet` |
| **05** | Analytics | [stage05_analytics.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage05_analytics.py) | `conversations.parquet` -> DuckDB aggregate metrics -> `analytics_summary.parquet` |
| **06** | Temporal Intel | [stage06_temporal_intelligence.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage06_temporal_intelligence.py) | Conversations -> Daily group Z-scores & volume spike signals |
| **07** | Issue Clusters | [stage07_issue_clusters.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage07_issue_clusters.py) | Sampled conversations -> `TfidfVectorizer` + `MiniBatchKMeans` + Pain Score |
| **08** | Analytics Snapshots | [stage08_analytics_snapshots.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage08_analytics_snapshots.py) | Analytics + Temporal + Clusters -> `AnalyticsSnapshot` docs |
| **09** | Knowledge Memory | [stage09_knowledge_memory.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage09_knowledge_memory.py) | Snapshots + Runbooks + Conversations + Clusters -> `knowledge_documents.parquet` |
| **10** | Embeddings | [stage10_embeddings.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage10_embeddings.py) | Knowledge texts -> `TfidfVectorizer` (max 2000 features) sparse matrix |
| **11** | Vector DB | [stage11_vector_db.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage11_vector_db.py) | Vectors + Docs -> In-memory Cosine Similarity index |
| **12** | Hybrid Retrieval | [stage12_hybrid_retrieval.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage12_hybrid_retrieval.py) | Query + Docs -> BM25 + TF-IDF Vector score fusion (`alpha=0.5`) |
| **13** | Query Router | [stage13_query_router.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage13_query_router.py) | Query -> Intent classification -> Corpus filtering |
| **14** | Reranker | [stage14_reranker.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage14_reranker.py) | Retrieval candidates -> Source-trust priority score multiplier |
| **15** | Evidence & Confidence | [stage15_evidence_confidence.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage15_evidence_confidence.py) | Top candidates -> Cited evidence chain + 0–99% confidence score |
| **16** | Insight Memory | [stage16_insight_memory.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage16_insight_memory.py) | Generated insight -> JSON persistence in `outputs/insight_memory.json` |
| **17** | LLM Grounded Insight | [stage17_llm_grounded_insight.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage17_llm_grounded_insight.py) | Prompt + Evidence -> 5-part grounded synthesis (template / Claude API) |
| **Storage & Schemas** | Foundation | [storage.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/storage.py), [schemas.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/schemas.py), [config_loader.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/config_loader.py) | Pydantic data contracts, PyArrow Parquet read/write, CheckpointManager |

---

## 5. In-Memory Data Loading Assessment

> **Does the current pipeline load data entirely into memory?**
> **YES.**

### Empirical Evidence:

1. **Stage 1 Ingestion**: In [stage01_raw_data.py:36-37](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage01_raw_data.py#L36-L37):
   ```python
   for chunk in adapter.stream_data(chunk_size=chunk_size, limit=limit):
       dict_records.extend([c.model_dump() for c in chunk])
   ```
   Even though `stream_data` reads chunks, `dict_records.extend()` collects **every single record into a single in-memory Python list**.
2. **Stage 3 Conversations**: In [stage03_conversations.py:27-39](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage03_conversations.py#L27-L39):
   `tweet_map` and `parent_map` dictionaries are instantiated in memory to hold every raw record simultaneously for parent-child pointer lookups.
3. **Stage 4 NLP**: [stage04_nlp.py:31](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage04_nlp.py#L31) iterates over the entire `conversations` list in RAM and returns an all-in-memory enriched list.
4. **Stage 9 Knowledge Memory**: In [stage09_knowledge_memory.py:101-127](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage09_knowledge_memory.py#L101-L127), every single conversation thread is converted into a distinct `KnowledgeDocument` object held in RAM.
5. **Stage 10 & 11 RAG Indexing**: `TfidfVectorizer.fit_transform` and `VectorDB` store all document text strings and sparse matrices entirely in memory.

---

## 6. Conversation Reconstruction & Global Dataset Access

> **Does conversation reconstruction require global access to the dataset?**
> **YES (under the current threading model).**

### Rationale:
* In `twcs_cleaned.csv`, tweets are ordered chronologically by arrival, **not grouped by conversation or thread**.
* A brand reply (e.g. `tweet_id: 105`) may reply to a customer tweet (`in_response_to_tweet_id: 12`) that appeared thousands of rows earlier or days prior.
* `build_conversations()` in [stage03_conversations.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage03_conversations.py#L27-L40) populates `parent_map[in_response_to_tweet_id]`.
* If data is chunked arbitrarily (e.g. 50,000 rows per chunk) and processed in isolation without global parent-child lookups or a global disk/database index, **replies whose parents reside in a different chunk will fail to thread**, resulting in broken, truncated conversations.

---

## 7. Existing Batching & Checkpoint Mechanisms

* **Checkpoint System**: Managed by `CheckpointManager` in [storage.py:14-47](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/storage.py#L14-L47). State is persisted to `data/checkpoints/pipeline_state.json`. It tracks completed stages and skips rerun if marked `COMPLETED`.
* **Storage Layer**: Uses PyArrow (`pyarrow.parquet`) for snappy-compressed Parquet files and DuckDB in-memory SQL execution over Parquet files.
* **Sampling Guardrail**: Stage 7 ([stage07_issue_clusters.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/stage07_issue_clusters.py#L17)) caps clustering input to `max_sample_size: 10000` via [config.yaml](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/config/config.yaml#L44).
* **Deficiency**: There is **no stage-to-stage disk streaming pipeline**. Intermediate outputs are written to Parquet at the end of each stage, but the next stage immediately reads the entire Parquet back into RAM as a monolithic list.

---

## 8. Existing Output Format & Traceability Fields

* **Primary Storage Schemas** (defined in [schemas.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/pipeline/schemas.py)):
  - `CaseRecord`: `case_id`, `conversation_id`, `customer_id`, `channel`, `area`, `timestamp`, `raw_text`, `clean_text`, `inbound`, `response_tweet_id`, `in_response_to_tweet_id`, `source_type`.
  - `Conversation`: `conversation_id`, `customer_id`, `turns` (`turn_id`, `role`, `author_id`, `text`, `raw`, `timestamp`, `in_response_to_tweet_id`), `customer_turn_count`, `company_turn_count`, `start_time`, `end_time`, `first_response_time`, `conversation_duration`, `repeat_contact_signals`, `has_company_response`, `nlp`.
  - `NLPResult`: `intent`, `category`, `sentiment`, `sentiment_label`, `emotion`, `urgency`, `severity` (`label`, `score`, `reasons`), `escalation_signals`, `temporal_signals`, `confidence`, `label_source`, `model_version`.
* **Row-Level Export Verification**: [run_pipeline_test.py](file:///c:/Users/prem/Downloads/rootiq_rag/rootiq_rag/run_pipeline_test.py#L67-L150) maps conversation-level NLP results back to individual source rows, exporting `data/processed/sample_1000_processed.csv` with 21 explicit columns preserving 100% row-level traceability to original `tweet_id`s.

---

## 9. Bottlenecks & Failure Points Scaling from 50K to ~2.8M Rows

If the current pipeline is executed directly against the full ~2.81 million row dataset (`twcs_cleaned.csv`), the following failure modes will occur:

1. **RAM Exhaustion / OOM Crash (Critical Risk)**:
   - Holding 2.81M `CaseRecord` dicts in RAM requires ~4–6 GB.
   - Building `tweet_map` and `parent_map` across 2.81M records requires ~6–10 GB.
   - Stage 9 (`build_knowledge_memory`) will generate ~1.5M - 2.0M `KnowledgeDocument` records, taking ~12–16 GB.
   - Total memory demand will exceed **25–35 GB RAM**, causing severe OS swap thrashing or a `MemoryError` crash on standard developer hardware.
2. **Conversation Threading Algorithmic Bottleneck**:
   - `build_conversations()` performs pure Python dictionary lookups and recursive list building across 2.81M elements. In Python, this single-threaded loop will take tens of minutes and stall the execution.
3. **NLP Processing Latency**:
   - Running pure Python regex and string matching across ~1.5M conversation threads sequentially in a single thread will take ~30–50 minutes.
4. **TF-IDF Embedding & Vector DB Memory Explosion**:
   - `TfidfVectorizer.fit_transform()` over 1.5M+ documents will generate an immense sparse matrix.
   - `VectorDB.search()` computes linear NumPy cosine similarity (`cosine_similarity(query_vector, self.vectors)`) across 1.5M rows for every query in RAM without vector indexing (HNSW / FAISS / DuckDB VSS).
5. **No Chunked Pipeline Execution**:
   - The code lacks batch iteration between Parquet files on disk, preventing out-of-core processing.

---

## Verdict

`SCALABILITY ISSUES FOUND`
