import os
from typing import Dict, List, Optional
from pipeline.adapters import CSVDatasetAdapter, SyntheticDatasetAdapter
from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.schemas import CaseRecord
from pipeline.storage import StorageEngine

logger = get_logger("Stage01_RawData")


def load_and_ingest_raw_data(
    config: Optional[Dict] = None,
    limit: Optional[int] = None,
    use_synthetic: bool = False,
    offset: int = 0
) -> List[Dict]:
    cfg = config or load_config()
    dataset_cfg = cfg.get("dataset", {})
    raw_path = dataset_cfg.get("raw_csv_path", "data/raw/twcs_cleaned.csv")
    source_type = dataset_cfg.get("source_type", "twcs_case")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_csv_path = os.path.join(base_dir, raw_path) if not os.path.isabs(raw_path) else raw_path

    if use_synthetic or not os.path.exists(abs_csv_path):
        logger.info("Using SyntheticDatasetAdapter for ingestion...")
        adapter = SyntheticDatasetAdapter(source_type="synthetic_case")
    else:
        logger.info(f"Using CSVDatasetAdapter to ingest {abs_csv_path}...")
        adapter = CSVDatasetAdapter(file_path=abs_csv_path, source_type=source_type)

    storage = StorageEngine(cfg)
    chunk_size = cfg.get("storage", {}).get("chunk_size", 50000)

    # 1. MongoDB Atlas ingestion REMOVED (Step 3: Repartition Storage)
    # MongoDB is now exclusively reserved for Analytics Snapshots and Issue Clusters
    # Raw data is persisted purely in Parquet chunks to save space.

    total_count = 0
    records_to_return = []

    def _chunk_generator():
        nonlocal total_count
        for chunk in adapter.stream_data(chunk_size=chunk_size, limit=limit, offset=offset):
            dumped = [c.model_dump() for c in chunk]
            total_count += len(dumped)
            # 2. Append directly to Parquet stream (MongoDB write removed)
            
            # Accumulate for return only if limit is specified and manageable (<= 300000)
            if limit is not None and limit <= 300000:
                records_to_return.extend(dumped)
            yield dumped

    storage.write_parquet_chunks(_chunk_generator(), "raw_cases.parquet", subfolder="parquet")
    storage.checkpoint_mgr.save_checkpoint("stage01_raw_data", {"count": total_count})

    logger.info(f"[STAGE 1 RAW DATA] Explicitly opened {abs_csv_path} and read {total_count:,} raw rows.")
    if total_count <= 300000:
        return storage.read_parquet("raw_cases.parquet", subfolder="parquet")
    return records_to_return




# Backward compatibility wrapper
def generate_raw_complaints(n: int = 60) -> List[Dict]:
    dict_records = load_and_ingest_raw_data(limit=n, use_synthetic=False)
    legacy_rows = []
    for r in dict_records:
        legacy_rows.append({
            "complaint_id": r["case_id"],
            "customer_id": r["customer_id"],
            "channel": r["channel"],
            "area": r.get("area") or "Global",
            "raw_text": r["raw_text"],
            "timestamp": r["timestamp"],
            "company_reply": None,
            "inbound": r["inbound"],
            "response_tweet_id": r.get("response_tweet_id"),
            "in_response_to_tweet_id": r.get("in_response_to_tweet_id"),
            "source_type": r["source_type"],
        })
    return legacy_rows


if __name__ == "__main__":
    data = generate_raw_complaints(50)
    print(f"Ingested {len(data)} rows successfully.")
