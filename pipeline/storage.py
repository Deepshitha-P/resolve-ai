from datetime import datetime, timezone
import json
import os
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Any, Dict, List, Optional
from pipeline.config_loader import load_config
from pipeline.logger import get_logger

logger = get_logger("StorageEngine")


class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, "pipeline_state.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint state: {e}")
        return {}

    def save_checkpoint(self, stage_name: str, metadata: Dict[str, Any]):
        self.state[stage_name] = {
            "status": "COMPLETED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)
        logger.info(f"Saved checkpoint for stage '{stage_name}'")

    def is_completed(self, stage_name: str) -> bool:
        return self.state.get(stage_name, {}).get("status") == "COMPLETED"

    def clear(self):
        self.state = {}
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)


class StorageEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.storage_cfg = self.config.get("storage", {})
        self.base_dir = self.storage_cfg.get("base_dir", "data")
        
        for k in ["raw_dir", "parquet_dir", "conversations_dir", "nlp_dir", "analytics_dir", "knowledge_dir", "checkpoints_dir"]:
            dir_path = self.storage_cfg.get(k, os.path.join(self.base_dir, k.replace("_dir", "")))
            os.makedirs(dir_path, exist_ok=True)
            
        self.con = duckdb.connect(database=":memory:")
        self.checkpoint_mgr = CheckpointManager(self.storage_cfg.get("checkpoints_dir", "data/checkpoints"))

    def get_parquet_path(self, filename: str, subfolder: str = "parquet") -> str:
        target_dir = os.path.join(self.base_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, filename)

    def write_parquet(self, records: List[Dict[str, Any]], filename: str, subfolder: str = "parquet"):
        if not records:
            logger.warning(f"No records to write for {filename}")
            return None
        
        file_path = self.get_parquet_path(filename, subfolder)
        table = pa.Table.from_pylist(records)
        pq.write_table(table, file_path, compression="snappy")
        logger.info(f"Wrote {len(records):,} records to Parquet: {file_path}")
        return file_path

    def write_parquet_chunks(self, chunk_generator, filename: str, subfolder: str = "parquet", schema: Optional[pa.Schema] = None) -> str:
        file_path = self.get_parquet_path(filename, subfolder)
        writer = None
        first_schema = schema
        total_records = 0

        try:
            for chunk in chunk_generator:
                if not chunk:
                    continue
                if isinstance(chunk, list):
                    # Pyarrow cannot write empty-dict struct fields.
                    # Replace {} with {"_": ""} for any dict-valued field.
                    def _san(rec):
                        return {
                            k: ({"_": ""} if isinstance(v, dict) and not v else v)
                            for k, v in rec.items()
                        } if isinstance(rec, dict) else rec
                    chunk = [_san(r) for r in chunk]
                    table = pa.Table.from_pylist(chunk, schema=first_schema)
                elif isinstance(chunk, pa.Table):
                    table = chunk
                else:
                    continue
                
                if writer is None:
                    first_schema = table.schema
                    writer = pq.ParquetWriter(file_path, first_schema, compression="snappy")
                elif first_schema is not None and table.schema != first_schema:
                    try:
                        table = table.cast(first_schema)
                    except Exception:
                        pass
                
                writer.write_table(table)
                total_records += len(table)
            
            if writer:
                writer.close()
                logger.info(f"Streamed {total_records:,} records to Parquet: {file_path}")
            else:
                logger.warning(f"No records written to streaming Parquet: {file_path}")
        except Exception as e:
            if writer:
                writer.close()
            logger.error(f"Error in write_parquet_chunks for {file_path}: {e}")
            raise e


        return file_path

    def read_parquet(self, filename: str, subfolder: str = "parquet") -> List[Dict[str, Any]]:
        file_path = os.path.join(self.base_dir, subfolder, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Parquet file not found: {file_path}")
            return []
        
        table = pq.read_table(file_path)
        return table.to_pylist()

    def read_parquet_batches(self, filename: str, subfolder: str = "parquet", batch_size: int = 50000):
        file_path = os.path.join(self.base_dir, subfolder, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Parquet file not found: {file_path}")
            return
        
        pf = pq.ParquetFile(file_path)
        for batch in pf.iter_batches(batch_size=batch_size):
            yield batch.to_pylist()

    def query_parquet_duckdb(self, parquet_rel_path: str, sql_query: str) -> List[Dict[str, Any]]:
        file_path = os.path.join(self.base_dir, parquet_rel_path)
        if not os.path.exists(file_path):
            logger.warning(f"Parquet file not found for DuckDB query: {file_path}")
            return []
        
        file_path_fwd = file_path.replace('\\', '/')
        formatted_query = sql_query.replace("{parquet_file}", f"'{file_path_fwd}'")
        try:
            rel = self.con.sql(formatted_query)
            if rel is None or not hasattr(rel, "arrow"):
                return []
            arrow_table = rel.arrow().read_all()
            return arrow_table.to_pylist()
        except Exception as e:
            logger.error(f"DuckDB query error on {file_path}: {e}")
            return []

