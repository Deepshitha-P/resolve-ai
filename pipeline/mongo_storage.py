import os
from typing import List, Dict, Optional
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pipeline.logger import get_logger

logger = get_logger("MongoStorageEngine")

class MongoStorageEngine:
    """
    Connects to MongoDB Atlas for storing Aggregated Data (Snapshots and Clusters).
    Includes a capacity pre-flight check to warn if > 80% full.
    """
    def __init__(self):
        self.uri = os.environ.get("MONGO_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")
        self.db_name = "resolve_ai"
        self.client = None
        self.db = None
        self.is_connected = False
        
        self._connect()

    def _connect(self):
        if "<username>" in self.uri:
            logger.warning("[MONGO DB] MONGO_URI contains placeholder. Skipping MongoDB.")
            return

        try:
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.is_connected = True
            logger.info(f"[MONGO DB] Successfully connected to Atlas ({self.db_name})")
            self.check_capacity()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"[MONGO DB] Failed to connect to MongoDB Atlas (timeout). Error: {e}")
        except Exception as e:
            logger.warning(f"[MONGO DB] Unexpected error connecting to MongoDB Atlas: {e}")

    def check_capacity(self):
        if not self.is_connected:
            return
        try:
            stats = self.db.command("dbstats")
            # For Atlas Free Tier, hard limit is 512 MB
            data_size_mb = stats.get('dataSize', 0) / (1024 * 1024)
            limit_mb = 512.0
            percent_used = (data_size_mb / limit_mb) * 100
            
            if percent_used > 80.0:
                logger.warning(f"[MONGO DB WARNING] Storage capacity is at {percent_used:.1f}% ({data_size_mb:.1f} MB / {limit_mb} MB).")
            else:
                logger.info(f"[MONGO DB] Storage capacity looks good: {percent_used:.1f}% used.")
        except Exception as e:
            logger.warning(f"[MONGO DB] Could not check capacity: {e}")

    def save_snapshot(self, snapshot: Dict):
        if not self.is_connected:
            return
        try:
            coll = self.db["analytics_snapshots"]
            if "_id" not in snapshot:
                snapshot["_id"] = snapshot.get("document_id")
            coll.replace_one({"_id": snapshot["_id"]}, snapshot, upsert=True)
            logger.info(f"[MONGO DB] Saved snapshot {snapshot.get('document_id')}")
        except Exception as e:
            logger.warning(f"[MONGO DB] Failed to save snapshot: {e}")

    def save_clusters(self, clusters: List[Dict]):
        if not self.is_connected or not clusters:
            return
        try:
            coll = self.db["issue_clusters"]
            for c in clusters:
                if "_id" not in c:
                    c["_id"] = c.get("cluster_id")
                coll.replace_one({"_id": c["_id"]}, c, upsert=True)
            logger.info(f"[MONGO DB] Saved {len(clusters)} clusters to MongoDB.")
        except Exception as e:
            logger.warning(f"[MONGO DB] Failed to save clusters: {e}")
